; SYNTAX TEST "Packages/sublime-clojure/ClojureC.sublime-syntax"


; REGEXPS
  #""
; ^^^ string.regexp
; ^^  punctuation.definition.string.begin
;   ^ punctuation.definition.string.end
;    ^ - string.regexp
  #"abc"
; ^^^^^^ string.regexp
; ^^  punctuation.definition.string.begin
;      ^ punctuation.definition.string.end
;       ^ - string.regexp
  #"\\ \07 \077 \0377 \xFF \uFFFF \x{0} \x{FFFFF} \x{10FFFF} \N{white smiling face}"
;   ^^ constant.character.escape.clojure
;      ^^^ constant.character.escape.clojure
;          ^^^^ constant.character.escape.clojure
;               ^^^^^ constant.character.escape.clojure
;                     ^^^^ constant.character.escape.clojure
;                          ^^^^^^ constant.character.escape.clojure
;                                 ^^^^^ constant.character.escape.clojure
;                                       ^^^^^^^^^ constant.character.escape.clojure
;                                                 ^^^^^^^^^^ constant.character.escape.clojure
;                                                            ^^^^^^^^^^^^^^^^^^^^^^ constant.character.escape.clojure
  #"\t \n \r \f \a \e \cC \d \D \h \H \s \S \v \V \w \W"
;   ^^ constant.character.escape.clojure
;      ^^ constant.character.escape.clojure
;         ^^ constant.character.escape.clojure
;            ^^ constant.character.escape.clojure
;               ^^ constant.character.escape.clojure
;                  ^^ constant.character.escape.clojure
;                     ^^^ constant.character.escape.clojure
;                         ^^ constant.character.escape.clojure
;                            ^^ constant.character.escape.clojure
;                               ^^ constant.character.escape.clojure
;                                  ^^ constant.character.escape.clojure
;                                     ^^ constant.character.escape.clojure
;                                        ^^ constant.character.escape.clojure
;                                           ^^ constant.character.escape.clojure
;                                              ^^ constant.character.escape.clojure
;                                                 ^^ constant.character.escape.clojure
;                                                    ^^ constant.character.escape.clojure
  #"\p{IsLatin} \p{L} \b \b{g} \B \A \G \Z \z \R \X \0 \99 \k<gr3> \( \} \""
;   ^^^^^^^^^^^ constant.character.escape.clojure
;               ^^^^^ constant.character.escape.clojure
;                     ^^ constant.character.escape.clojure
;                        ^^^^^ constant.character.escape.clojure
;                              ^^ constant.character.escape.clojure
;                                 ^^ constant.character.escape.clojure
;                                    ^^ constant.character.escape.clojure
;                                       ^^ constant.character.escape.clojure
;                                          ^^ constant.character.escape.clojure
;                                             ^^ constant.character.escape.clojure
;                                                ^^ constant.character.escape.clojure
;                                                   ^^ constant.character.escape.clojure
;                                                      ^^^ constant.character.escape.clojure
;                                                          ^^^^^^^ constant.character.escape.clojure
;                                                                  ^^ constant.character.escape.clojure
;                                                                     ^^ constant.character.escape.clojure
;                                                                        ^^ constant.character.escape.clojure
  #"\y \x \uABC \p{Is Latin} \k<1gr> "
;   ^^ invalid.illegal.escape.regexp
;      ^^ invalid.illegal.escape.regexp
;         ^^ invalid.illegal.escape.regexp
;               ^^ invalid.illegal.escape.regexp
;                            ^^ invalid.illegal.escape.regexp
  #"[^a-z\[^&&[-a-z-]]]"
;   ^ punctuation.section.brackets.begin
;    ^ keyword.operator.negation.regexp
;         ^ - punctuation.section.brackets
;          ^ - keyword.operator.negation.regexp
;           ^^ keyword.operator.intersection.regexp
;             ^ punctuation.section.brackets.begin
;              ^ - keyword.operator.range.regexp
;                ^ keyword.operator.range.regexp
;                  ^ - keyword.operator.range.regexp
;                   ^^ punctuation.section.brackets.end
;                     ^ - punctuation
  #"a? a* a+ a{1} a{1,} a{1,2}"
;    ^ keyword.operator.quantifier.regexp
;       ^ keyword.operator.quantifier.regexp
;          ^ keyword.operator.quantifier.regexp
;             ^^^ keyword.operator.quantifier.regexp
;                  ^^^^ keyword.operator.quantifier.regexp
;                        ^^^^^ keyword.operator.quantifier.regexp
  #"a?? a*? a+? a{1}? a{1,}? a{1,2}?"
;    ^^ keyword.operator.quantifier.regexp
;        ^^ keyword.operator.quantifier.regexp
;            ^^ keyword.operator.quantifier.regexp
;                ^^^^ keyword.operator.quantifier.regexp
;                      ^^^^^ keyword.operator.quantifier.regexp
;                             ^^^^^^ keyword.operator.quantifier.regexp
  #"a?+ a*+ a++ a{1}+ a{1,}+ a{1,2}+"
;    ^^ keyword.operator.quantifier.regexp
;        ^^ keyword.operator.quantifier.regexp
;            ^^ keyword.operator.quantifier.regexp
;                ^^^^ keyword.operator.quantifier.regexp
;                      ^^^^^ keyword.operator.quantifier.regexp
;                             ^^^^^^ keyword.operator.quantifier.regexp
  #"(x|(\(\||[)|])))"
;   ^ punctuation.section.parens.begin
;     ^ keyword.operator.union.regexp
;      ^ punctuation.section.parens.begin
;        ^ - punctuation.section.parens
;          ^ - keyword.operator
;           ^ keyword.operator.union.regexp
;             ^ - punctuation.section.parens - invalid
;              ^ - keyword.operator - invalid
;                ^^ punctuation.section.parens.end
;                  ^ invalid.illegal.stray-bracket-end
  #"(?<name>a) (?:a) (?idm-suxUa) (?sux-idm:a) (?=a) (?!a) (?<=a) (?<!a) (?>a)"
;   ^ punctuation.section.parens.begin
;    ^^^^^^^ keyword.operator.special.regexp
;            ^ punctuation.section.parens.end
;               ^^ keyword.operator.special.regexp
;                     ^^^^^^^^^ keyword.operator.special.regexp
;                                  ^^^^^^^^^ keyword.operator.special.regexp
;                                               ^^ keyword.operator.special.regexp
;                                                     ^^ keyword.operator.special.regexp
;                                                           ^^^ keyword.operator.special.regexp
;                                                                  ^^^ keyword.operator.special.regexp
;                                                                         ^^ keyword.operator.special.regexp
  #"(abc) \Q (a|b) [^DE] )] \" \E (abc)"
;       ^ punctuation.section.parens.end - constant.character.escape
;         ^^ punctuation.section.quotation.begin
;           ^^^^^^^^^^^^^^^^^^^ constant.character.escape.clojure - punctuation - keyword - invalid
;                              ^^ punctuation.section.quotation.end
;                                 ^ punctuation.section.parens.begin - constant.character.escape
  #"\Q ABC" #"(" #"["
; ^^^^^^^^^ string.regexp
;     ^^^^ constant.character.escape.clojure
;         ^ punctuation.definition.string.end - constant.character.escape
;          ^ - string.regexp
;           ^^^^ string.regexp
;               ^  - string.regexp
;                ^^^^ string.regexp
;                    ^  - string.regexp


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
