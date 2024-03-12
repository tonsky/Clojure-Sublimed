(require ' [puget.printer :as puget])

(puget/cprint [nil
               true
               \space
               "string"
               {:omega 123N
                :alpha '(func x y)
                :gamma 3.14159}
               #{\a "heterogeneous" :set}
               (java.util.Currency/getInstance "USD")
               (java.util.Date.) 
               (java.util.UUID/randomUUID)])