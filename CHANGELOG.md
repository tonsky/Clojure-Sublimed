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
