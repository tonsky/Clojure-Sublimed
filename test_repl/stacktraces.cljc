(ns stacktraces)

(defn f []
  (throw (ex-info "Error" {:data :data})))

(defn g []
  (f))

(defn h []
  (g))

(h)

(meta #'h)

(try
  (h)
  (catch Exception e
    (with-out-str
      (.printStackTrace e))))

(defn -main [& args]
  (h))
