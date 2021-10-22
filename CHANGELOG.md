### October 22, 2021

- Renamed syntaxes to `Clojure (Sublime Clojure)` and `EDN (Sublime Clojure)`

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
