(ns watches)

(defn f []
  (dotimes [i 10]
    (+ i (rand-int 100))
    (Thread/sleep 100)))

(f)
