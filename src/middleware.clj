(ns sublime-clojure.middleware
  (:require
   [clojure.main :as main]
   [clojure.stacktrace :as stacktrace]
   [clojure.string :as str]
   [nrepl.middleware :as middleware]
   [nrepl.middleware.print :as print]
   [nrepl.middleware.caught :as caught]
   [nrepl.transport :as transport])
  (:import
   [nrepl.transport Transport]))

(defn- root-cause [^Throwable t]
  (when t
    (loop [t t]
      (if-some [cause (.getCause t)]
        (recur cause)
        t))))

(defn print-root-trace [^Throwable t]
  (stacktrace/print-stack-trace (root-cause t)))

(defn trace [^Throwable t]
  (let [trace (with-out-str
                (.printStackTrace t (java.io.PrintWriter. *out*)))]
    (if-some [idx (str/index-of trace "\n\tat clojure.lang.Compiler.eval(Compiler.java:")]
      (subs trace 0 idx)
      trace)))

(defn- caught-transport [{:keys [transport] :as msg}]
  (reify Transport
    (recv [this]
      (transport/recv transport))
    (recv [this timeout]
      (transport/recv transport timeout))
    (send [this {throwable ::caught/throwable :as resp}]
      (let [root  (root-cause throwable)
            data  (ex-data root)
            loc   (when (instance? clojure.lang.Compiler$CompilerException throwable)
                    {::line   (or (.-line throwable) (:clojure.error/line (ex-data throwable)))
                     ::column (:clojure.error/column (ex-data throwable))
                     ::source (or (.-source throwable) (:clojure.error/source (ex-data throwable)))})
            resp' (cond-> resp
                    root (assoc
                           ::root-ex-msg   (.getMessage root)
                           ::root-ex-class (.getSimpleName (class root))
                           ::trace         (trace root))
                    loc  (merge loc)
                    data (update ::print/keys (fnil conj []) ::root-ex-data)
                    data (assoc ::root-ex-data data))]
        (transport/send transport resp'))
      this)))

(defn wrap-errors [handler]
  (fn [msg]
    (handler (assoc msg :transport (caught-transport msg)))))

(middleware/set-descriptor!
  #'wrap-errors
  {:requires #{#'caught/wrap-caught} ;; run inside wrap-caught
   :expects #{"eval"} ;; but outside of "eval"
   :handles {}})

(defn- output-transport [{:keys [transport] :as msg}]
  (reify Transport
    (recv [this]
      (transport/recv transport))
    (recv [this timeout]
      (transport/recv transport timeout))
    (send [this resp]
      (when-some [out (:out resp)]
        (.print System/out out)
        (.flush System/out))
      (when-some [err (:err resp)]
        (.print System/err err)
        (.flush System/err))
      (transport/send transport resp)
      this)))

(defn wrap-output [handler]
  (fn [msg]
    (handler (assoc msg :transport (output-transport msg)))))

(middleware/set-descriptor!
  #'wrap-output
  {:requires #{}
   :expects #{"eval"} ;; run outside of "eval"
   :handles {}})
