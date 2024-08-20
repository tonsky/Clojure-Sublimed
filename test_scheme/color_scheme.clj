
; Constants
nil true false \c \tab 1 1.0 1/2 :a :a.b/c.d #inst "1985-01-25"

; Symbols
abc ab/cd _abc

; Strings
"" "abc" "\" \u221e \x"

; Regexps
#"re \n \uFFFF \p{L} \Qabc\E) \y"

; Top-level parens
() [] {} #() #{} #?() #?@() 

; Nested parens
(() [] {} #() #{} #?() #?@())
[() [] {} #() #{} #?() #?@()]
{() [] {} #() #{} #?() #?@()}
#{() [] {} #() #{} #?() #?@()}
#(() [] {} #() #{} #?() #?@())
([{}])
(((((((((()))))))))) [[[[[[[[[[]]]]]]]]]] {{{{{{{{{{}}}}}}}}}}

; Definitions
(def xyz)
(def xyz xyz)
(def xyz 123)
(def 123 xyz)
(def
  xyz)
(do (def xyz))

; Punctuation
,

; Meta
^{:s  sym
  :v  "str\n"
  :n  123
  :re #"\p{L}) \y"
  :l  ([{}])
  :q  '(abc)
  :sq `(abc ~def)
  :m  ^int i
  :d  @ref
  :v  #'var
  :c  #?(:clj)
  :df (def x 1)
  ; linecomment
  #_#_reader comment
  (comment form))))} sym

; Quotes
'{:symbol  name/space
  :string  "str\n\x"
  :regexp  #"\p{L}) \y"
  :number  123.456
  :keyword :key/word
  :parens  (() #() #?(:clj :cljs) [] {} #{})
  :quoted  ('abc `(x ~y))
  :meta    ^int i
  :vars    [@ref #'var]
  :defs    (def x 1)
  ; linecomment
  #_#_reader comment
  (comment form))))}

; Syntax quotes
`{:symbol  name/space
  :string  "str\n\x"
  :regexp  #"\p{L}) \y"
  :number  123.456
  :keyword :key/word
  :parens  (() #() #?(:clj :cljs) [] {} #{})
  :quoted  ('abc `(x ~y))
  :meta    ^int i
  :vars    [@ref #'var]
  :defs    (def x 1)
  ; linecomment
  #_#_reader comment
  (comment form))))}

`{:symbol  name/space
  :string  "str\n\x"
  :regexp  #"\p{L}) \y"
  :number  123.456
  :keyword :key/word
  :parens  (() #() #?(:clj :cljs) [] {} #{})
  :quoted  ('abc `(x ~y))
  :meta    ^int i
  :vars    [@ref #'var]
  :defs    (def x 1)
  ; linecomment
  #_#_reader comment
  (comment form))))}

`~{:symbol  name/space
   :string  "str\n\x"
   :regexp  #"\p{L}) \y"
   :number  123.456
   :keyword :key/word
   :parens  (() #() #?(:clj :cljs) [] {} #{})
   :quoted  ('abc `(x ~y))
   :meta    ^int i
   :vars    [@ref #'var]
   :defs    (def x 1)
   ; linecomment
   #_#_reader comment
   (comment form))))}

; Line comments
; {:symbol  name/space
;  :string  "str\n\x"
;  :regexp  #"\p{L}) \y"
;  :number  123.456
;  :keyword :key/word
;  :parens  (() #() #?(:clj :cljs) [] {} #{})
;  :quoted  ('abc `(x ~y))
;  :meta    ^int i
;  :vars    [@ref #'var]
;  :defs    (def x 1)
;  ; linecomment
;  #_#_reader comment
;  (comment form))))}

; Reader comments
#_{:symbol  name/space
   :string  "str\n\x"
   :regexp  #"\p{L}) \y"
   :number  123.456
   :keyword :key/word
   :parens  (() #() #?(:clj :cljs) [] {} #{})
   :quoted  ('abc `(x ~y))
   :meta    ^int i
   :vars    [@ref #'var]
   :defs    (def x 1)
   ; linecomment
   #_#_reader comment
   (comment form))))}

; Form comments
(comment
  {:symbol  name/space
   :string  "str\n\x"
   :regexp  #"\p{L}) \y"
   :number  123.456
   :keyword :key/word
   :parens  (() #() #?(:clj :cljs) [] {} #{})
   :quoted  ('abc `(x ~y))
   :meta    ^int i
   :vars    [@ref #'var]
   :defs    (def x 1)
   ; linecomment
   #_#_reader comment
   (comment form))))})
