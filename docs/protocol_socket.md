# Upgraded Socket REPL protocol

All messages are:

- EDN-formatted,
- No keywords or symbols, only strings and ints,
- '\n' inside strings escaped,
- no newlines inside messages,
- newline after each message.

---

```
RCV {"tag" "started"}
```

When client receives this message, REPL has finished upgrading and is ready to accept commands.

---

```
SND {"op"     => "eval"
     "id"     => any, id
     "code"   => string. Code to evaluate
     "ns"     => string, optional. Namespace name. Defaults to user
     "file"   => string, optional. File name where this code comes from. Defaults to NO_SOURCE_FILE
     "line"   => int, optional. Line in file
     "column" => int, optional. Column position of first code character, 0-based}
```

Evaluate form. If `code` contains multiple top-level forms, they are evaluated sequentially. After each successful evaluation, you get this:

```
RCV {"tag"         => "ret"
     "id"          => any, id
     "idx"         => int, sequential number of form in original `code`
     "val"         => string, pr-str value
     "time"        => int, execution time, ms
     "form"        => string, form that being evaluated
     "from_line"   => int, line at the beginning of the form
     "from_column" => int, column at the beginning of the form
     "to_line"     => int, line at the end of the form
     "to_column"   => int, column at the end of the form}
```

Value string will be truncated after 1024 characters, so don’t rely on it be valid readable Clojure.

If some form fails, you get this and batch execution stops:

```
RCV {"tag"    => "ex"
     "id"     => any. Id
     "val"    => string. Error messasge
     "trace"  => multiline string. Stacktrace
     "source" => string, if known. File name
     "line"   => int, if known
     "column" => int, 0-based, if known
     "form", "from_"/"to_" "_line"/"_column" => same as in "ret"}
```

Finally, success of failure, you’ll always recieve this:

```
{"tag" => "done"
 "id"  => any. Id}
```

---

To interrupt evaluation, send this:

```
SND {"op" => "interrupt"
     "id" => any}
```

Whole batch will be stopped by throwing an exception. You’ll receive :ex and :done after this

---

To look up a symbol, send this:

```
SND {"op"     => "lookup"
     "id"     => any
     "symbol" => string
     "ns"     => string, optional, defaults to user}
```

To which you’ll get either

```
RCV {"tag" => "lookup"
     "id"  => any
     "val" => map, description}
```

Val map looks like this for functions:

```
{"ns"       "clojure.core"
 "name"     "str"
 "arglists" "([] [x] [x & ys])"
 "doc"      "With no args, returns the empty string. With one arg x, returns\n  x.toString().  (str nil) returns the empty string. With more than\n  one arg, returns the concatenation of the str values of the args."
 "file"     "clojure/core.clj"
 "line"     "546"
 "column"   "1"
 "added"    "1.0"}
```

for vars:

```
{"ns"    "clojure.core"
 "name"  "*warn-on-reflection*"
 "doc"   "When set to true, the compiler will emit warnings when reflection is\n  needed to resolve Java method calls or field accesses.\n\n  Defaults to false."
 "added" "1.0"}
```

and for special forms:

```
{"ns"           "clojure.core"
 "name"         "do"
 "forms"        "[(do exprs*)]"
 "doc"          "Evaluates the expressions in order and returns the value of\n  the last. If no expressions are supplied, returns nil."
 "file"         "clojure/core.clj"
 "special-form" "true"}
```

If symbol can’t be found, you’ll get:

```
RCV {"tag" => "ex"
     "id"  => any, id
     "val" => string, message}
```
