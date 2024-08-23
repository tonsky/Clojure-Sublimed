; SYNTAX TEST "Clojure (Sublimed).sublime-syntax"


;;;;;;;;;; CONSTANTS ;;;;;;;;;;

  nil true false
; ^^^ constant.language
;     ^^^^ constant.language
;          ^^^^^ constant.language
  Nil nnil truee
; ^^^^^^^^^^^^^^ -constant.language


;;;;;;;;;; STRINGS ;;;;;;;;;;

  "abcde" 
; ^^^^^^^ string.quoted.double
; ^       punctuation.definition.string.begin
;       ^ punctuation.definition.string.end
;        ^ -string.quoted.double
  "" 
; ^^ string.quoted.double
; ^  punctuation.definition.string.begin
;  ^ punctuation.definition.string.end
;   ^ -string.quoted.double
  "([{)]} ;"
; ^^^^^^^^^^ string.quoted.double
  "multi
; ^       punctuation.definition.string.begin
; ^^^^^^  string.quoted.double
  line
; ^^^^    string.quoted.double
string"
; ^^^^^   string.quoted.double
;     ^   punctuation.definition.string.end


;;;;;;;;;; ESCAPES ;;;;;;;;;;

  "\" \\ \' \r \n \b \t \f \377 \u221e \u221E"
;  ^^ constant.character.escape
;  ^  punctuation.definition.character.escape.begin     
;    ^ -constant.character.escape
;     ^^ constant.character.escape
;        ^^ constant.character.escape
;           ^^ constant.character.escape
;              ^^ constant.character.escape
;                 ^^ constant.character.escape
;                    ^^ constant.character.escape
;                       ^^ constant.character.escape
;                          ^^^^ constant.character.escape
;                               ^^^^^^ constant.character.escape
;                                      ^^^^^^ constant.character.escape
;; INCORRECT STRINGS
  "\x \888 \u000 \u000g"
;  ^^ constant.character.escape & invalid.illegal.escape.string
;  ^  punctuation.definition.character.escape.begin 
;    ^ -constant.character.escape
;     ^^ constant.character.escape & invalid.illegal.escape.string
;          ^^ constant.character.escape & invalid.illegal.escape.string
;                ^^ constant.character.escape & invalid.illegal.escape.string


;;;;;;;;;; CHARACTERS ;;;;;;;;;;

  \c \newline \u221E \u221e \o3 \o50 \o377
; ^  punctuation.definition.character.begin
; ^^ constant.character
;   ^ -constant.character
;    ^^^^^^^^ constant.character
;             ^^^^^^ constant.character
;                    ^^^^^^ constant.character
;                           ^^^ constant.character
;                               ^^^^ constant.character
;                                    ^^^^^ constant.character
  \\ \] \) \} \" \' \; \,
; ^^ constant.character
;    ^^ constant.character
;       ^^ constant.character
;          ^^ constant.character
;             ^^ constant.character
;                ^^ constant.character
;                   ^^ constant.character
;                      ^^ constant.character
;; NOT CHARACTERS
  \aa \u11 \o378 \
; ^^ constant.character & invalid.illegal.character
; ^  punctuation.definition.character.begin
;     ^^^^ constant.character & invalid.illegal.character
;          ^^^^^ constant.character & invalid.illegal.character
;                ^ constant.character & invalid.illegal.character
  a\b
; ^^^ -constant.character


;;;;;;;;;; LINE COMMENTS ;;;;;;;;;;

  ; single semicolon
; ^^^^^^^^^^^^^^^^^^ comment.line
; ^                  punctuation.definition.comment.line
;  ^^^^^^^^^^^^^^^^^ -punctuation.definition.comment.line
  "abc" ; after something
;       ^^^^^^^^^^^^^^^^^ comment.line
;       ^                 punctuation.definition.comment.line


;;;;;;;;;; READER COMMENTS ;;;;;;;;;;

  #_abc #_"abc" #_123 #_:kw #_nil #_\a #_1.23 #_1/2 
; ^^ punctuation.definition.comment.reader
; ^^^^^ comment.reader
;      ^ - comment
;       ^^ punctuation.definition.comment.reader
;       ^^^^^^^ comment.reader
;              ^ - comment
;               ^^ punctuation.definition.comment.reader
;               ^^^^^ comment.reader
;                    ^ - comment
;                     ^^ punctuation.definition.comment.reader
;                     ^^^^^ comment.reader
;                          ^ - comment
;                           ^^ punctuation.definition.comment.reader
;                           ^^^^^ comment.reader
;                                ^ - comment
;                                 ^^ punctuation.definition.comment.reader
;                                 ^^^^ comment.reader
;                                     ^ - comment
;                                      ^^ punctuation.definition.comment.reader
;                                      ^^^^^^ comment.reader
;                                            ^ - comment
;                                             ^^ punctuation.definition.comment.reader
;                                             ^^^^^ comment.reader
;                                                  ^ - comment

  #_[a [b c]] #_[] #_[[]] [#_abc] [[#_abc]] [[#_abc] []] [#_[abc]] [#_[abc[def]] []]
; ^^^^^^^^^^^ comment.reader
;            ^ - comment
;             ^^^^ comment.reader
;                 ^ - comment
;                  ^^^^^^ comment.reader
;                        ^^ - comment
;                          ^^^^^ comment.reader
;                               ^^^^ - comment
;                                   ^^^^^ comment.reader
;                                        ^^^^^ - comment
;                                             ^^^^^ comment.reader
;                                                  ^^^^^^^ - comment
;                                                         ^^^^^^^ comment.reader
;                                                                ^^^ - comment
;                                                                   ^^^^^^^^^^^^ comment.reader
;                                                                               ^^^^ - comment

  #_(a (b c)) #_() #_(()) (#_abc) ((#_abc)) ((#_abc) ()) (#_(abc)) (#_(abc(def)) ())
; ^^^^^^^^^^^ comment.reader
;            ^ - comment
;             ^^^^ comment.reader
;                 ^ - comment
;                  ^^^^^^ comment.reader
;                        ^^ - comment
;                          ^^^^^ comment.reader
;                               ^^^^ - comment
;                                   ^^^^^ comment.reader
;                                        ^^^^^ - comment
;                                             ^^^^^ comment.reader
;                                                  ^^^^^^^ - comment
;                                                         ^^^^^^^ comment.reader
;                                                                ^^^ - comment
;                                                                   ^^^^^^^^^^^^ comment.reader
;                                                                               ^^^^ - comment

  #_{a {b c}} #_{} #_{{}} {#_abc} {{#_abc}} {{#_abc} {}} {#_{abc}} {#_{abc{def}} {}}
; ^^^^^^^^^^^ comment.reader
;            ^ - comment
;             ^^^^ comment.reader
;                 ^ - comment
;                  ^^^^^^ comment.reader
;                        ^^ - comment
;                          ^^^^^ comment.reader
;                               ^^^^ - comment
;                                   ^^^^^ comment.reader
;                                        ^^^^^ - comment
;                                             ^^^^^ comment.reader
;                                                  ^^^^^^^ - comment
;                                                         ^^^^^^^ comment.reader
;                                                                ^^^ - comment
;                                                                   ^^^^^^^^^^^^ comment.reader
;                                                                               ^^^^ - comment

; touching forms
  #_[abc]def #_abc[def] #_[abc][def]
; ^^^^^^^ comment.reader
;        ^^^^ - comment
;            ^^^^^ comment.reader
;                 ^^^^^^ - comment
;                       ^^^^^^^ comment.reader
;                              ^^^^^ - comment

; whitespace
  #_ abc def #_,abc def
; ^^^^^^ comment.reader
;       ^^^^^ - comment
;            ^^^^^^ comment.reader
;                  ^^^^ - comment

; double reader comment
  #_#_abc def ghi
; ^^^^^^^^^^^ comment.reader
;            ^^^^ - comment

  #_#_abc #_def ghi jkl
; ^^^^^^^^^^^^^^^^^ comment.reader
;                  ^^^^ - comment

  #_#_#_#_#_#_#_a b c d e f g h i j k
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^ comment.reader
;                            ^^^^^^^^ - comment

  #_#_[abc][def][ghi]
; ^^^^^^^^^^^^^^ comment.reader
;               ^^^^^ - comment

  #_#_[abc]#_[def][ghi][jkl]
; ^^^^^^^^^^^^^^^^^^^^^ comment.reader
;                      ^^^^^ - comment

; multiline

  #_
; ^^ comment.reader
  a
; ^ comment.reader
  b
; ^ - comment

  #_#_
; ^^^^ comment.reader
  a
; ^ comment.reader
  #_b
; ^^^ comment.reader
  c
; ^ comment.reader
  d
; ^ - comment

  #_[
; ^^^ comment.reader
  abc
; ^^^ comment.reader
  ] def
; ^ comment.reader
;  ^^^^ - comment
  ghi
; ^^^ - comment

  (((#_x)))
;   ^^^^^ meta.parens meta.parens meta.parens
;    ^^^ comment.reader

;;;;;;;;;; SYMBOLS ;;;;;;;;;;

  a abc абв
; ^ source.symbol
;  ^ -source.symbol
;   ^^^ source.symbol
;       ^^^ source.symbol
  . * + ! - _ ? $ % & = < > /
; ^ source.symbol
;   ^ source.symbol
;     ^ source.symbol
;       ^ source.symbol
;         ^ source.symbol
;           ^ source.symbol
;             ^ source.symbol
;               ^ source.symbol
;                 ^ source.symbol
;                   ^ source.symbol
;                     ^ source.symbol
;                       ^ source.symbol
;                         ^ source.symbol
;                           ^ source.symbol
  a1 a: a# a' -a +a .a k::v
; ^^ source.symbol
;    ^^ source.symbol
;       ^^ source.symbol
;          ^^ source.symbol
;             ^^ source.symbol
;                ^^ source.symbol
;                   ^^ source.symbol
;                      ^^^^ source.symbol
  a/b a1/b2 абв/где abc.def/uvw.xyz clojure.core//
; ^^^ source.symbol
; ^ meta.namespace.symbol
;  ^  punctuation.definition.namespace
;     ^^^^^ source.symbol
;     ^^ meta.namespace.symbol
;       ^ punctuation.definition.namespace
;           ^^^^^^^ source.symbol
;           ^^^ meta.namespace.symbol
;              ^ punctuation.definition.namespace
;                   ^^^^^^^^^^^^^^^ source.symbol
;                   ^^^^^^^ meta.namespace.symbol
;                          ^ punctuation.definition.namespace
;                                   ^^^^^^^^^^^^^^ source.symbol
;                                   ^^^^^^^^^^^^ meta.namespace.symbol
;                                               ^ punctuation.definition.namespace
  _ _a _abc x/_a
; ^ source.symbol.unused
;   ^^ source.symbol.unused
;      ^^^^ source.symbol.unused
;           ^^^^ source.symbol.unused

; NOT SYMBOLS
  a/ /b 1a -1a +1a .1a
; ^^^^^^^^^^^^^^^^^^^^ -source.symbol


;;;;;;;;;; KEYWORDS ;;;;;;;;;;

  :a :abc :абв
; ^^ constant.other.keyword
; ^  punctuation.definition.keyword.begin
;  ^ -punctuation.definition.keyword.begin
;   ^ -constant.other.keyword
;    ^^^^ constant.other.keyword
;         ^^^^ constant.other.keyword
  :. :* :+ :! :- :_ :? :$ :% :& := :< :> :# :1 :' :a: :k::v
; ^^ constant.other.keyword
;    ^^ constant.other.keyword
;       ^^ constant.other.keyword
;          ^^ constant.other.keyword
;             ^^ constant.other.keyword
;                ^^ constant.other.keyword
;                   ^^ constant.other.keyword
;                      ^^ constant.other.keyword
;                         ^^ constant.other.keyword
;                            ^^ constant.other.keyword
;                               ^^ constant.other.keyword
;                                  ^^ constant.other.keyword
;                                     ^^ constant.other.keyword
;                                        ^^ constant.other.keyword
;                                           ^^ constant.other.keyword
;                                              ^^ constant.other.keyword
;                                                 ^^^ constant.other.keyword
;                                                     ^^^^^ constant.other.keyword
  :a/b :1/2 :абв/где :abc.def/uvw.xyz
; ^^^^ constant.other.keyword
; ^    punctuation.definition.keyword.begin
;  ^ meta.namespace.keyword
;   ^  punctuation.definition.namespace
;     ^ -constant.other.keyword
;      ^^^^ constant.other.keyword
;       ^ meta.namespace.keyword
;        ^ punctuation.definition.namespace
;           ^^^^^^^^ constant.other.keyword
;            ^^^ meta.namespace.keyword
;               ^ punctuation.definition.namespace
;                    ^^^^^^^^^^^^^^^^ constant.other.keyword
;                     ^^^^^^^ meta.namespace.keyword
;                            ^ punctuation.definition.namespace
  ::kv ::k/v
; ^^^^ constant.other.keyword
; ^^ punctuation.definition.keyword.begin
;      ^^^^^ constant.other.keyword
;      ^^ punctuation.definition.keyword.begin
;        ^ meta.namespace.keyword
;         ^ punctuation.definition.namespace

;; NOT KEYWORDS
  :kv/ :/kv :/ :k/:v :k/v/v :::kv 
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ -constant.other.keyword


;;;;;;;;;; INTEGERS ;;;;;;;;;;

  0 1 23 1234567890 -0 +0 0N
; ^ constant.numeric.integer
;  ^ -constant.numeric.integer
;   ^ constant.numeric.integer
;     ^^ constant.numeric.integer
;        ^^^^^^^^^^ constant.numeric.integer
;                   ^^ constant.numeric.integer
;                      ^^ constant.numeric.integer
;                         ^^ constant.numeric.integer
;                          ^ punctuation.definition.integer.precision
  0123 -0123
; ^^^^ constant.numeric.integer
;      ^^^^^ constant.numeric.integer
  0x0123 -0x123 0XFF
; ^^^^^^ constant.numeric.integer
;        ^^^^^^ constant.numeric.integer
;               ^^^^ constant.numeric.integer
  36r0123abyz -32R0123ABYZ
; ^^^^^^^^^^^ constant.numeric.integer
;             ^^^^^^^^^^^^ constant.numeric.integer

;; NOT INTEGERS
  09 1n ++1 --1 +N -N
; ^^^^^^^^^^^^^^^^^^^ -constant.numeric.integer


;;;;;;;;;; FLOATS ;;;;;;;;;;
  0.0 0.000 999.999 1. 0e1 2e+3 4e-5 67E89 1.2e3 444.555E+666 1.e3
; ^^^ constant.numeric.float
;    ^ -constant.numeric.float
;     ^^^^^ constant.numeric.float
;           ^^^^^^^ constant.numeric.float
;                   ^^ constant.numeric.float
;                      ^^^ constant.numeric.float
;                          ^^^^ constant.numeric.float
;                               ^^^^ constant.numeric.float
;                                    ^^^^^ constant.numeric.float
;                                          ^^^^^ constant.numeric.float
;                                                ^^^^^^^^^^^^ constant.numeric.float
;                                                             ^^^^ constant.numeric.float
  0M 123M 4.M 5e6M 7.8e9M -3.14 +2e19M
; ^^ constant.numeric.float
;  ^ punctuation.definition.float.precision
;    ^^^^ constant.numeric.float
;       ^ punctuation.definition.float.precision
;         ^^^ constant.numeric.float
;           ^ punctuation.definition.float.precision
;             ^^^^ constant.numeric.float
;                ^ punctuation.definition.float.precision
;                  ^^^^^^ constant.numeric.float
;                       ^ punctuation.definition.float.precision
;                         ^^^^^ constant.numeric.float
;                               ^^^^^^ constant.numeric.float
;                                    ^ punctuation.definition.float.precision
  ##Inf ##-Inf ##NaN
; ^^^^^ constant.numeric.float
;       ^^^^^^ constant.numeric.float
;              ^^^^^ constant.numeric.float

;; NOT FLOATS
  00.0 1e2.3 1e 1.0e --1.0 ++1.0 +M -M 1m ###Inf ##inf ##+Inf
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ -constant.numeric.float


;;;;;;;;;; RATIOS ;;;;;;;;;;

  1/2 0/2 999/999 +1/2 -1/2
; ^^^ constant.numeric.ratio
;    ^ -constant.numeric.ratio
;     ^^^ constant.numeric.ratio
;         ^^^^^^^ constant.numeric.ratio
;                 ^^^^ constant.numeric.ratio
;                      ^^^^ constant.numeric.ratio

;; NOT RATIOS
  1/0 00/2 0/01 ++0/2 --0/2
; ^^^^^^^^^^^^^^^^^^^^^^^^^ -constant.numeric.ratio


;;;;;;;;;; TAGS ;;;;;;;;;;

  #inst "1985-01-25" 
; ^^^^^^^^^^^^^^^^^^ constant.other.instant
;                   ^ -constant.other.instant
  #inst"2018-03-28T10:48:00.000"
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ constant.other.instant
  #inst   "2018-03-28T10:48:00.000Z"
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ constant.other.instant
  #inst "2018-03-28T10:48:00.000+01:30"
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ constant.other.instant
  #inst "2018-12-31T23:59:60.999999999-23:59"
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ constant.other.instant
  #uuid "c5634984-363d-4727-B8CE-b06ab1253c81"
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ constant.other.uuid
  #datascript/DB {:schema {}, :datoms {}}
; ^^^^^^^^^^^^^^ storage.type.tag
;; NOT TAGS
  #inst "1985-"
; ^^^^^^^^^^^^^ constant.other.instant & invalid.illegal.instant
  #inst "1985-20"
; ^^^^^^^^^^^^^^^ constant.other.instant & invalid.illegal.instant
  #inst "1985-12-40"
; ^^^^^^^^^^^^^^^^^^ constant.other.instant & invalid.illegal.instant
  #inst "1985-12-31T30"
; ^^^^^^^^^^^^^^^^^^^^^ constant.other.instant & invalid.illegal.instant
  #inst "1985-12-31T23:60"
; ^^^^^^^^^^^^^^^^^^^^^^^^ constant.other.instant & invalid.illegal.instant
  #inst "1985-12-31T23:59:70"
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^ constant.other.instant & invalid.illegal.instant
  #inst "1985-12-31T23:59:60.999+30:00"
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ constant.other.instant & invalid.illegal.instant
  #inst "1985-12-31T23:59:60.999+12:60"
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ constant.other.instant & invalid.illegal.instant
  #uuid "abc"
; ^^^^^^^^^^^ constant.other.uuid & invalid.illegal.uuid
  #uuid "g5634984-363d-4727-b8ce-b06ab1253c81"
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ constant.other.uuid & invalid.illegal.uuid
  #123 #a/ #_tag #{} ##Inf
; ^^^^^^^^^^^^^^^^^^^^^^^^ -storage.type.tag


;;;;;;;;;; PUNCTUATION ;;;;;;;;;;

  , 
; ^ punctuation.definition.comma
;  ^ -punctuation
  " "
; ^ punctuation.definition.string.begin
;  ^ -punctuation
;   ^ punctuation.definition.string.end
  ( )
; ^^^ meta.parens
; ^ punctuation.section.parens.begin
;   ^ punctuation.section.parens.end
  [ ]
; ^^^ meta.brackets
; ^ punctuation.section.brackets.begin
;   ^ punctuation.section.brackets.end
  { }
; ^^^ meta.braces
; ^ punctuation.section.braces.begin
;   ^ punctuation.section.braces.end
  #{ }
; ^^^^ meta.braces
; ^^ punctuation.section.braces.begin
;    ^ punctuation.section.braces.end
  ; ...
; ^ punctuation.definition.comment.line
;  ^ -punctuation


;;;;;;;;;; BALANCING ;;;;;;;;;;

  []]
; ^^ -invalid.illegal.stray-bracket-end
;   ^ invalid.illegal.stray-bracket-end
  {}}}
; ^^ -invalid.illegal.stray-bracket-end
;   ^^ invalid.illegal.stray-bracket-end
  ())))
; ^^ -invalid.illegal.stray-bracket-end
;   ^^^ invalid.illegal.stray-bracket-end
  ([)]))   {[(}])]}   #{{)]}}}
;   ^    invalid.illegal.stray-bracket-end
;      ^ invalid.illegal.stray-bracket-end
;             ^^ invalid.illegal.stray-bracket-end
;                        ^^ invalid.illegal.stray-bracket-end
;                            ^ invalid.illegal.stray-bracket-end
  {(["abc])}"])}
; ^^^^^^^^^^^^^^ -invalid.illegal.stray-bracket-end
  {[()]} ;; )]}
; ^^^^^^^^^^^^^ -invalid.illegal.stray-bracket-end


;;;;;;;;;; VAR QUOTE ;;;;;;;;;;

  #'map
; ^^ punctuation.definition.var
  #' ,,, map
; ^^ punctuation.definition.var
  (((#'map)))
;   ^^^^^^^ meta.parens meta.parens meta.parens
;    ^^ punctuation.definition.var


;;;;;;;;;; DEREF ;;;;;;;;;;

  @*atom
; ^ keyword.operator.deref
  @ , *atom
; ^ keyword.operator.deref
;  ^^^^^^^^ - keyword.operator.deref
;   ^ punctuation.definition.comma
  (((@map)))
;   ^^^^^^ meta.parens meta.parens meta.parens
;    ^ keyword.operator.deref


;;;;;;;;;; READER CONDITIONALS ;;;;;;;;;;
  #?(:clj 1 :cljs 2)
; ^^^^^^^^^^^^^^^^^^ meta.parens meta.reader_conditional
; ^^^ punctuation.section.parens.begin
; ^^ punctuation.definition.reader_conditional
;                  ^ punctuation.section.parens.end
;                   ^ - punctuation - meta.section
  #?@(:clj [3 4] :cljs [5 6])
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.parens meta.reader_conditional
; ^^^ punctuation.definition.reader_conditional
; ^^^^ punctuation.section.parens.begin
;                           ^ punctuation.section.parens.end
;                            ^ - punctuation - meta.section
  [[#?(:clj 1 :cljs 2)]]
;   ^^^^^^^^^^^^^^^^^^ meta.parens meta.reader_conditional
  #? [123]
; ^^^^^^^^ - meta.reader_conditional


;;;;;;;;;; QUOTE ;;;;;;;;;;

  '[datascript :as ds] []
; ^ keyword.operator.quote
; ^^^^^^^^^^^^^^^^^^^^ meta.quoted
;                     ^^^ -meta.quoted
  'datascript.core []
; ^ keyword.operator.quote
; ^^^^^^^^^^^^^^^^ meta.quoted
;                 ^^^ -meta.quoted
  'datascript.core[]
; ^^^^^^^^^^^^^^^^ meta.quoted
;                 ^^ -meta.quoted
  ' , datascript.core []
; ^ keyword.operator.quote
; ^^^^^^^^^^^^^^^^^^^ meta.quoted
;  ^^^^^^^^^^^^^^^^^^^^^ - keyword.operator
;   ^ punctuation.definition.comma
;                    ^^^ - meta.quoted
  'x()
; ^^ meta.quoted
;   ^^ - meta.quoted
  '()x
; ^^^ meta.quoted
;    ^ - meta.quoted
  '()()
; ^^^ meta.quoted
;    ^^ - meta.quoted
  '
; ^ meta.quoted
  x y z
; ^ meta.quoted
;  ^^^^ - meta.quoted
  ''x y z
; ^^^ meta.quoted
;    ^^^^ - meta.quoted
  ''()()()
; ^^^^ meta.quoted
;     ^^^^ - meta.quoted
  (('x))
;  ^^^^ meta.parens meta.parens
;   ^^ meta.quoted
;     ^^ - meta.quoted
  (((''x y z)))
; ^^^^^^^^^^^^^ meta.parens
;  ^^^^^^^^^^^ meta.parens meta.parens
;   ^^^^^^^^^ meta.parens meta.parens meta.parens
;    ^^^ meta.quoted
;       ^^^^^^^ - meta.quoted


;;;;;;;;;; SYNTAX QUOTE, UNQUOTE, UNQUOTE SPLICING ;;;;;;;;;;

  ((`x))
;  ^^^^ meta.parens meta.parens
;   ^^ meta.quoted.syntax
;     ^^ - meta.quoted.syntax

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


;;;;;;;;;; METADATA ;;;;;;;;;;

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
; ^^^^ meta.metadata
;     ^^^^ - meta.metadata
;         ^^^^^^^^^^^^^^^^ meta.metadata
;                         ^^ - meta.metadata
  ^x()
; ^^ meta.metadata
;   ^^ - meta.metadata
  ^()x
; ^^^ meta.metadata
;    ^ - meta.metadata
  ^()()
; ^^^ meta.metadata
;    ^^ - meta.metadata
  ^
; ^ meta.metadata
  x y z
; ^ meta.metadata
;  ^^^^ - meta.metadata
  (((^x y)))
;   ^^^^^^ meta.parens meta.parens meta.parens
;    ^^ meta.metadata
;      ^^ - meta.metadata


;;;;;;;;;; REGEXPS ;;;;;;;;;;
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


;;;;;;;;;; DEFINITIONS ;;;;;;;;;;

  (defn fname [arg arg2] body)
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.parens
;                             ^ -meta.parens
;  ^^^^ source.symbol.def
;       ^^^^^ source.symbol entity.name 
; ^ punctuation.section.parens.begin
;  ^^^^ source.symbol.def
;                            ^ punctuation.section.parens.end

;; EVERYTHING

  (defn- ^{:meta :map} fn "doc" {:attr :map} [args] {:pre ()} body) 
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.parens
;                                                                  ^ - meta.parens
;  ^^^^^ source.symbol.def
;        ^^^^^^^^^^^^^ meta.metadata
;                      ^^ source.symbol entity.name

;; INCOMPLETE FNS ARE STILL CLOSED

  (defn)
; ^^^^^^ meta.parens
;  ^^^^ source.symbol.def
;       ^ -meta.parens
  (defn f)
; ^^^^^^^^ meta.parens
;  ^^^^ source.symbol.def
;         ^ -meta.parens
;       ^ source.symbol entity.name
  (defn
; ^^^^^ meta.parens
;  ^^^^ source.symbol.def
    f)
;   ^^ meta.parens
;   ^ source.symbol entity.name
  ( , , defn f) 
; ^^^^^^^^^^^^^ meta.parens
;       ^^^^ source.symbol.def
;              ^ -meta.parens
;            ^ source.symbol entity.name
  ( , #_smth
; ^^^^^^^^^^ meta.parens
    def
;   ^^^ meta.parens source.symbol.def
    , #_smth
;   ^^^^^^^^ meta.parens
    sym)
;   ^^^^ meta.parens
;   ^^^ source.symbol entity.name

; ENTITY.NAME MUST BE SECOND

  (def #_comment fun boom)
;  ^^^ source.symbol.def
;                ^^^ source.symbol entity.name
;                   ^^^^^^ - entity.name
  (def ^{:doc "abc"} fun boom)
;  ^^^ source.symbol.def
;                    ^^^ source.symbol entity.name
;                       ^^^^^^ - entity.name
  (def ^longs fun boom)
;  ^^^ source.symbol.def
;             ^^^ source.symbol entity.name
;                ^^^^^^ - entity.name
  (def 15 fun)
;  ^^^ source.symbol.def
;         ^^^ - entity.name
  (def "str" fun)
;  ^^^ source.symbol.def
;            ^^^ - entity.name
  (def {a b} fun)
;  ^^^ source.symbol.def
;            ^^^ - entity.name
  (defn 15 "str" {a b} fname 15 sym \n ("abc") [])
;  ^^^^ source.symbol.def
;                      ^^^^^ - entity.name
  (def x 1)
; ^^^^^^^^^ meta.parens
;  ^^^ source.symbol
;      ^ entity.name
  (defmethod x 1)
; ^^^^^^^^^^^^^^^ meta.parens
;  ^^^^^^^^^ source.symbol
;            ^ entity.name
  (rum/defcs x 1)
; ^^^^^^^^^^^^^^^ meta.parens
; ^ punctuation.section.parens.begin
;  ^^^^^^^^^ source.symbol
;  ^^^ meta.namespace.symbol
;     ^ punctuation.definition.namespace
;            ^ entity.name
;               ^ punctuation.section.parens.end
  (defmethod clojure.test/report :error [m])
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.parens
; ^ punctuation.section.parens.begin
;            ^^^^^^^^^^^^^^^^^^^ entity.name
;            ^^^^^^^^^^^^ meta.namespace.symbol
;                        ^ punctuation.definition.namespace
;                                          ^ punctuation.section.parens.end
  #?(:clj (def x 1))
;         ^^^^^^^^^ meta.parens
;              ^ entity.name
;         ^ punctuation.section.parens.begin
;                 ^ punctuation.section.parens.end


;;;;;;;;;; ANONYMOUS FN ;;;;;;;;;;
  #(+ %1 %2)
; ^^^^^^^^^^ meta.function & meta.parens
; ^ punctuation.definition.anon_fn
;  ^ punctuation.section.parens.begin
;           ^^ - meta.function
;          ^ punctuation.section.parens.end


;;;;;;;;;; FORM COMMENT ;;;;;;;;;;
  ()
; ^^ - comment
  (comment 123)
; ^^^^^^^^^^^^^ comment.form
  (comment
; ^^^^^^^^ comment.form
    123)
; ^^^^^^ comment.form
  ( , , , #_skip 
; ^^^^^^^ comment.form
   comment
; ^^^^^^^^ comment.form
    123)
; ^^^^^^ comment.form
  (not comment)
; ^^^^^^^^^^^^^ - comment
  (nested (comment smth))
; ^^^^^^^^ - comment
;         ^^^^^^^^^^^^^^ comment.form
;                       ^ - comment


;;;;;;;;;; META + QUOTED + COMMENT ;;;;;;;;;;

;;;;; Quoted inside meta
  ^'x y z
; ^^^ meta.metadata
;  ^^ meta.quoted
;    ^^^^ - meta.metadata - meta.quoted
  (((^'x y z)))
; ^^^^^^^^^^^^^ meta.parens
;  ^^^^^^^^^^^ meta.parens
;   ^^^^^^^^^ meta.parens
;    ^^^ meta.metadata
;     ^^ meta.quoted
;       ^^^^^^^ - meta.metadata - meta.quoted

;;;;; Meta inside quoted
  '^x y z
; ^^^^^ meta.quoted
;  ^^ meta.metadata
;    ^^ - meta.metadata
;      ^^ - meta.quoted
  ((('^x y z)))
; ^^^^^^^^^^^^^ meta.parens
;  ^^^^^^^^^^^ meta.parens
;   ^^^^^^^^^ meta.parens
;    ^^^^^ meta.quoted
;     ^^ meta.metadata
;       ^^^^^^^ - meta.metadata
;         ^^^^^ - meta.quoted

;;;;; Comment inside meta
  ^#_x y z
; ^^^^^^ meta.metadata
;  ^^^ comment
;       ^^ - meta.metadata - comment

;;;;; Comment inside quoted
  '#_x y z
; ^^^^^^ meta.quoted
;  ^^^ comment
;       ^^ - meta.metadata - comment

;;;;; Commented meta
  #_^x y z
; ^^^^^^ comment
;   ^^ meta.metadata
;       ^^ - comment - meta.metadata

;;;;; Commented quote
  #_'x y z
; ^^^^ comment
;   ^^ meta.quoted
;     ^^^^ - meta.quoted - comment
