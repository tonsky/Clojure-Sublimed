(ns clojure-sublimed.socket-repl
  (:require
    [clojure.string :as str]
    [clojure.walk :as walk]
    [clojure-sublimed.core :as core])
  (:import
    [java.io FilterWriter Reader StringReader Writer]
    [java.lang.reflect Field]
    [clojure.lang Compiler Compiler$CompilerException LineNumberingPushbackReader LispReader LispReader$ReaderException RT TaggedLiteral]))

(defonce ^:dynamic *out-fn*
  prn)

(defonce *out-fns
  (atom #{}))

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
      {"tag"    "ex"
       "val"    val
       "trace"  trace
       "source" source
       "line"   line
       "column" column})))

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
  (let [{:strs [code ns line column file]} form
        name   (or (some-> file (str/split #"[/\\]") last) "NO_SOURCE_FILE")
        ns     (symbol (or ns "user"))
        ns-obj (or
                 (find-ns ns)
                 (do
                   (require ns)
                   (find-ns ns)))
        ;; Adapted from clojure.lang.Compiler/load
        ;; Does not bind *uncheked-math*, *warn-on-reflection* and *data-readers*
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
                  Compiler/COLUMN_AFTER   (.getColumnNumber reader)
                  #'*e                    nil
                  #'*1                    nil
                  #'*2                    nil
                  #'*3                    nil})
        ret    (try
                 (loop [idx 0]
                   (vswap! *context* assoc "idx" idx)
                   (let [[obj obj-str] (read+string opts reader)]
                     (when-not (identical? obj eof)
                       (.set Compiler/LINE_AFTER (.getLineNumber reader))
                       (.set Compiler/COLUMN_AFTER (.getColumnNumber reader))
                       (vswap! *context* assoc
                         "from_line"   (.get Compiler/LINE_BEFORE)
                         "from_column" (.get Compiler/COLUMN_BEFORE)
                         "to_line"     (.get Compiler/LINE_AFTER)
                         "to_column"   (.get Compiler/COLUMN_AFTER)
                         "form"        obj-str)
                       (let [start (System/nanoTime)
                             ret   (Compiler/eval obj false)]
                         (*out-fn*
                           {"tag"  "ret"
                            "val"  (core/bounded-pr-str ret)
                            "time" (-> (System/nanoTime) (- start) (quot 1000000))})
                         (consume-ws reader)
                         (.set Compiler/LINE_BEFORE (.getLineNumber reader))
                         (.set Compiler/COLUMN_BEFORE (.getColumnNumber reader))
                         (recur (inc idx))))))
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
                   (pop-thread-bindings)))]))

(defn fork-eval [{:strs [id print_quota] :as form}]
  (swap! *evals assoc id 
    (future
      (binding [core/*print-quota* (or print_quota core/*print-quota*)]
        (try
          (core/track-vars
            (eval-code form))
          (catch Throwable t
            (try
              (report-throwable t)
              (catch Throwable t
                :ignore)))
          (finally
            (swap! *evals dissoc id)
            (vswap! *context* dissoc "idx" "from_line" "from_column" "to_line" "to_column" "form")
            (*out-fn*
              {"tag" "done"})))))))
 
(defn interrupt [{:strs [id]}]
  (when-some [f (@*evals id)]
    (future-cancel f)))

(def safe-meta?
  #{:ns :name :doc :file :arglists :forms :macro :special-form :protocol :line :column :added :deprecated :resource})

(defn lookup-symbol [form]
  (let [{:strs [id op symbol ns]} form
        ns     (clojure.core/symbol (or ns "user"))
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
          {"tag" "lookup"
           "val" meta'})
        {"tag" "ex"
         "val" (str "Symbol '" symbol " not found in ns '" ns)}))))

(defmacro watch [id form]
  `(let [res# ~form
         msg# {"tag"      "watch"
               "val"      (core/bounded-pr-str res#)
               "watch_id" ~id}]
     (doseq [out-fn# @*out-fns]
       (out-fn# msg#))
     res#))

(defn out-fn [out]
  (let [lock (Object.)]
    #(locking lock
       (binding [*out*            out
                 *print-readably* true]
         (prn (merge (sorted-map) (some-> *context* deref) %))))))

(defn repl []
  (let [out-fn (out-fn *out*)]
    (try
      (swap! *out-fns conj out-fn)
      (binding [*out-fn* out-fn
                *out*    (core/duplicate-writer (.getRawRoot #'*out*) "out" out-fn)
                *err*    (core/duplicate-writer (.getRawRoot #'*err*) "err" out-fn)
                core/*changed-vars (atom {})]
        (out-fn {"tag" "started"})
        (loop []
          (when
            (binding [*context* (volatile! {})]
              (try
                (let [form (read-command *in*)]
                  (core/set-changed-vars!)
                  (when-some [id (form "id")]
                    (vswap! *context* assoc "id" id))
                  (case (get form "op")
                    "eval"      (fork-eval form)
                    "interrupt" (interrupt form)
                    "lookup"    (lookup-symbol form)
                    (throw (Exception. (str "Unknown op: " (get form "op")))))
                  true)
                (catch Throwable t
                  (when-not (-> t ex-data ::stop)
                    (report-throwable t)
                    true))))
            (recur)))
        (doseq [[id f] @*evals]
          (future-cancel f)))
      (finally
        (swap! *out-fns disj out-fn)))))
