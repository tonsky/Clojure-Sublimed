; simple expr
(+ 1 2)
 (+ 1 2) 

(str 1 '\newline 2)

"xxx\nyyy\"zzz\\aaa\t"

; long value
(range 300)

; complex value
(bean "abc")

; delayed eval
(do (Thread/sleep 5000) :done)
(do (Thread/sleep 5000) :done)
(do (Thread/sleep 5000) :done)
(do (Thread/sleep 5000) :done)
(do (Thread/sleep 900) :done)
(do (Thread/sleep 490) :done)
(do (Thread/sleep 90) :done)

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
(throw (Exception. "ex with msg"))
*e

; truncating
(range) 
(throw (ex-info "abc" {:a (range 300)}))

; lookups
var
if
cond
*out*
*warn-on-reflection*
*print-namespace-maps*
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
