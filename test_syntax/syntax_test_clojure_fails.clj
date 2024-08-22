; SYNTAX TEST "Clojure (Sublimed).sublime-syntax"

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
