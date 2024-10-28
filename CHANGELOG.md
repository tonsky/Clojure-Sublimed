### WIP

- Pretty print selection #123
- Execute code from inside top-level `; ...` and `#_...` #124
- `Toggle Comment` command that uses `#_` instead of `;;`
- Remove background color on quoted strings inside metadata
- Better handle eval of `#_` forms in nREPL JVM
- Made line numbers much more transparent

### 4.2.2 - Sep 27, 2024

- cljfmt correctly indents forms with custom rules - again

### 4.2.1 - Sep 27, 2024

- cljfmt correctly indents forms with custom rules

### 4.2.0 - Sep 27, 2024

- Simplified formatting rules: if list's first form is a symbol, indent next line by +2 spaces, in all other cases, indent to opening paren (1 space)
- We now provide `cljfmt.edn` that tries to match our default formatting
- Better handle selection after formatting with cljfmt
- Highlight namespace name as `entity.name`, same as defs
- No exceptions on disconnect
- Removed background on unused symbols inside quotes

### 4.1.1 - Sep 6, 2024

- Support Clojure 1.12 array type annotations

### 4.1.0 - Aug 30, 2024

- Eval previous form at current level #118
- Auto-detect UNIX sockets, support relative paths
- Correctly parse escaped comma #120 via @oakmac

### 4.0.0 - Aug 23, 2024

Syntax has been significantly reworked.

- New syntax that can highlight reader comments `comment.reader` together with the following form
- Highlight `(comment ...)` blocks as `comment.form`
- Highlight namespaces in symbols as `meta.namespace.symbol`
- Highlight unused symbols as `source.symbol.unused`
- Properly highlight `entity.name` in `def*` forms only at second position, skipping all meta/comments
- Quote & syntax quote highlight following form as `meta.quoted` and `meta.quoted.syntax`
- Metadata highlights following form as `meta.metadata`
- Octal & arbitrary radix integers #71
- Better keyword detection

Other changes:

- Built-in color scheme to utilize REPL and new syntax features.
- Allow using `cljfmt` for formatting (requires `cljfmt` binary on `$PATH`)
- Removed separate EDN syntax, merged with main Clojure (Sublimed)
- Settings can now be specified in main `Preferences.sublime-settings` as well. Just prepend `clojure_sublimed_` to each setting’s name.
- REPL can detect namespaces with meta on ns form #116
- Detect `.shadow-cljs/nrepl.port` and `.shadow-cljs/socket-repl.port` #114
- Connect commands now accept `timeout` argument for automation scenarios like “start clojure, start trying to connect to REPL until port is available”

### 3.8.0 - Aug 8, 2024

- `clojure_sublimed_reindent` command that reindents entire buffer if selection is empty and only selected lines if not

### 3.7.3 - June 16, 2024

- Fixed Socket REPL not working on Windows #95
- Fixed Exception in settings on first install #109

### 3.7.2 - May 5, 2024

- Some defensive coding around default settings fallback #109

### 3.7.1 - Mar 15, 2024

- Added `expand` argument to `clojure_sublimed_eval` command

### 3.7.0 - Mar 14, 2024

- New feature: Watches! Added `Add Watch` command
- Added `output.repl` panel for raw nREPL output #104
- Added `Toggle Output Panel` command for raw nREPL connections #104
- Fixed `Reconnect` command
- Added optional `on_finish` argument to `cs_conn.eval`
- Added `print_quota` as a setting and as an argument to `cs_conn.eval`

### 3.6.0 - Mar 5, 2024

- Added optional `transform` argument to `clojure_sublimed_eval` #101 #102
- Display failed test reports as red
- Socket REPL: fixed escaping in `clojure_sublimed_eval_code` #103 via @KGOH

### 3.5.0 - Jan 22, 2023

- Detect namespace from in-ns forms

### 3.4.1 - Dec 7, 2023

- Fixed status eval not clearing on disconnect

### 3.4.0 - Nov 30, 2023

- Support multiple windows, one connection per widnow
- Support .repl-port files for Socket REPL

### 3.3.0 - Oct 26, 2023

- Eval inside already evaled region re-evals same region instead of going to top form
- Printer can display newlines

### 3.2.1 - Sep 10, 2023

- Socket: Report number of reflection warnings in status bar

### 3.2.0 - Sep 10, 2023

- Socket REPL: handle exceptions in lookup
- Do not silence exception during lazy seq printing

### 3.1.3 - Aug 19, 2023

- Show file/line/column information when `clojure_sublimed_eval_code` fails

### 3.1.2 - June 1, 2023

- Fixed indenting of reader conditionals

### 3.1.1 - Apr 3, 2023

- Fixed perf degradation on reindent #96

### 3.1.0 - Mar 13, 2023

- Socket: Fixed status_eval, bind *1/*2/*3/*e for e.g. tools.namespace
- Do not fail because of styles #91

### 3.0.0 - Mar 9, 2023

- Huge refactoring, easier to add new REPLs
- REPLs do not depend on syntax highlighting anymore, will work with any syntax
- new REPL: Raw nREPL
- new REPL: Socket REPL (no external dependencies, faster to start than nREPL)
- Report results of different forms in the same selection separately (Socket REPL only)
- Removed `clojure_sublimed_require_namespace` command
- Implemented pretty-printing of expanded results in Python, removing clojure.pprint dependency
- Added `wrap_width` setting

### 2.11.0 - Jan 5, 2023

- Connect command accepts 'auto' (will look for `.nrepl-port` file) #82

### 2.10.0 - Jan 4, 2023

- Do not move cursor if error region visible on screen #73
- Fixed: Wrong highlight of the source of error #79
- Render sequential spaces #78
- Fixed: Exceptions from evaluating buffer without a file name are not processed #18
- Special case when CompilerError has wrong location info
- Select whole line on error

### 2.9.1 - Dec 3, 2022

- Added Main.sublime-menu #85 via @wundervaflja

### 2.9.0 - Nov 21, 2022

- Allow connection through UNIX domain socket #80 via @tribals

### 2.8.1 - Nov 2, 2022

- Allow specifying `ns` in `clojure-sublimed-eval-code`

### 2.8.0 - Oct 17, 2022

- Shadow-cljs support #43 #77 via @sainadh-d

### 2.7.0 - Sep 27, 2022

- Added `eval_shared`

### 2.6.0 - Sep 27, 2022

- Added `format_on_save` option #76 thx @sainadh-d

### 2.5.2 - May 24, 2022

- Fixed clojure_sublimed_eval_code #75
- Fixed clojure_sublimed_insert_newline with multicursor #72 

### 2.5.1 - January 19, 2022

- Fixed indent on Enter

### 2.5.0 - January 18, 2022

- Pretty print returned values. Toggle with Toggle Info (Ctrl + I)
- Do not reindent blank lines

### 2.4.1 - January 13, 2022

- Proper `messages.json` and install message.

### 2.4.0 - January 12, 2022

New commands:

- Reindent Buffer
- Reindent Lines
- Insert Newline

### 2.3.0 - January 4, 2022

- A command to require namespace of symbol #12 #59 via @jaihindhreddy
- Fixed regions returning on undo #22 #60 via @jaihindhreddy
- Fixed AttributeError: 'Connection' object has no attribute 'eval_in_session'

### 2.2.0 - December 29, 2021

- Do clone, eval and close in a single middleware #20 via @jaihindhreddy and @tonsky
- Auto-close sessions cloned by eval #48 #49 #50 via @tonsky
- Interrupt pending eval when region is erased #16 #58 via @jaihindhreddy and @tonsky

### 2.1.0 - December 28, 2021

- An option to use nREPL session for eval #9 #57 via @jaihindhreddy
- Optimize region invalidation #19 #54 via @jaihindhreddy
- Optimise iterating through evals by maintaining evals by view #23 #51 #55 #56 via @jaihindhreddy
- Use ephemeral sessions instead of cloning for each eval #20 #48 #50 via @jaihindhreddy

### 2.0.0 - December 22, 2021

- Renamed to Clojure Sublimed due to Package Control policy. Thanks @YurySolovyov for the name

### 1.0.7 - December 15, 2021

- Toggle symbol info works on def/defn #44 #45

### 1.0.6 - December 14, 2021

- Escape HTML in evaluation results #35 #38 thx @jaihindhreddy
- Measure time-taken in nREPL middleware #13 #39 thx @jaihindhreddy
- Eval form on the left if between forms #10 #42 thx @jaihindhreddy
- Fixed Ctrl+I at the last position in the file #17
- Copy evaluation result #37

### 1.0.5 - November 10, 2021

- Fixed runtime error on startup #32

### 1.0.4 - November 10, 2021

- Clear Eval Code status in non-active views #32
- When evaluating buffer fails, scroll to error line #28

### 1.0.3 - November 9, 2021

- Fixed exception in eval code command handling excetpion response

### 1.0.2 - November 4, 2021

- Automatically detect port from .nrepl-port #5

### 1.0.1 - November 1, 2021

- Do not bundle any key bindings by default
- Bind keys to eval arbitrary code #25
- Remove phantom if region is fully removed #21

### 1.0.0 - October 25, 2021

- Initial release

### October 22, 2021

- Renamed syntaxes to `Clojure (Sublime Clojure)` and `EDN (Sublime Clojure)`
- Added nREPL client

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
