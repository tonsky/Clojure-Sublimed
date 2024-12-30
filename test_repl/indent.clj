  (when something
something)

((([]{}))asdas(()))

(when something
  body)

(defn f [x]
  body)
  
(defn f
[x]      

body)
  
(defn many-args [a b c
d e f]

body)
  
(defn multi-arity
([x]
body)
([x y]
body))

(let [x 1
y 2]
body)
  
[1 2 3
4 5 6]

{::key-1 v1
:key-2 v2}

(1 2
3 4)

(ns abc
(:require
a b
c))

#{a b c
d e f}

#:ns{:key v}

#?(:clj 1
:cljs 2)

#?@(:clj [1]
:cljs [2])

(abcdef abcde abcd abc ab a)

(a ab abc abcd abcde abcdef)

  (abc)

  "asdasd
 asdas
     aksjdlkj
lkjdlk"

"((([[[abc]]])))"

(def x
"asdasd
 asdas
     aksjdlkj
lkjdlk")

(def y [
"asdas"
"adasd"
"adasd"
])

;; asds
  ;; asdas
    ;; asdasd

[]
{}
#'()

(if "((([[[{{{"
\(
;; ((([[[{{{
nil)

(letfn [(square [x]
(* x x))
(sum [x y]
(+ x y))]
(let [x 3
y 4]
(sum (square x)
(square y))))

(let [x 1
      x+y 22
      x+y+z 333
      a {:a 1, :b 2, :c 3}
      bb {:a+b 123, :c+d 456, :e+f 789}
      ccc {:a+b+c 12345, :d+e+f 67890, :g+h+i 0xFFFFFF}])
