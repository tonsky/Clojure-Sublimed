(ns stacktraces)

(defn f []
  (throw (ex-info "Error" {:data :data})))

(defn g []
  (f))

(defn h []
  (g))

(g)
(h)

(/ 1 0)

(meta #'h)

(try
  (h)
  (catch Exception e
    (with-out-str
      (.printStackTrace e (java.io.PrintWriter. *out*)))))

(defn -main [& args]
  (h))
