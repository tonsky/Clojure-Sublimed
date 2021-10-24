# Clojure support for Sublime Text 4

<div align=center><img src="./screenshots/logo.png" width="350"></div>

This package provides Clojure support for Sublime Text and includes:

- Clojure and EDN syntax grammars (Sublime Text 3 or later)
- Clojure nREPL client (version 4075 or later)

## Clojure syntax

Unfortunately, Clojure syntax that is shipped with Sublime Text handles many edge cases badly:

<img src="https://raw.github.com/tonsky/sublime-clojure/master/screenshots/syntaxes.png" width="806" height="299" alt="Syntaxes">

Unlike default Clojure syntax, this package is:

- pedantic as per [EDN spec](https://github.com/edn-format/edn) and [Clojure Reader](https://clojure.org/reference/reader),
- rigorously tested,
- detects unbalanced brackets and incorrect escape sequences efficiently,
- punctuation and validation _inside_ regexps.,
- quoted and unquoted regions are marked for highlighting,
- semantically correct tokenization, perfect for fonts with ligatures,
- unicode-friendly (supports unicode letters in symbols/keywords),
- has separate EDN syntax, same way JSON is separate from JavaScript in Sublime Text.

Want to put your parser to test? Check out [syntax_test_edn.edn](./test_syntax/edn.edn) and [syntax_test_clojure.cljc](./test_syntax/clojure.cljc).

## nREPL Client

Sublime Clojure nREPL client enables interactive development from the comfort of your editor.

Principles:

- Minimal distraction. Display evaluation results inline.
- Decomplected. Eval code and nothing more.
- Server-agnostic. We work with any nREPL socket, local or over network.

Features:

- [x] evaluate code,
- [x] display evaluation results inline.
- [x] display stack traces inline,
- [x] interrupt evaluation,
- [x] eval multiple forms at once (parallel evaluation),
- [x] lookup symbol info,
- [x] show evaluation time.

We intentionally excluded following features:

- [ ] Autocomplete. Static analysis is much simpler and much more reliable than requiring an always-live connection to the working app.

Why nREPL and not Socket Server REPL/pREPL/unREPL?

- nREPL has the widest adoption,
- nREPL is machine-friendly,
- nREPL comes with batteries included (interrupt, load-file, sideload),
- nREPL is extensible via middleware,
- nREPL serialization is easier to access from Python than EDN.

Differences from [Tutkain](https://tutkain.flowthing.me/):

- nREPL instead of Socket Server REPL
- Does not have separate REPL panel
- Keeps multiple eval results on a screen simultaneously
- Can show stack traces inline in editor
- Can eval several forms in parallel
- Can eval non well-formed forms (e.g. `(+ 1 2`)
- Can eval infinite sequences
- Redirects all `*out*`/`*err*` to `System.out`/`System.err`

## Installation

Install package from source:

```bash
git clone https://github.com/tonsky/sublime-clojure.git
ln -s `pwd`/sublime-clojure ~/Library/Application\ Support/Sublime\ Text/Packages/Sublime\ Clojure
```

Or from Package Control (coming later):

- `Package Control: Install Package` → `Sublime Clojure`

Assign syntax to Clojure files:

- open any clj/cljc/cljs file,
- run `View` → `Syntax` → `Open all with current extension as...` → `Sublime Clojure` → `Clojure (Sublime Clojure)`.

## How to use

Important! Make sure you switched your syntax to `Clojure (Sublime Clojure)`.

1. Run nREPL server.
2. Run `Clojure REPL: Connect` command.

From here you have three options:

`Clojure REPL: Evaluate Topmost Form` evaluates topmost form around your cursor:

<img src="https://raw.github.com/tonsky/sublime-clojure/master/screenshots/eval_topmost.png" width="285" height="55" alt="Evaluate Topmost">

`Clojure REPL: Evaluate Selection` evaluates selected text:

<img src="https://raw.github.com/tonsky/sublime-clojure/master/screenshots/eval_selection.png" width="283" height="58" alt="Evaluate Selection">

`Clojure REPL: Evaluate Buffer` will evaluate the entire file:

<img src="https://raw.github.com/tonsky/sublime-clojure/master/screenshots/eval_buffer.png" width="416" height="211" alt="Evaluate Buffer">

You don’t have to wait for one form to finish evaluating to evaluate something else. Multiple things can be executed in parallel:

<img src="https://raw.github.com/tonsky/sublime-clojure/master/screenshots/eval_parallel.gif" width="353" height="151" alt="Evaluate in Parallel">

By default, Sublime Clojure will also print evaluation time if it took more than 100 ms:

<img src="https://raw.github.com/tonsky/sublime-clojure/master/screenshots/eval_elapsed.png" width="453" height="134" alt="Elapsed time">

If your evaluation failed, put your cursor inside failed region and run `Clojure REPL: Toggle Stacktrace`:

<img src="https://raw.github.com/tonsky/sublime-clojure/master/screenshots/toggle_stacktrace.png" width="594" height="165" alt="Toggle Stacktrace">

If your evaluation runs too long and you want to interrupt it, run `Clojure REPL: Interrupt Pending Evaluations`:

<img src="https://raw.github.com/tonsky/sublime-clojure/master/screenshots/interrupt.png" width="587" height="39" alt="Interrupt">

If you want to clear evaluation results, run `Clojure REPL: Clear Evaluation Results`.

Finally, run `Clojure REPL: Lookup Symbol` when over a symbol to see its documentation:

<img src="https://raw.github.com/tonsky/sublime-clojure/master/screenshots/lookup.png" width="593" height="143" alt="Lookup Symbol">

To edit settings, run `Preferences: Sublime Clojure Settings` command.

## Default Key Bindings

Command                       | macOS                            | Windows/Linux                                   | Mnemonic
------------------------------|----------------------------------|-------------------------------------------------| -----------------------
Evaluate Topmost Form         | <kbd>Ctrl</kbd> <kbd>Enter</kbd> | <kbd>Ctrl</kbd> <kbd>Alt</kbd> <kbd>Enter</kbd> |
Evaluate Selection            | <kbd>Ctrl</kbd> <kbd>Enter</kbd> | <kbd>Ctrl</kbd> <kbd>Alt</kbd> <kbd>Enter</kbd> |
Evaluate Buffer               | <kbd>Ctrl</kbd> <kbd>B</kbd>     | <kbd>Ctrl</kbd> <kbd>Alt</kbd> <kbd>B</kbd>     | <kbd>B</kbd>uffer
Toggle Stacktrace             | <kbd>Ctrl</kbd> <kbd>E</kbd>     | <kbd>Ctrl</kbd> <kbd>Alt</kbd> <kbd>E</kbd>     | <kbd>E</kbd>xception
Interrupt Pending Evaluations | <kbd>Ctrl</kbd> <kbd>C</kbd>     | <kbd>Ctrl</kbd> <kbd>Alt</kbd> <kbd>C</kbd>     | <kbd>C</kbd>ancel
Clear Evaluation Results      | <kbd>Ctrl</kbd> <kbd>L</kbd>     | <kbd>Ctrl</kbd> <kbd>Alt</kbd> <kbd>L</kbd>     | C<kbd>l</kbd>ear
Lookup Symbol                 | <kbd>Ctrl</kbd> <kbd>D</kbd>     | <kbd>Ctrl</kbd> <kbd>Alt</kbd> <kbd>D</kbd>     | <kbd>D</kbd>ocumentation

To change key bindings, run `Preferences: Sublime Clojure Key Bindings` command.

## License

[MIT License](./LICENSE.txt)

## See also

[Writer Color Scheme](https://github.com/tonsky/sublime-scheme-writer): A color scheme optimized for long-form writing.

[Alabaster Color Scheme](https://github.com/tonsky/sublime-scheme-alabaster): Minimal color scheme for coding.

[Sublime Profiles](https://github.com/tonsky/sublime-profiles): Profile switcher.

## Credits

Made by [Niki Tonsky](https://twitter.com/nikitonsky).
