(ns clojure-sublimed.socket-repl
  (:require
    [clojure.string :as str]
    [clojure-sublimed.exception :as exception])
  (:import
    [java.io Writer]))

(def ^:dynamic *out-fn*)

(def ^:dynamic *context*)

(defn stop! []
  (throw (ex-info "Stop" {::stop true})))

(defn read-command [in]
  (let [[form s] (read+string {:eof ::eof, :read-cond :allow} in)]
    (when (= ::eof form)
      (stop!))
    
    (vswap! *context* assoc :form s)
    
    (when-not (map? form)
      (throw (Exception. "Unexpected form")))
    
    form))

(defn eval-code [form]
  (let [{:keys [id op code ns line column file]} form
        code' (binding [*read-eval* false]
                (read-string {:read-cond :preserve} code))
        start (System/nanoTime)
        ret   (eval `(do (in-ns '~(or ns 'user)) ~code'))
        time  (-> (System/nanoTime)
                (- start)
                (quot 1000000))]
    (*out-fn*
      {:tag  :ret
       :id   id
       :val  ret
       :time time})))

(def safe-meta?
  #{:ns :name :doc :file :arglists :forms :macro :special-form :protocol :line :column :added :deprecated :resource})

(defn lookup-symbol [form]
  (let [{:keys [id op symbol ns] :or {ns 'user}} form
        ns     (clojure.core/symbol ns)
        symbol (clojure.core/symbol symbol)
        meta   (if (special-symbol? symbol)
                 (assoc ((requiring-resolve 'clojure.repl/special-doc) symbol)
                   :ns 'clojure.core
                   :file "clojure/core.clj"
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
            *err*    (.getRawRoot #'*err*)]
    (*out-fn* {:tag :started})
    (loop []
      (when
        (binding [*context* (volatile! {})]
          (try
            (let [form (read-command *in*)]
              (when-some [id (:id form)]
                (vswap! *context* assoc :id id))
                
              (case (:op form)
                :close  (stop!)
                :eval   (eval-code form)
                :lookup (lookup-symbol form)
                (throw (Exception. (str "Unknown op: " (:op form)))))
              true)
            (catch Throwable t
              (when-not (-> t ex-data ::stop)
                (let [root  ^Throwable (exception/root-cause t)
                      {:clojure.error/keys [source line column]} (ex-data root)
                      cause ^Throwable (or (some-> root .getCause) root)
                      data  (ex-data cause)
                      class (.getSimpleName (class cause))
                      msg   (.getMessage cause)
                      val   (cond-> (str class ": " msg)
                              data
                              (str " " (pr-str data))
                              
                              (and source line column) 
                              (str " (" source ":" line ":" column ")"))
                      trace (exception/trace-str root)]
                  (*out-fn*
                    (merge
                      {:tag    :ex
                       :val    val
                       :trace  trace
                       :source source
                       :line   line
                       :column column}
                      @*context*))
                  true)))))
        (recur)))))

(repl)
