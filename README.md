# Better EDN syntax for SublimeText 3

## Why another syntax?

All existing Clojure syntaxes for TextMate, Atom, VS Code and SublimeText get many things right, but annoyingly leave tons of edge cases (and sometimes later additions) out. Some examples:

```clojure
a'    ;; is a valid symbol
/     ;; also a valid symbol
:1    ;; is a valid keyword
:a:b  ;; also a valid keyword
\o377 ;; a valid character
100N  ;; bigint 
01/2  ;; invalid ratio
#datascript/DB {} ;; custom reader tag with a namespace
```

Want to put your parser to test? Check out [syntax_specimen_edn.edn](./syntax_specimen_edn.edn).

Sublime Text 3 also extended syntax definitions with stacks. With stacks it’s now possible to correctly highlight unbalanced brackets efficiently.

Third reason is that EDN is a limited subset of Clojure. Many things allowed in Clojure are not allowed in EDN (anonymous functions, metadata, double-colon keywords, namespaced maps, derefs, quotes etc). So I decided EDN deserves its own grammar, same way JSON is separate from JavaScript in ST.

## Highlights

- Pedantic as per [EDN spec](https://github.com/edn-format/edn).
- Strings, escape sequences, characters, comments, symbols, keywords, integers, floats, ratios, constants, instants, uuids and custom reader tags.
- Highlights unbalanced brackets and incorrect escape sequences.
- Unicode-friendly (supports unicode letters in symbols/keywords).

## Installation

```
git clone https://github.com/tonsky/sublime-clojure.git
ln -s `pwd`/sublime-clojure ~/Library/Application Support/Sublime Text 3/Packages/
```

## Testing

### Automated

Open `syntax_test_edn.edn` and run `Build`.

### Manual

Open `syntax_specimen_edn.edn` and see if it highlights everything it should and doesn’t highlight anything it shouldn’t.

## License

[MIT License](./LICENSE.txt)

## CHANGES

### Dec 30, 2018

- Supported namespaced `/` symbol.
- Tokens can end directly with `;`, without any whitespace in between.
- Content of `()[]{}` is marked with `meta.brackets.inner`, making possible different highlight for top-level and nested brackets.
- All bracket/paren/braces classes replaces with single `punctuation.brackets.begin`/`...end`.
- Beginning of Clojure syntax, highlighting `entity.name` in all `def*`/`ns` forms.

### Dec 24, 2018

- Instants, uuids, custom reader tags;
- punctuation class for colons and slashes in symbols/keywords, comma, backslash in strings/chars;
- allow single quote in keywords;
- more [conventional](https://macromates.com/manual/en/language_grammars) class names;
- automated tests.

### Dec 23, 2018

- Inital version.