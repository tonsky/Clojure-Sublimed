; skips

; (/ 1 0)
#_(/ 2 0)
#_#_(/ 3 0) (/ 4 0)

; simple expr
(+ 1 2)
 (+ 3 4) 

*warn-on-reflection*

(str 1 '\newline 2)

"xxx\nyyy\"zzz\\aaa\t"

; long value
(range 300)

(range 1 100)

; complex value
(bean "abc")

; namespaced maps
#:clojure.core{:first "Terence", :last "Tao", :occupation #:inner{:name "Mathematics"}}

; delayed eval
(do (Thread/sleep 1400) :first)
*e
(do (Thread/sleep 1300) :second)
(do (Thread/sleep 1200) :third)
(do (Thread/sleep 1100) :fourth)
(do (Thread/sleep 990) :fifth)
(do (Thread/sleep 490) :sixth)
(do (Thread/sleep 90) :seventh)
(do (Thread/sleep 45) :eigths)

(defn x)

; infinite sequence
(range) 

; print
(println "Hello, Sublime!")
(.println System/out "System.out.println")

; print to stderr
(binding [*out* *err*] (println "abc"))
(.println System/err "System.err.println")

; print in background
(doseq [i (range 0 10)] (Thread/sleep 1000) (println i))

; throw exception
(throw (ex-info 
  "abc" {:a 1}))
#?(:clj (throw (Exception. "ex with msg"))
   :cljs (throw (js/Error. "ex with msg")))
*e
(/ 1 0)

; truncating
(range) 
(throw (ex-info "abc" {:a (range 300)}))

; Phantom wrapping
#{1 2 3 4 5 6 7 8 9 {:a 1 :bbb 234 :cc 5} 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 {:a 6 :bbb 789 :cc 10} 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99}

[[1 "looooooooooooooooooooooooooooooooong" 2] [1 "looooooooooooooooooooooooooooooooong" 2] [1 "looooooooooooooooooooooooooooooooong" 2] [1 "looooooooooooooooooooooooooooooooong" 2] [1 "looooooooooooooooooooooooooooooooong" 2] [1 "looooooooooooooooooooooooooooooooong" 2] [1 "looooooooooooooooooooooooooooooooong" 2] [1 "looooooooooooooooooooooooooooooooong" 2]]

(defn x)

(try
  (eval '(defn x))
  (catch Throwable e
    e))

; lookups
var
if
cond
*out*
*warn-on-reflection*
*print-namespace-maps*
(keys @clojure-sublimed.socket-repl/*evals)
set!
clojure.set/join
find-keyword
(def ^{:doc "Doc"} const 0)
(defn f2
  "Test function"
  ([] (f2 1))
  ([a] (f2 1 a))
  ([a & rest] (println a rest)))

; wrapped exception (RuntimeException inside CompilerException)
unresolved-symbol

(defn f [])

(defn g []
  (let [x unresolved-symbol]
    ))

; top-level forms
true
false
symbol -a +a
:keyword
:namespaced/keyword
::keyword
::namespaced/keyword
\n
\newline
\o377
100 -1 +1
100N
100.0
1/2
"string" 
"multi
   line
 string with   \\n
   some \n  spaces"
#"regex"
@deref
#'var
#_"hello"
#inst "2021-10-20"
#uuid "d3e13f30-85b1-4334-9b67-5e6d580e266c"
#p "abc"
^:false sym
^{:meta [true false]} sym
[1 2 3]
'(1 2 3)
{:a 1 :b 2 :c 3}
'({[] #{}})
[{() #{}}]
{[#{()}] '(((())))}
#{[()]}

; comment forms
(comment
  "hello"
  (println "hello"))
(comment "hello")
(comment "hello" )
(  comment "hello")

; column reports for Unicode
"fhsjdfd\ufhjsdf"
#"alkjdljl👨🏿kjlkj👨🏻‍🤝‍👨🏼ljasljlkjasjasljas\uakldjasdlk"

; two forms
(+ 1 2)(+ 3 4)
:first(Thread/sleep 1000):second

; malformed expr
(+ 1
(+ 1 2))

; namespace
(clojure.pprint/pprint :abc)
clojure.pprint
