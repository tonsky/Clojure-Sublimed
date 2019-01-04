# Clojure

[ ] def -> variable.other.constant
[ ] defn -> entity.name.function
[v] rest -> entity.name.*

[v] Reader conditionals `#?()` `#?@()`
[v] Regexps `#"..."`
[v] Lambdas `#(...)`
[v] Quotes `'` `&` `\``
[v] Splices `~` `~@`
[v] Vars `#'`
[v] derefs `@`
[ ] accessors `.`, `.-` punctuation.accessor

[ ] Variables? variable.other, variable.language (`&env`, `&form`), variable.parameter, variable.other.member
[ ] Fn invocations: variable.function
[ ] Mark as constant everything escaped?
[ ] Do not match symbols?
[v] Limit data types of metadata (symbol/string/map/keyword)

# REPL

[ ] pending eval indicator
[ ] cancel eval
[ ] eval top-level form
[ ] hint arglists
[ ] no CIDER dep (autoinstall)
[ ] auto-detect .nrepl-port
[ ] handle large output
[ ] print in-progress stdout
[ ] cljc eval
[ ] keep file/line when evaling forms
[ ] prepl?
[ ] show symbol docs
[ ] reliable ns name parsing