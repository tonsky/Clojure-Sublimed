(ns stacktraces)

(defn f []
  (throw (ex-info "Error" {:data :data})))

(defn g []
  (f))

(defn h []
  (g))

(meta #'h)

(h)

(defn -main [& args]
  (h))
