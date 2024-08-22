; SYNTAX TEST "Clojure (Sublimed).sublime-syntax"

  `~x
; ^ meta.quoted.syntax
;  ^^ meta.quoted.syntax meta.unquoted

  '~x
;  ^ invalid

  '#'var
; ^^^^^^ meta.quoted
;  ^^^^^ meta.var

  #' ,,, map
; ^^^^^^^^^^ meta.var
; ^^ punctuation.definition.var
;   ^^^^^^^^ - punctuation.definition.var
;    ^^^ punctuation.definition.comma
  #'123
; ^^ meta.var
;   ^^^ - meta.var

  @ , *atom
; ^^^^^^^^^ meta.deref
  @@@*atom
; ^^^^^^^^ meta.deref meta.deref meta.deref
;  ^^^^^^^ meta.deref meta.deref
;   ^^^^^^ meta.deref

  #?  ,,, ,,  (:clj 1 :cljs 2)
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.reader_conditional meta.parens
; ^^ punctuation.definition.reader_conditional
; ^^ punctuation.section.parens.begin
;             ^ punctuation.section.parens.begin
;     ^^^ punctuation.definition.comma
;         ^^ punctuation.definition.comma

  #? #_clj (:clj 123)
; ^^ meta.reader_conditional
;    ^^^^^^^^^^^^^^^^ - meta.reader_conditional

  ^^x y z
; ^^^^^ meta.metadata
;  ^^ meta.metadata meta.metadata
;      ^^ - meta.metadata
  ^^()()()
; ^^^^^^ meta.metadata
;  ^^^ meta.metadata meta.metadata
;       ^^ - meta.metadata
  (((^^x y z)))
; ^^^^^^^^^^^^^ meta.parens
;  ^^^^^^^^^^^ meta.parens meta.parens
;   ^^^^^^^^^ meta.parens meta.parens meta.parens
;    ^^^ meta.metadata
;       ^^^^^^^ - meta.metadata
