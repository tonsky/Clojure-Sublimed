# Better EDN syntax for SublimeText 3

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

### Dec 24, 2018

- Instants, uuids, custom reader tags;
- punctuation class for colons and slashes in symbols/keywords, comma, backslash in strings/chars;
- allow single quote in keywords;
- more [conventional](https://macromates.com/manual/en/language_grammars) class names;
- automated tests.

### Dec 23, 2018

- Inital version.