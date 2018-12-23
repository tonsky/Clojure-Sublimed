# Better EDN syntax for SublimeText 3

- Pedantic as per [EDN spec](https://github.com/edn-format/edn).
- Strings, escape sequences, characters, comments, symbols, keywords, integers, floats, ratios, constants.
- Highlights unbalanced brackets and incorrect escape sequences.
- Unicode-friendly (supports unicode letters in symbols/keywords).

## Installation

Copy `EDN.sublime-syntax` to `~/Library/Application Support/Sublime Text 3/Packages`

## Testing

Try opening `syntax_test_edn.edn` and see if it highlights everything it should and doesn’t highlight anything it shouldn’t.

## License

[MIT License](./LICENSE.txt)