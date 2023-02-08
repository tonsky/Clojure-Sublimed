(ns clojure-sublimed.socket-repl
  (:require
    [clojure.string :as str]
    [clojure-sublimed.exception :as exception])
  (:import
    [java.io Writer]))

(def ^:dynamic *out-fn*
  prn)

(def ^:dynamic *context*
  nil)

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

(defn reader [code line column]
  (let [reader (clojure.lang.LineNumberingPushbackReader. (java.io.StringReader. code))]
    (when line
      (.setLineNumber reader (int line)))
    (when column
      (when-some [field (->> clojure.lang.LineNumberingPushbackReader
                          (.getDeclaredFields)
                          (filter #(= "_columnNumber" (.getName

(defn eval-code [form]
  (let [{:keys [id op code ns line column file]} form
        ; code' (binding [*read-eval* false]
        ;         (read-string {:read-cond :preserve} code))
        start  (System/nanoTime)
        ns     (or ns 'user)
        ns-obj (or
                 (find-ns ns)
                 (do
                   (require ns)
                   (find-ns ns)))
        name   (last (str/split file #"[/\\]"))
        ; ret   (eval `(do (in-ns '~(or ns 'user)) ~code'))
        ret    (binding [*read-eval* false
                         *ns*        ns-obj]
                 (clojure.lang.Compiler/load (reader code line column) file name))
        time   (-> (System/nanoTime)
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
                        (if (safe-meta?