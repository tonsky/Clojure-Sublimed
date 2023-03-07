(ns clojure-sublimed.socket-repl
  (:require
    [clojure.string :as str]
    [clojure-sublimed.core :as core])
  (:import
    [java.io Reader StringReader]
    [java.lang.reflect Field]
    [clojure.lang Compiler Compiler$CompilerException LineNumberingPushbackReader LispReader LispReader$ReaderException RT]))

(defonce ^:dynamic *out-fn*
  prn)

(defonce ^:dynamic *context*
  nil)

(defonce *evals
  (atom {}))

(defn stop! []
  (throw (ex-info "Stop" {::stop true})))

(defn read-command [in]
  (let [[form s] (read+string {:eof ::eof, :read-cond :allow} in)]
    (when (= ::eof form)
      (stop!))
    
    ; (vswap! *context* assoc :form s)
    
    (when-not (map? form)
      (throw (Exception. (str "Unexpected form: " (pr-str form)))))
    
    form))

(defn report-throwable [^Throwable t]
  (let [root  ^Throwable (core/root-cause t)
        {:clojure.error/keys [source line column]} (ex-data root)
        cause ^Throwable (or (some-> root .getCause) root)
        data  (ex-data cause)
        class (.getSimpleName (class cause))
        msg   (.getMessage cause)
        val   (cond-> (str class ": " msg)
                data
                (str " " (core/bounded-pr-str data)))
        trace (core/trace-str root {:location? false})]
    (*out-fn*
      (merge
        {:tag    :ex
         :val    val
         :trace  trace
         :source source
         :line   line
         :column column}
        @*context*))))

(defn reader ^LineNumberingPushbackReader [code line column]
  (let [reader (LineNumberingPushbackReader. (StringReader. code))]
    (when line
      (.setLineNumber reader (int line)))
    (when column
      (when-some [field (.getDeclaredField LineNumberingPushbackReader "_columnNumber")]
        (doto ^Field field
          (.setAccessible true)
          (.set reader (int column)))))
    reader))

(defn consume-ws [^LineNumberingPushbackReader reader]
  (loop [ch (.read reader)]
    (if (or (Character/isWhitespace ch) (= (int \,) ch))
      (recur (.read reader))
      (when-not (neg? ch)
        (.unread reader ch)))))
  
(defn eval-code [form]
  (let [{:keys [id code ns line column file]} form
        start  (System/nanoTime)
        name   (or (some-> file (str/split #"[/\\]") last) "NO_SOURCE_FILE")
        ns     (or ns 'user)
        ns-obj (or
                 (find-ns ns)
                 (do
                   (require ns)
                   (find-ns ns)))
        ;; "Adapted from clojure.lang.Compiler/load
        ;; Does not bind *uncheked-math*, *warn-on-reflection* and *data-readers*"
        eof    (Object.)
        opts   {:eof       eof
                :read-cond :allow}
        reader (reader code line column)
        _      (consume-ws reader)
        _      (push-thread-bindings
                 {Compiler/LOADER         (RT/makeClassLoader)
                  #'*file*                file
                  #'*source-path*         name
                  Compiler/METHOD         nil
                  Compiler/LOCAL_ENV      nil
                  Compiler/LOOP_LOCALS    nil
                  Compiler/NEXT_LOCAL_NUM 0
                  #'*read-eval*           true
                  #'*ns*                  ns-obj
                  Compiler/LINE_BEFORE    (.getLineNumber reader)
                  Compiler/COLUMN_BEFORE  (.getColumnNumber reader)
                  Compiler/LINE_AFTER     (.getLineNumber reader)
                  Compiler/COLUMN_AFTER   (.getColumnNumber reader)})
        ret    (try
                 (loop [ret nil]
                   (let [obj (read opts reader)]
                     (if (identical? obj eof)
                       ret
                       (do
                         (consume-ws reader)
                         (.set Compiler/LINE_AFTER (.getLineNumber reader))
                         (.set Compiler/COLUMN_AFTER (.getColumnNumber reader))
                         (let [ret (Compiler/eval obj false)]
                           (.set Compiler/LINE_BEFORE (.getLineNumber reader))
                           (.set Compiler/COLUMN_BEFORE (.getColumnNumber reader))
                           (recur ret))))))
                 (catch LispReader$ReaderException e
                   (throw (Compiler$CompilerException.
                            file
                            (.-line e)
                            (.-column e)
                            nil
                            Compiler$CompilerException/PHASE_READ
                            (.getCause e))))
                 (catch Throwable e
                   (if (instance? Compiler$CompilerException e)
                     (throw e)
                     (throw (Compiler$CompilerException.
                              file
                              (.deref Compiler/LINE_BEFORE)
                              (.deref Compiler/COLUMN_BEFORE)
                              nil
                              Compiler$CompilerException/PHASE_EXECUTION
                              e))))
                 (finally
                   (pop-thread-bindings)))
        time (-> (System/nanoTime)
               (- start)
               (quot 1000000))]
    (*out-fn*
      {:tag  :ret
       :id   id
       :val  (core/bounded-pr-str ret)
       :time time})))

(defn fork-eval [{:keys [id forms]}]
  (let [f (future
            (try
              (core/track-vars
                (doseq [form forms]
                  (vswap! *context* assoc :id (:id form))
                  (eval-code form)))
              (catch Throwable t
                (try
                  (report-throwable t)
                  (catch Throwable t
                    :ignore))))
            (swap! *evals dissoc id)
            (vswap! *context* assoc :id id)
            (*out-fn*
              (merge @*context* {:tag :done})))]
    (swap! *evals assoc id f)))
 
(defn interrupt [{:keys [id]}]
  (when-some [f (@*evals id)]
    (future-cancel f)))

(def safe-meta?
  #{:ns :name :doc :file :arglists :forms :macro :special-form :protocol :line :column :added :deprecated :resource})

(defn lookup-symbol [form]
  (let [{:keys [id op symbol ns] :or {ns 'user}} form
        ns     (clojure.core/symbol ns)
        symbol (clojure.core/symbol symbol)
        meta   (if (special-symbol? symbol)
                 (assoc ((requiring-resolve 'clojure.repl/special-doc) symbol)
                   :ns           'clojure.core
                   :file         "clojure/core.clj"
                   :special-form true)
                 (meta (ns-resolve ns symbol)))]
    (*out-fn*
      (if meta
        (let [meta' (reduce-kv
                      (fn [m k v]
                        (if (safe-meta? k)
                          (assoc m (name k) (str v)) ; stringify to match nREPL
                          m))
                      nil
                      meta)]
          {:tag :lookup
           :id  id
           :val meta'})
        {:tag :ex
         :id  id
         :val (str "Symbol '" symbol " not found in ns '" ns)}))))

(defn out-fn [out]
  (let [lock (Object.)]
    #(locking lock
       (binding [*out* out]
         (prn %)))))

(defn repl []
  (binding [*out-fn* (out-fn *out*)
            *out*    (.getRawRoot #'*out*)
            *err*    (.getRawRoot #'*err*)
            core/*changed-vars (atom {})]
    (*out-fn* {:tag :started})
    (loop []
      (when
        (binding [*context* (volatile! {})]
          (try
            (let [form (read-command *in*)]
              (core/set-changed-vars!)
              (when-some [id (:id form)]
                (vswap! *context* assoc :id id))
              (case (:op form)
                :close     (stop!)
                :eval      (fork-eval form)
                :interrupt (interrupt form)
                :lookup    (lookup-symbol form)
                (throw (Exception. (str "Unknown op: " (:op form)))))
              true)
            (catch Throwable t
              (when-not (-> t ex-data ::stop)
                (report-throwable t)
                true))))
        (recur)))
    (doseq [[id f] @*evals]
      (future-cancel f))))
