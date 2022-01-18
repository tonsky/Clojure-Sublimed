(macroexpand-1 '(for [x (range) 
                      :when (pos? x) 
                      y (range) 
                      :let [z (+ x y)]]
                  [x y z]))

(throw (ex-info "Hey" {}))

(+ 1 2)

(take 1000 (range))