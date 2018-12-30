; SYNTAX TEST "Packages/sublime-clojure/ClojureC.sublime-syntax"


; SIMPLE DEFN
  (defn fname [arg arg2] body)
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.definition & meta.parens
;                             ^ -meta.definition -meta.parens
;       ^^^^^ source.symbol entity.name 
; ^ punctuation.section.parens.begin
;                            ^ punctuation.section.parens.end


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
; ^^^^^^^^^^^^^^^ meta.definition & meta.parens
;            ^ entity.name
; ^ punctuation.section.parens.begin
;     ^ punctuation.definition.symbol.namespace.clojure
;               ^ punctuation.section.parens.end


; DEF OF NAMESPACED SYMBOL
  (defmethod clojure.test/report :error [m])
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.definition & meta.parens
;            ^^^^^^^^^^^^^^^^^^^ entity.name
; ^ punctuation.section.parens.begin
;                        ^ punctuation.definition.symbol.namespace.clojure
;                                          ^ punctuation.section.parens.end


; NON-TOP DEF
  #?(:clj (def x 1))
;         ^^^^^^^^^ meta.definition & meta.parens
;              ^ entity.name
;         ^ punctuation.section.parens.begin
;                 ^ punctuation.section.parens.end
