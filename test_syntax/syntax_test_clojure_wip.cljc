; SYNTAX TEST "Clojure (Sublimed).sublime-syntax"

  ( , , defn f) 
; ^^^^^^^^^^^^^ meta.definition
;              ^ -meta.definition
;            ^ entity.name

  (def 15 fun)
;         ^^^ - entity.name
  (def "str" fun)
;            ^^^ - entity.name
  (def {a b} fun)
;            ^^^ - entity.name
  (defn 15 "str" {a b} fname 15 sym \n ("abc") [])
;                      ^^^^^ - entity.name


; ^^^^^^ comment.block.clojure
  ( , , , #_skip 
; ^^^^^^^ comment.block.clojure
   comment
; ^^^^^^^^ comment.block.clojure
    123)
; ^^^^^^ comment.block.clojure
