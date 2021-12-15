; SYNTAX TEST "Clojure (Sublime Clojure).sublime-syntax"


; VAR QUOTE
  #'map
; ^ keyword.operator.var
  #' , map
; ^^ keyword.operator.var
;   ^^^^^^ - keyword.operator.var
;    ^ punctuation.definition.comma


; DEREF
  @*atom
; ^ keyword.operator.deref
  @ , *atom
; ^ keyword.operator.deref
;  ^^^^^^^^ - keyword.operator.deref
;   ^ punctuation.definition.comma


; READER CONDITIONALS
  #?(:clj 1 :cljs 2)
; ^^^ punctuation.section.parens.begin
; ^^^^^^^^^^^^^^^^^^ meta.parens
;                  ^ punctuation.section.parens.end
;                   ^ - punctuation - meta.section
  #?@(:clj [3 4] :cljs [5 6])
; ^^^^ punctuation.section.parens.begin
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.parens
;                           ^ punctuation.section.parens.end
;                            ^ - punctuation - meta.section


; QUOTE
  '[datascript :as ds] []
; ^ keyword.operator.quote
; ^^^^^^^^^^^^^^^^^^^^ meta.quoted
;                     ^^^ -meta.quoted
  'datascript.core []
; ^ keyword.operator.quote
; ^^^^^^^^^^^^^^^^ meta.quoted
;                 ^^^ -meta.quoted
  ' , datascript.core []
; ^ keyword.operator.quote
;  ^^^^^^^^^^^^^^^^^^ - keyword.operator
; ^^^^^^^^^^^^^^^^^^^ meta.quoted
;   ^ punctuation.definition.comma


; SYNTAX QUOTE, UNQUOTE, UNQUOTE SPLICING
  `(let [x# ~x] ~@(do `(...))) []
; ^ keyword.operator.quote.syntax
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.quoted.syntax
;                             ^^^ - meta.quoted
;           ^ keyword.operator.unquote - invalid
;           ^^ meta.quoted.syntax meta.unquoted
;               ^^ keyword.operator.unquote - invalid
;               ^^^^^^^^^^^^^ meta.quoted.syntax meta.unquoted
;                     ^^^^^^ meta.quoted.syntax meta.unquoted meta.quoted.syntax
  ` , (~ , x ~@ , xs) []
; ^^^^^^^^^^^^^^^^^^^ meta.quoted.syntax
;                    ^^^ - meta.quoted.syntax
; ^ keyword.operator.quote.syntax
;  ^^^^^^^^^^^^^^^^^^^^^ - keyword.operator.quote.syntax
;   ^ punctuation.definition.comma
;      ^^^^ meta.unquoted
;      ^ keyword.operator.unquote
;       ^^^ - keyword.operator.unquote
;        ^ punctuation.definition.comma
;            ^^^^^^^ meta.unquoted
;            ^^ keyword.operator.unquote
;              ^^^^^ - keyword.operator.unquote
;               ^ punctuation.definition.comma


; METADATA
  ^{:a 1 :b 2} ^String ^"String" ^:dynamic x
; ^ punctuation.definition.metadata
; ^^^^^^^^^^^^ meta.metadata
;             ^ - meta.metadata
;              ^ punctuation.definition.metadata
;              ^^^^^^^ meta.metadata
;                     ^ - meta.metadata
;                      ^ punctuation.definition.metadata
;                      ^^^^^^^^^ meta.metadata
;                               ^ - meta.metadata
;                                ^ punctuation.definition.metadata
;                                 ^^^^^^^^ meta.metadata
;                                         ^ - meta.metadata
  ^ , :dynamic x
; ^^^^^^^^^^^^ meta.metadata
;             ^^ - meta.metadata
; ^ punctuation.definition.metadata
;  ^^^^^^^^^^^^^ - punctuation.definition.metadata
;   ^ punctuation.definition.comma
  ^123 x  ^[:dynamic true] x
;  ^^^ -meta.metadata
;          ^^^^^^^^^^^^^^^ -meta.metadata


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
;   ^^ constant.character.escape
;      ^^^ constant.character.escape
;          ^^^^ constant.character.escape
;               ^^^^^ constant.character.escape
;                     ^^^^ constant.character.escape
;                          ^^^^^^ constant.character.escape
;                                 ^^^^^ constant.character.escape
;                                       ^^^^^^^^^ constant.character.escape
;                                                 ^^^^^^^^^^ constant.character.escape
;                                                            ^^^^^^^^^^^^^^^^^^^^^^ constant.character.escape
  #"\t \n \r \f \a \e \cC \d \D \h \H \s \S \v \V \w \W"
;   ^^ constant.character.escape
;      ^^ constant.character.escape
;         ^^ constant.character.escape
;            ^^ constant.character.escape
;               ^^ constant.character.escape
;                  ^^ constant.character.escape
;                     ^^^ constant.character.escape
;                         ^^ constant.character.escape
;                            ^^ constant.character.escape
;                               ^^ constant.character.escape
;                                  ^^ constant.character.escape
;                                     ^^ constant.character.escape
;                                        ^^ constant.character.escape
;                                           ^^ constant.character.escape
;                                              ^^ constant.character.escape
;                                                 ^^ constant.character.escape
;                                                    ^^ constant.character.escape
  #"\p{IsLatin} \p{L} \b \b{g} \B \A \G \Z \z \R \X \0 \99 \k<gr3> \( \} \""
;   ^^^^^^^^^^^ constant.character.escape
;               ^^^^^ constant.character.escape
;                     ^^ constant.character.escape
;                        ^^^^^ constant.character.escape
;                              ^^ constant.character.escape
;                                 ^^ constant.character.escape
;                                    ^^ constant.character.escape
;                                       ^^ constant.character.escape
;                                          ^^ constant.character.escape
;                                             ^^ constant.character.escape
;                                                ^^ constant.character.escape
;                                                   ^^ constant.character.escape
;                                                      ^^^ constant.character.escape
;                                                          ^^^^^^^ constant.character.escape
;                                                                  ^^ constant.character.escape
;                                                                     ^^ constant.character.escape
;                                                                        ^^ constant.character.escape
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
;           ^^^^^^^^^^^^^^^^^^^ constant.character.escape - punctuation - keyword - invalid
;                              ^^ punctuation.section.quotation.end
;                                 ^ punctuation.section.parens.begin - constant.character.escape
  #"\Q ABC" #"(" #"["
; ^^^^^^^^^ string.regexp
;     ^^^^ constant.character.escape
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
;  ^^^^ source.symbol
;                            ^ punctuation.section.parens.end


; EVERYTHING
  (defn- ^{:meta :map} fn "doc" {:attr :map} [args] {:pre ()} body)
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.definition
;  ^^^^^ source.symbol
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
;  ^^^ source.symbol
;      ^ entity.name


; DEFMETHOD
  (defmethod x 1)
; ^^^^^^^^^^^^^^^ meta.definition
;  ^^^^^^^^^ source.symbol
;            ^ entity.name


; NAMESPACED DEF
  (rum/defcs x 1)
; ^^^^^^^^^^^^^^^ meta.definition & meta.parens
;            ^ entity.name
; ^ punctuation.section.parens.begin
;  ^^^^^^^^^ source.symbol
;     ^ punctuation.definition.symbol.namespace
;               ^ punctuation.section.parens.end


; DEF OF NAMESPACED SYMBOL
  (defmethod clojure.test/report :error [m])
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.definition & meta.parens
;            ^^^^^^^^^^^^^^^^^^^ entity.name
; ^ punctuation.section.parens.begin
;                        ^ punctuation.definition.symbol.namespace
;                                          ^ punctuation.section.parens.end


; NON-TOP DEF
  #?(:clj (def x 1))
;         ^^^^^^^^^ meta.definition & meta.parens
;              ^ entity.name
;         ^ punctuation.section.parens.begin
;                 ^ punctuation.section.parens.end


; ANONYMOUS FN
  #(+ %1 %2)
; ^^^^^^^^^^ meta.function & meta.parens
;           ^^ - meta.function
; ^^ punctuation.section.parens.begin
;          ^ punctuation.section.parens.end
