import re, time

class Node:
    """
    AST Node.
    Start-end positions in string. Start included, end excluded.
    Optional children. Name from Named ('token', 'string' etc).
    Text is substring[start:end], only for terminal nodes like Regex or String
    """
    def __init__(self, start, end, children = None, name = None, text = None):
        self.start = start
        self.end = end
        self.children = children if children is not None else []
        self.name = name
        self.text = text

    def __str__(self, indent = ""):
        res = "{}({} {}..{}".format(indent, self.name, self.start, self.end)
        if self.text:
            res += " '" + self.text.replace("\n", "\\n") + "'"
        if self.children:
            for child in self.children:
                res += "\n" + child.__str__(indent + "  ")
        res += ")"
        return res

    def __getattr__(self, name):
        for child in self.children:
            if child.name == "." + name:
                return child

class Named:
    """
    Parser that assigns name to Node
    """
    def __init__(self, name, parser_name):
        self.name = name
        self.parser_name = parser_name
        self.parser = None

    def parse(self, string, pos):
        if not self.parser:
            self.parser = get_parser(self.parser_name)
        node = self.parser.parse(string, pos)
        if node is None:
            return None
        elif not node.name:
            node.name = self.name
            return node
        else:
            return Node(node.start, node.end, children = [node], name = self.name)

parsers = {}

def get_parser(x):
    """
    This is basically needed to postpone dependency resolution after all named parsers have been created, to allow for cyclic references
    """
    if isinstance(x, str):
        return parsers[x]
    else:
        return x

def append_children(children, node):
    """
    Append named nodes, but skip and splice children directly if no name
    """
    if node.name:
        children.append(node)
    else:
        for child in node.children:
            append_children(children, child)

class Regex:
    """
    Terminal parser that matches regex
    """
    def __init__(self, pattern_str, name = None):
        self.name = name
        self.pattern_str = pattern_str
        self.pattern = re.compile(pattern_str)

    def parse(self, string, pos):
        if match := self.pattern.match(string, pos):
            return Node(pos, match.end(), name = self.name, text = match.group(0))

class String:
    """
    Terminal parser that matches exact string match
    """
    def __init__(self, str, name = None):
        self.str = str
        self.len = len(str)
        self.name = name

    def parse(self, string, pos):
        if pos + self.len <= len(string):
            if string[pos:pos + self.len] == self.str:
                return Node(pos, pos + self.len, name = self.name, text = self.str)

class Char:
    """
    Terminal parser that matches one char
    """
    def __init__(self, char, name = None):
        self.char = char
        self.name = name

    def parse(self, string, pos):
        if pos < len(string) and string[pos] == self.char:
            return Node(pos, pos + 1, name = self.name, text = self.char)

class NotChar:
    """
    Terminal parser that matches any single char but one
    """
    def __init__(self, char, name = None):
        self.char = char
        self.name = name

    def parse(self, string, pos):
        if pos < len(string):
            if string[pos] != self.char:
                return Node(pos, pos + 1, name = self.name, text = string[pos])

class AnyChar:
    """
    Terminal parser that matches any single char
    """
    def __init__(self, name = None):
        self.name = name

    def parse(self, string, pos):
        if pos < len(string):
            return Node(pos, pos + 1, name = self.name, text = string[pos])

class Seq:
    """
    Parser that matches a linear sequence of other parsers
    """
    def __init__(self, *parser_names, name = None):
        self.parser_names = parser_names
        self.parsers = None
        self.name = name

    def parse(self, string, pos):
        if not self.parsers:
            self.parsers = [get_parser(n) for n in self.parser_names]
        children = []
        end = pos
        for parser in self.parsers:
            if node := parser.parse(string, end):
                append_children(children, node)
                end = node.end
            else:
                return None
        return Node(pos, end, children, name = self.name)

class Choice:
    """
    Parser that matches first matching of several parsers
    """
    def __init__(self, *parser_names):
        self.parser_names = parser_names
        self.parsers = None

    def parse(self, string, pos):
        if not self.parsers:
            self.parsers = list([get_parser(n) for n in self.parser_names])
        for parser in self.parsers:
            if node := parser.parse(string, pos):
                return node

class Optional:
    """
    Parser that matches child parser or skips it altogether
    """
    def __init__(self, parser_name):
        self.parser_name = parser_name
        self.parser = None

    def parse(self, string, pos):
        if not self.parser:
            self.parser = get_parser(self.parser_name)
        return self.parser.parse(string, pos) or Node(pos, pos)

class Repeat:
    """
    Parser that matches child parser zero or more times
    """
    def __init__(self, parser_name, name = None):
        self.parser_name = parser_name
        self.parser = None
        self.name = name

    def parse(self, string, pos):
        if not self.parser:
            self.parser = get_parser(self.parser_name)
        children = []
        end = pos
        while node := self.parser.parse(string, end):
            append_children(children, node)
            end = node.end
        return Node(pos, end, children, name = self.name if end > pos else None)

class Repeat1:
    """
    Parser that matches child parser one or more times
    """
    def __init__(self, parser_name):
        self.parser_name = parser_name
        self.parser = None

    def parse(self, string, pos):
        if not self.parser:
            self.parser = get_parser(self.parser_name)
        children = []
        end = pos
        while node := self.parser.parse(string, end):
            append_children(children, node)
            end = node.end
        if children:
            return Node(pos, end, children)

ws = r" ,\n\r\t\f\u000B\u001C\u001D\u001E\u001F\u2028\u2029\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2008\u2009\u200a\u205f\u3000"
parsers['_ws'] = Regex(r'[' + ws + r']+')
parsers['comment'] = Regex(r";[^\n]*", name = "comment")
parsers['discard'] = Seq(String("#_", name = "marker"), Repeat('_gap'), Named(".body", '_form'), name = "discard")
parsers['_gap'] = Choice('_ws', 'comment', 'discard')

parsers['meta'] = Seq(Repeat1(Seq(Regex(r'#?\^', name = ".marker"),
                                  Repeat('_gap'),
                                  Named(".meta", '_form'),
                                  Repeat('_gap'))),
                      Named(".body", '_form'),
                      name = "meta")

parsers['wrap'] = Seq(Regex(r"(@|'|`|~@|~|#')", name = ".marker"),
                      Repeat('_gap'),
                      Named('.body', '_form'),
                      name = "wrap")

token = '[^' + r'()\[\]{}\"@~^;`#\'' + ws + '][^' + r'()\[\]{}\"@^;`' + ws + ']*'
parsers['token'] = Regex(r'(##)?(\\[()\[\]{}\"@^;`]|' + token + ")", name = "token")

parsers['string'] = Seq(Regex(r'#?"', name=".open"),
                        Optional(Regex(r'([^"\\]+|\\.)+', name = ".body")),
                        Optional(Char('"', name = ".close")),
                        name = "string")

parsers['brackets'] = Seq(Char("[", name = ".open"),
                          Repeat(Choice('_gap', '_form', NotChar(r"]", name = "error")), name = ".body"),
                          Optional(Char("]", name = ".close")),
                          name = "brackets")

parsers['parens'] = Seq(Regex(r"(#\?@|#\?|#=|#)?\(", name = ".open"),
                        Repeat(Choice('_gap', '_form', NotChar(r")", name = "error")), name = ".body"),
                        Optional(Char(")", name = ".close")),
                        name = "parens")

parsers['braces'] = Seq(Regex(r"(#(:" + token + r")?)?\{", name = ".open"),
                        Repeat(Choice('_gap', '_form', NotChar(r"}", name = "error")), name = ".body"),
                        Optional(Char("}", name = ".close")),
                        name = "braces")

parsers['tagged'] = Seq(Char("#"),
                        Repeat('_gap'),
                        Named('.tag', 'token'),
                        Repeat('_gap'),
                        Named('.body', '_form'),
                        name = "tagged")

parsers['_form'] = Choice('token',
                          'string',
                          'parens',
                          'brackets',
                          'braces',
                          'wrap',
                          'meta',                              
                          'tagged')

# top-level parser
parsers['source'] = Repeat(Choice('_gap', '_form', AnyChar(name = "error")), name = "source")

def parse(string):
    """
    The main function that parses string and returns AST
    """
    return get_parser('source').parse(string, 0)

def is_symbol(node):
    """
    Utility functions that checks if AST node is a symbol
    """
    if node.name == 'token' and node.text:
        s = node.text
        if s == 'true' or s == 'false' or s == 'nil':
            return False
        elif s == '/' or s == '-' or s == '+':
            return True
        elif s[0] == '+' or s[0] == '-':
            return s[1] not in '0123456789'
        else:
            return s[0] not in '+-:\\0123456789'

def partition(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]

def unescape(m):
    s = m.group(0)
    if '\\\\' == s:
        return '\\'
    elif '\\"' == s:
        return '"'
    elif '\\n' == s:
        return '\n'
    elif '\\t' == s:
        return '\t'
    elif '\\r' == s:
        return '\r'
    elif '\\f' == s:
        return '\f'
    elif '\\b' == s:
        return '\b'

def as_obj(node, string):
    if 'token' == node.name and node.text:
        s = node.text
        if 'true' == s:
            return True
        elif 'false' == s:
            return False
        elif 'nil' == s:
            return None
        elif ':' == s[0]:
            return s
        elif re.fullmatch(r'[+-]?[0-9]*\.[0-9]*([eE][+-]?\d+)?', s):
            return float(s)
        elif re.fullmatch(r'[+-]?[0-9]+', s):
            return int(s)
        else:
            text = string[node.start:node.end]
    elif 'string' == node.name and node.body:
        text = re.sub(r'\\[\\"rntfb]', unescape, node.body.text)
    elif 'string' == node.name:
        text = ''
    else:
        text = string[node.start:node.end]
    return text

def parse_as_dict(string):
    parsed = parse(string)
    braces = parsed.children[0]
    assert 'braces' == braces
    dict = {}
    for key, val in partition(braces.body.children, 2):
        key = as_obj(key, string)
        val = as_obj(val, string)
        dict[key] = val
    return dict

def search(node, pos, pred = lambda x: True, max_depth = 1000):
    """
    Search inside node what’s the deepest node that includes pos.
    Stops at max_depth and if pred evals to true.
    If two nodes touch around pos, checks both for pred.
    """
    if max_depth <= 0 or not node.children:
        if pred(node):
            return node
        else:
            return None
    for child in node.children:
        if child.start <= pos <= child.end:
            if res := search(child, pos, pred = pred, max_depth = max_depth - 1):
                return res
        elif pos < child.start:
            break

if __package__:
    import sublime, sublime_plugin

def parse_tree(view, region = None):
    """
    Parses current buffer content and return AST
    """
    id = view.buffer_id()
    text = view.substr(region or sublime.Region(0, view.size()))
    return parse(text)

def symbol_at_point(view, point):
    """
    Returns symbol left/right/around cursor 
    """
    parsed = parse_tree(view)
    start = time.time()
    if node := search(parsed, point, pred = is_symbol):
        return sublime.Region(node.start, node.end)

def topmost_form(view, point):
    """
    Find topmost form under cursor, or left to the cursor.
    If inside (comment), finds second-topmost form
    """

    # move left to first non-space
    if point >= view.size() or view.substr(sublime.Region(point, point + 1)).isspace():
        while point > 0 and view.substr(sublime.Region(point - 1, point)).isspace():
            point = point - 1

    parsed = parse_tree(view)
    if node := search(parsed, point, max_depth = 1):
        if body := node.body:
            if body.children:
                first_form = body.children[0]
                if first_form.name == "token" and first_form.text == "comment" and point > first_form.end:
                    if inner := search(body, point, max_depth = 1):
                        node = inner
        return sublime.Region(node.start, node.end)

def previous_form_at_level(view, point):
    """
    Finds last form before cursor on the same level. E.g.

    (+ 1 (* 2 3) 3)
                ^ cursor
         ^^^^^^^ result
    """
    parsed = parse_tree(view)
    def find_previous(node):
        if not node:
            return
        children = node.body.children if node.body else node.children
        if not children:
            return
        for child in reversed(children):
            if child.end <= point:
                return child
            if child.start < point < child.end:
                return find_previous(child)
    return find_previous(parsed)

def namespace(view, point):
    """
    Finds name of last namespace defined in buffer up to the point
    """
    ns = None
    parsed = parse_tree(view)
    for child in parsed.children:
        if child.end >= point:
            break
        if child.name == 'meta':
            child = child.body.children[0]
        if child.name == 'parens':
            body = child.body
            if len(body.children) >= 2:
                first_form = body.children[0]
                if first_form.name == 'token' and first_form.text == 'ns':
                    second_form = body.children[1]
                    while second_form.name == 'meta' and second_form.body:
                        second_form = second_form.body.children[0]
                    if is_symbol(second_form):
                        ns = second_form.text
                elif first_form.name == 'token' and first_form.text == 'in-ns':
                    second_form = body.children[1]
                    if second_form.name == 'wrap' and second_form.marker.text == "'":
                        unwrapped = second_form.body.children[0]
                        if is_symbol(unwrapped):
                            ns = unwrapped.text
    return ns

def defsym(node):
    """
    Finds name of the symbol (def.* <THIS> ...) defined by node form
    """
    if node.name == 'parens':
        body = node.body
        if len(body.children) >= 2:
            first_form = body.children[0]
            if first_form.name == 'token' and re.fullmatch(r'(ns|([^/]+/)?def.*)', first_form.text):
                second_form = body.children[1]
                while second_form.name == 'meta' and second_form.body:
                    second_form = second_form.body.children[0]
                if is_symbol(second_form):
                    return second_form.text

def plugin_unloaded():
    parsed_cache = {}
