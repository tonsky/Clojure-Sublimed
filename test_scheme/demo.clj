;; Clojure Sublimed
;; ----------------

;; Nested parentheses
((())) ([{}]) [#{} #?(:clj) #()]

;; Reader comments
(let [x 1 #_(throw (ex-info "" {}))
      y 2
      ;; Including stacking
      #_#_ z (/ 1 0)])

;; Block comments
(comment
  (/ 1 0))

;; Unused symbols
(defn fn [a _unused & _])

;; Namespaces
clojure.string/index-of

;; Metadata
^{:doc "abc"} x

;; Quoting
... '[a b c] ...

;; And unquoting
`(let [x# ~(gensym x)]
       ...)

;; Trickiy edge cases
(defn #_c ^int fn "doc" {:attr :map} [])
'^int sym
^'tag sym
#_#_()()()

;; Error detection
"\u221 \x" #".* \E) \y"
#inst "1985-" \aa 1/0 09 #123 nnil truee
:kv: :kv/ :/kv :/ :kv/ab: :kv/ab/




(defn reverse
  "Returns a seq of the items in reverse order."
  {:added "1.0"
   :static true}
  [coll]
  (reduce1 conj () coll))

;; math stuff
(defn ^:private nary-inline
  ([op]
   (nary-inline op op))
  ([op unchecked-op]
   (fn [x y & more]
     (let [op (if *unchecked-math*
                unchecked-op op)]
       (reduce1
         (fn [a b]
           `(. clojure.lang.Numbers (~op ~a ~b)))
         `(. clojure.lang.Numbers (~op ~x ~y))
         more))))))

(defn ^:private >1? [n]
  (clojure.lang.Numbers/gt n 1))

(defn ^:private >0? [n]
  (clojure.lang.Numbers/gt n 0))
