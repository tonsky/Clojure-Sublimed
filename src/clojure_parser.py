import re, time

class Node:
    def __init__(self, start, end, children = [], name = None, text = None):
        self.start = start
        self.end = end
        self.children = children
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
    if isinstance(x, str):
        return parsers[x]
    else:
        return x

def append_children(msg, children, node):
    if node.name:
        children.append(node)
    else:
        for child in node.children:
            append_children(msg, children, child)

class Regex:
    def __init__(self, pattern_str, name = None):
        self.name = name
        self.pattern_str = pattern_str
        self.pattern = re.compile(pattern_str)

    def parse(self, string, pos):
        if match := self.pattern.match(string, pos):
            return Node(pos, match.end(), name = self.name, text = match.group(0))

class String:
    def __init__(self, str, name = None):
        self.str = str
        self.len = len(str)
        self.name = name

    def parse(self, string, pos):
        if pos + self.len <= len(string):
            if string[pos:pos + self.len] == self.str:
                return Node(pos, pos + self.len, name = self.name, text = self.str)

class Char:
    def __init__(self, char, name = None):
        self.char = char
        self.name = name

    def parse(self, string, pos):
        if pos < len(string) and string[pos] == self.char:
            return Node(pos, pos + 1, name = self.name, text = self.char)

class NotChar:
    def __init__(self, char, name = None):
        self.char = char
        self.name = name

    def parse(self, string, pos):
        if pos < len(string):
            if string[pos] != self.char:
                return Node(pos, pos + 1, name = self.name, text = string[pos])

class AnyChar:
    def __init__(self, name = None):
        self.name = name

    def parse(self, string, pos):
        if pos < len(string):
            return Node(pos, pos + 1, name = self.name, text = string[pos])

class Seq:
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
                append_children(self, children, node)
                end = node.end
            else:
                return None
        return Node(pos, end, children, name = self.name)

class Choice:
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
    def __init__(self, parser_name):
        self.parser_name = parser_name
        self.parser = None

    def parse(self, string, pos):
        if not self.parser:
            self.parser = get_parser(self.parser_name)
        return self.parser.parse(string, pos) or Node(pos, pos)

class Repeat:
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
            append_children(self, children, node)
            end = node.end
        return Node(pos, end, children, name = self.name if end > pos else None)

class Repeat1:
    def __init__(self, parser_name):
        self.parser_name = parser_name
        self.parser = None

    def parse(self, string, pos):
        if not self.parser:
            self.parser = get_parser(self.parser_name)
        children = []
        end = pos
        while node := self.parser.parse(string, end):
            append_children(self, children, node)
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
                        Char('"', name = ".close"),
                        name = "string")

parsers['brackets'] = Seq(Char("[", name = ".open"),
                          Repeat(Choice('_gap', '_form', NotChar(r"]", name = "error")), name = ".body"),
                          Char("]", name = ".close"),
                          name = "brackets")

parsers['parens'] = Seq(Regex(r"(#\?@|#\?|#=|#)?\(", name = ".open"),
                        Repeat(Choice('_gap', '_form', NotChar(r")", name = "error")), name = ".body"),
                        Char(")", name = ".close"),
                        name = "parens")

parsers['braces'] = Seq(Regex(r"(#(:" + token + r")?)?\{", name = ".open"),
                        Repeat(Choice('_gap', '_form', NotChar(r"}", name = "error")), name = ".body"),
                        Char("}", name = ".close"),
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

parsers['source'] = Repeat(Choice('_gap', '_form', AnyChar(name = "error")), name = "source")

def parse(string):
    return get_parser('source').parse(string, 0)

def is_symbol(node):
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

def search(node, pos, pred = lambda x: True, max_depth = 1000):
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

parse_trees = {}

def parse_tree(view):
    import sublime
    id = view.buffer_id()
    if id in parse_trees:
        return parse_trees[id]
    text = view.substr(sublime.Region(0, view.size()))
    parsed = parse(text)
    parse_trees[id] = parsed
    return parsed

def invalidate_parse_tree(view):
    id = view.buffer.id()
    if id in parse_trees:
        del parse_trees[id]
