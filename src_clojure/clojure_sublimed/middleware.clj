(ns clojure-sublimed.middleware
  (:require
    [clojure.pprint :as pprint]
    [clojure.string :as str]
    [clojure-sublimed.exception :as exception]
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

(defn print-root-trace [^Throwable t]
  (println (exception/trace-str t)))

(defn- populate-caught [{t ::caught/throwable :as resp}]
  (let [root  ^Throwable (exception/root-cause t)
        {:clojure.error/keys [source line column]} (ex-data root)
        cause ^Throwable (or (some-> root .getCause) root)
        data  (ex-data cause)
        resp' (cond-> resp
                cause  (assoc
                         ::caught/throwable root
                         ::root-ex-msg      (.getMessage cause)
                         ::root-ex-class    (.getSimpleName (class cause))
                         ::trace            (exception/trace-str root))
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