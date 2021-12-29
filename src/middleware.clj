(ns clojure-sublimed.middleware
  (:require
   [clojure.main :as main]
   [clojure.stacktrace :as stacktrace]
   [clojure.string :as str]
   [nrepl.middleware :as middleware]
   [nrepl.middleware.print :as print]
   [nrepl.middleware.caught :as caught]
   [nrepl.middleware.session :as session]
   [nrepl.transport :as transport])
  (:import
   [nrepl.transport Transport]))

(defn on-send [{:keys [transport] :as msg} on-send]
  (assoc msg :transport
    (reify Transport
      (recv [this]
        (transport/recv transport))
      (recv [this timeout]
        (transport/recv transport timeout))
      (send [this resp]
        (when-some [resp' (on-send resp)]
          (transport/send transport resp'))
        this))))

(defn after-send [{:keys [transport] :as msg} after-send]
  (assoc msg :transport
    (reify Transport
      (recv [this]
        (transport/recv transport))
      (recv [this timeout]
        (transport/recv transport timeout))
      (send [this resp]
        (transport/send transport resp)
        (after-send resp)
        this))))

(defn- root-cause [^Throwable t]
  (if-some [cause (some-> t .getCause)]
    (recur cause)
    t))

(defn print-root-trace [^Throwable t]
  (stacktrace/print-stack-trace (root-cause t)))

(defn- duplicate? [^StackTraceElement prev-el ^StackTraceElement el]
  (and
    (= (.getClassName prev-el) (.getClassName el))
    (= (.getFileName prev-el) (.getFileName el))
    (= "invokeStatic" (.getMethodName prev-el))
    (#{"invoke" "doInvoke"} (.getMethodName el))))

(defn- clear-duplicates [els]
  (for [[prev-el el] (map vector (cons nil els) els)
        :when (or (nil? prev-el) (not (duplicate? prev-el el)))]
    el))

(defn- trace-element-str [^StackTraceElement el]
  (let [file     (.getFileName el)
        clojure? (and file
                   (or (.endsWith file ".clj")
                     (.endsWith file ".cljc")
                     (= file "NO_SOURCE_FILE")))]
    (str
      "\t"
      (if clojure?
        (clojure.lang.Compiler/demunge (.getClassName el))
        (str (.getClassName el) "." (.getMethodName el)))
      " ("
      (.getFileName el)
      ":"
      (.getLineNumber el)
      ")")))

(defn- trace-str [^Throwable t]
  (str
    (.getSimpleName (class t))
    ": "
    (.getMessage t)
    (when-some [data (ex-data t)] (str " " (pr-str data)))
    "\n"
    (->> (.getStackTrace t)
      (take-while #(not= "clojure.lang.Compiler" (.getClassName ^StackTraceElement %)))
      (remove #(#{"clojure.lang.RestFn" "clojure.lang.AFn"} (.getClassName ^StackTraceElement %)))
      (clear-duplicates)
      (map trace-element-str)
      (str/join "\n"))))

(defn- populate-caught [{throwable ::caught/throwable :as resp}]
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
                       ::trace         (trace-str root))
                loc  (merge loc)
                data (update ::print/keys (fnil conj []) ::root-ex-data)
                data (assoc ::root-ex-data data))]
    resp'))

(defn wrap-errors [handler]
  (fn [msg]
    (handler (-> msg (on-send populate-caught)))))

(middleware/set-descriptor!
  #'wrap-errors
  {:requires #{#'caught/wrap-caught} ;; run inside wrap-caught
   :expects #{"eval"} ;; but outside of "eval"
   :handles {}})


(defn- redirect-output [resp]
  (when-some [out (:out resp)]
    (.print System/out out)
    (.flush System/out))
  (when-some [err (:err resp)]
    (.print System/err err)
    (.flush System/err))
  resp)

(defn wrap-output [handler]
  (fn [msg]
    (handler (-> msg (on-send redirect-output)))))

(middleware/set-descriptor!
  #'wrap-output
  {:requires #{}
   :expects #{"eval"} ;; run outside of "eval"
   :handles {}})


(defn time-eval [handler]
  (fn [{:keys [op] :as msg}]
    (if (= "eval" op)
      (let [start (System/nanoTime)]
        (-> msg
          (on-send #(cond-> % (contains? % :value) (assoc ::time-taken (- (System/nanoTime) start))))
          (handler)))
      (handler msg))))

(middleware/set-descriptor!
  #'time-eval
  {:requires #{#'wrap-output #'wrap-errors #'print/wrap-print}
   :expects #{"eval"}
   :handles {}})


(defn clone-and-eval [handler]
  (fn [{:keys [id op session transport] :as msg}]
    (if (= op "clone-eval-close")
      (let [*new-session (promise)]
        (-> {:id id :op "clone" :session session :transport transport}
          (on-send #(do (deliver *new-session (:new-session %)) %))
          (handler))
        (-> msg
          (assoc :session @*new-session :op "eval")
          (after-send (fn [resp]
                        (when (and
                                (= (:id resp) id)
                                (= (:session resp) @*new-session)
                                (contains? (:status resp) :done))
                          (future ((session/session handler) {:id id :op "close" :session @*new-session :transport transport})))))
          (handler)))
      (handler msg))))

(middleware/set-descriptor!
  #'clone-and-eval
  {:requires #{}
   :expects #{"eval" "clone"}
   :handles {"clone-and-eval"
             {:doc "Clones current session, evals given code in the cloned session"}}})
