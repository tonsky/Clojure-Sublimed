
; Constants
nil true false \c \newline 123 1.23 10/20 :abc :abc.def/uvw.xyz #inst "1985-01-25"

; Symbols
abc ab/cd

; Strings
"" "abc" "\" \u221e"

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
; Quotes
; Syntax quotes
; Reader comments
; Form comments
