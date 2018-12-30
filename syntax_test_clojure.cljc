; SYNTAX TEST "Packages/sublime-clojure/ClojureC.sublime-syntax"


; SIMPLE DEFN
  (defn fname [arg arg2] body)
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.definition
;                             ^ -meta.definition
;       ^^^^^ source.symbol entity.name 
; ^ punctuation.brackets.begin - meta.brackets.inner
;  ^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.brackets.inner
;                            ^ punctuation.brackets.end - meta.brackets.inner


; EVERYTHING
  (defn- ^{:meta :map} fn "doc" {:attr :map} [args] {:pre ()} body)
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.definition
;        ^^^^^^^^^^^^^ meta.metadata
;                      ^^ entity.name


; INCOMPLETE FNS ARE STILL CLOSED
  (defn)
; ^^^^^^ meta.definition
;       ^ -meta.definition
  (defn f)
; ^^^^^^^^ meta.definition
;         ^ -meta.definition
;       ^ entity.name


; PRECEDING SYMBOLS AND OTHER GARBAGE DO NOT CONFUSE ENTITY.NAME LOOKUP
  (defn 15 "str" {a b} fname 15 sym \n ("abc") [])
;                      ^^^^^ entity.name


; DEF
  (def x 1)
; ^^^^^^^^^ meta.definition
;      ^ entity.name


; DEFMETHOD
  (defmethod x 1)
; ^^^^^^^^^^^^^^^ meta.definition
;            ^ entity.name


; NAMESPACED DEF
  (rum/defcs x 1)
; ^^^^^^^^^^^^^^^ meta.definition
;            ^ entity.name
; ^ punctuation.brackets.begin - meta.brackets.inner
;  ^^^^^^^^^^^^^ meta.brackets.inner
;     ^ punctuation.definition.symbol.namespace.clojure
;               ^ punctuation.brackets.end - meta.brackets.inner


; DEF OF NAMESPACED SYMBOL
  (defmethod clojure.test/report :error [m])
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.definition
;            ^^^^^^^^^^^^^^^^^^^ entity.name
; ^ punctuation.brackets.begin - meta.brackets.inner
;  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.brackets.inner
;                        ^ punctuation.definition.symbol.namespace.clojure
;                                          ^ punctuation.brackets.end - meta.brackets.inner


; NON-TOP DEF
  ?#(:clj (def x 1))
;         ^^^^^^^^^ meta.definition
;              ^ entity.name
