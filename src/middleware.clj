(ns clojure-sublimed.middleware
  (:require
    [clojure.main :as main]
    [clojure.pprint :as pprint]
    [clojure.stacktrace :as stacktrace]
    [clojure.string :as str]
    [nrepl.middleware :as middleware]
    [nrepl.middleware.print :as print]
    [nrepl.middleware.caught :as caught]
    [nrepl.middleware.session :as session]
    [nrepl.transport :as transport])
  (:import
    [clojure.lang ExceptionInfo]
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

;; CompilerException has location info, but its cause RuntimeException has the message ¯\_(ツ)_/¯
(defn- root-cause [^Throwable t]
  (loop [t t
         data nil]
    (if (and
          (nil? data)
          (or
            (instance? clojure.lang.Compiler$CompilerException t)
            (instance? clojure.lang.LispReader$ReaderException t))
          (not= [0 0] ((juxt :clojure.error/line :clojure.error/column) (ex-data t))))
      (recur t (ex-data t))
      (if-some [cause (some-> t .getCause)]
        (recur cause data)
        (if data
          (ExceptionInfo. "Wrapper to pass CompilerException ex-data" data t)
          t)))))

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

(defn- trace-element [^StackTraceElement el]
  (let [file     (.getFileName el)
        clojure? (or (nil? file)
                   (= file "NO_SOURCE_FILE")
                   (.endsWith file ".clj")
                   (.endsWith file ".cljc"))]
    {:method (if clojure?
               (clojure.lang.Compiler/demunge (.getClassName el))
               (str (.getClassName el) "." (.getMethodName el)))
     :file   (.getFileName el)
     :line   (.getLineNumber el)}))

(defn as-table [table]
  (let [[method file] (for [col [:method :file]]
                        (->> table
                          (map #(get % col))
                          (map str)
                          (map count)
                          (reduce max (count "null"))))
        format-str (str "\t%-" method "s\t%-" file "s\t:%d")]
    (->> table
      (map #(format format-str (:method %) (:file %) (:line %)))
      (str/join "\n"))))

(defn- trace-str [^Throwable t]
  (let [{:clojure.error/keys [source line column]} (ex-data t)
        cause (or (.getCause t) t)]
    (str
      "\n"
      (->> (.getStackTrace cause)
        (take-while #(not (#{"clojure.lang.Compiler" "clojure.lang.LispReader"}
                           (.getClassName ^StackTraceElement %))))
        (remove #(#{"clojure.lang.RestFn" "clojure.lang.AFn"} (.getClassName ^StackTraceElement %)))
        (clear-duplicates)
        (map trace-element)
        (reverse)
        (as-table))
      "\n>>> "
      (.getSimpleName (class cause))
      ": "
      (.getMessage cause)
      (when (or source line column)
        (str " (" source ":" line ":" column ")"))
      (when-some [data (ex-data cause)]
        (str " " (pr-str data))))))

(defn print-root-trace [^Throwable t]
  (println (trace-str t)))

(defn- populate-caught [{t ::caught/throwable :as resp}]
  (let [root  ^Throwable (root-cause t)
        {:clojure.error/keys [source line column]} (ex-data root)
        cause ^Throwable (or (some-> root .getCause) root)
        data  (ex-data cause)
        resp' (cond-> resp
                cause  (assoc
                         ::caught/throwable root
                         ::root-ex-msg      (.getMessage cause)
                         ::root-ex-class    (.getSimpleName (class cause))
                         ::trace            (trace-str root))
                source (assoc  ::source source)
                line   (assoc  ::line line)
                column (assoc  ::column column)
                data   (update ::print/keys (fnil conj []) ::root-ex-data)
                data   (assoc  ::root-ex-data data))]
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

(defn pprint [value writer opts]
  (binding [pprint/*print-right-margin* 120]
    (pprint/pprint value writer)))