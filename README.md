# Better Clojure and EDN syntaxes for SublimeText 3

## Why another syntax?

All existing Clojure syntaxes for TextMate, Atom, VS Code and SublimeText get many things right, but annoyingly leave tons of edge cases (and sometimes later additions) out. Some examples:

```clojure
a'    ;; is a valid symbol
/     ;; also a valid symbol
:1    ;; is a valid keyword
:a:b  ;; also a valid keyword
:абв  ;; unicode keyword
\o377 ;; a valid character
100N  ;; bigint 
01/2  ;; invalid ratio
#datascript/DB {}   ;; custom reader tag with a namespace
^:kw ^"String" sym  ;; more than one metadata, non-map metadata
(rum/defc label []) ;; custom def form with a namespace
@ , *atom           ;; a space and a comma between deref and a symbol
```

<img src="https://s.tonsky.me/imgs/sublime_clojure.png">

Want to put your parser to test? Check out [syntax_test_edn.edn](./syntax_test_edn.edn) and [syntax_test_clojure.cljc](./syntax_test_clojure.cljc).

Sublime Text 3 also extended syntax definitions with stacks. It’s now possible to highlight unbalanced brackets efficiently.

Third reason is that EDN is a limited subset of Clojure. Many things allowed in Clojure are not allowed in EDN (anonymous functions, metadata, double-colon keywords, namespaced maps, derefs, quotes etc). So I decided EDN deserves its own grammar, same way JSON is separate from JavaScript in ST.

## Highlights

- Pedantic as per [EDN spec](https://github.com/edn-format/edn) and [Clojure Reader](https://clojure.org/reference/reader).
- Rigorously tested.
- Detects unbalanced brackets and incorrect escape sequences.
- Punctuation and validation _inside_ regexps. 
- Quoted and unquoted regions are marked for highlighting.
- Semantically correct tokenization, perfect for fonts with ligatures.
- Unicode-friendly (supports unicode letters in symbols/keywords).
- EDN: Strings, escape sequences, characters, comments, symbols, keywords, integers, floats, ratios, constants, instants, uuids and custom reader tags.
- Clojure: EDN + regular expressions, custom def forms, reader conditionals, quotes and syntax quotes, metadata.

## Installation

```
git clone https://github.com/tonsky/sublime-clojure.git
ln -s `pwd`/sublime-clojure ~/Library/Application Support/Sublime Text 3/Packages/
```

## Testing

Open `syntax_test_edn.edn` or `syntax_test_clojure.cljc` and run `Build`.

## License

[MIT License](./LICENSE.txt)

## CHANGES

### Jan 3, 2019

- Clojure syntax: quotes, reader conditionals, operators, better whitespace handling.

### Jan 1, 2019

- Clojure syntax: regexps.

### Dec 30, 2018

- Supported namespaced `/` symbol.
- Tokens can end directly with `;`, without any whitespace in between.
- Content of `()[]{}` is marked with `meta.parens`/`.brackets`/`.braces`, making possible nested brackets highlighting.
- Bracket/paren/braces classes replaced with `punctuation.section.(parens|brackets|braces).begin`/`...end`.
- Keywords use `constant.other.keyword` instead of `constant.keyword`.
- Beginning of Clojure syntax, highlighting `entity.name` in all `def*`/`ns` forms.

### Dec 24, 2018

- Instants, uuids, custom reader tags;
- punctuation class for colons and slashes in symbols/keywords, comma, backslash in strings/chars;
- allow single quote in keywords;
- more [conventional](https://macromates.com/manual/en/language_grammars) class names;
- automated tests.

### Dec 23, 2018

- Inital version.