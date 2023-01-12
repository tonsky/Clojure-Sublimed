import re

DEBUG = False
INDENT = ""

class Debug:
    def __init__(self, name, *args):
        global DEBUG
        if DEBUG:
            self.name = name.format(*args)

    def __enter__(self):
        global DEBUG, INDENT
        if DEBUG:
            print(INDENT, self.name)
            INDENT += "  "

    def __exit__(self, exc_type, exc_value, exc_tb):
        global DEBUG, INDENT
        if DEBUG:
            INDENT = INDENT[:-2]

class Node:
    def __init__(self, start, end, children = [], name = None):
        self.start = start
        self.end = end
        self.children = children
        self.name = name

    def serialize(self, string, indent = ""):
        res = "{}({} {}..{}".format(indent, self.name, self.start, self.end)
        if self.children:
            for child in self.children:
                if isinstance(child, str):
                    res += " '" + child.replace("\n", "\\n") + "'"
                else:
                    res += "\n" + child.serialize(string, indent + "  ")
        else:
            res += " '" + string[self.start:self.end].replace("\n", "\\n") + "'"
        res += ")"
        return res

    def __str__(self):
        return "Node({} {}..{} {} children)".format(self.name, self.start, self.end, len(self.children))

    def __getattr__(self, name):
        for child in self.children:
            if isinstance(child, Node) and child.name == name:
                return child

class Named:
    def __init__(self, name, parser_name):
        self.name = name
        self.parser_name = parser_name
        self.parser = None

    def parse(self, string, pos):
        if not self.parser:
            self.parser = get_parser(self.parser_name)
        with Debug("Named '{}' at {}", self.name, pos):
            node = self.parser.parse(string, pos)
            if not node:
                return None
            elif self.name.startswith(".") and (not node.children or node.start == node.end):
                return node
            elif not node.name:
                node.name = self.name
                return node
            else:
                return Node(node.start, node.end, children = [node], name = self.name)

parsers = {}

def get_parser(x):
    if not isinstance(x, str):
        return x
    elif x[0] == "_":
        return parsers[x]
    else:
        return Named(x, parsers[x])

def append_children(msg, children, node):
    if not isinstance(node, Node):
        pass
    elif node.name:
        children.append(node)
    else:
        for child in node.children:
            append_children(msg, children, child)

class Regex:
    def __init__(self, pattern_str):
        self.pattern_str = pattern_str
        self.pattern = re.compile(pattern_str)

    def parse(self, string, pos):
        with Debug("Regex '{}' at {}", self.pattern_str, pos):
            if match := self.pattern.match(string, pos):
                return Node(match.start(), match.end(), children = [match.group(0)])

class String:
    def __init__(self, str):
        self.str = str
        self.len = len(str)

    def parse(self, string, pos):
        with Debug("String '{}' at {}", self.str, pos):
            subs = string[pos:pos+self.len]
            if subs == self.str:
                return Node(pos, pos + self.len, children = [subs])

class Seq:
    def __init__(self, *parser_names):
        self.parser_names = parser_names
        self.parsers = None

    def parse(self, string, pos):
        if not self.parsers:
            self.parsers = [get_parser(n) for n in self.parser_names]
        with Debug("Seq {}", self.parser_names):
            children = []
            end = pos
            for parser in self.parsers:
                # print('Seq', parser, parse_quiet(parser, string, end))
                if node := parser.parse(string, end):
                    append_children(self, children, node)
                    end = node.end
                else:
                    return None
            return Node(pos, end, children)

class Choice:
    def __init__(self, *parser_names):
        self.parser_names = parser_names
        self.parsers = None

    def parse(self, string, pos):
        if not self.parsers:
            self.parsers = [get_parser(n) for n in self.parser_names]
        with Debug("Choice {}", self.parser_names):
            for parser in self.parsers:
                # print('Choice', parser, parse_quiet(parser, string, pos))
                if node := parser.parse(string, pos):
                    return node

class Optional:
    def __init__(self, parser_name):
        self.parser_name = parser_name
        self.parser = None

    def parse(self, string, pos):
        if not self.parser:
            self.parser = get_parser(self.parser_name)
        with Debug("Optional {}", self.parser_name):
            return self.parser.parse(string, pos) or Node(pos, pos)

class Repeat:
    def __init__(self, parser_name):
        self.parser_name = parser_name
        self.parser = None

    def parse(self, string, pos):
        if not self.parser:
            self.parser = get_parser(self.parser_name)
        with Debug("Repeat {}", self.parser_name):
            children = []
            end = pos
            while node := self.parser.parse(string, end):
                append_children(self, children, node)
                end = node.end
            return Node(pos, end, children)

class Repeat1:
    def __init__(self, parser_name):
        self.parser_name = parser_name
        self.parser = None

    def parse(self, string, pos):
        if not self.parser:
            self.parser = get_parser(self.parser_name)
        with Debug("Repeat1 {}", self.parser_name):
            children = []
            end = pos
            while node := self.parser.parse(string, end):
                append_children(self, children, node)
                end = node.end
            if len(children) > 0:
                return Node(pos, end, children)

ws = r"\f\n\r\t, \u000B\u001C\u001D\u001E\u001F\u2028\u2029\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2008\u2009\u200a\u205f\u3000"
safe = ws + r'()\[\]{}\"@~^;`#'
parsers['_ws']      = Regex(r'[' + ws + r']+')
parsers['comment']  = Regex(r"(;|#!)[^\n]*\n?")
parsers['discard']  = Seq(Named("marker", String("#_")), Repeat('_gap'), Named(".body", '_form'))
parsers['_gap']     = Choice('_ws', 'comment', 'discard')

parsers['meta']      = Seq(Repeat1(Seq(Named(".marker", Regex(r'#?\^')),
                                       Repeat('_gap'),
                                       Named(".meta", '_form'),
                                       Repeat('_gap'))),
                           Named(".body", '_form'))

parsers['wrap']      = Seq(Named(".marker", Regex(r"(#'|@|'|`|~@|~)")),
                           Repeat('_gap'),
                           Named('.body', '_form'))

parsers['token']     = Regex(r'(##)?[^' + safe + r']+')

parsers['string']    = Seq(Named('.open', Regex(r'#?"')),
                           Named('.body', Regex(r'(\\.|[^"\\])*')),
                           Named('.close', String('"')))

parsers['brackets']  = Seq(Named('.open', String("[")),
                           Named('.body', Repeat(Choice('_gap', '_form', 'error', Named("error", Regex(r"[^\]]"))))),
                           Named('.close', String("]")))

parsers['parens']    = Seq(Named('.open', Regex(r"(#\?@|#\?|#=|#)?\(")),
                           Named(".body", Repeat(Choice('_gap', '_form', 'error', Named("error", Regex(r"[^)]"))))),
                           Named('.close', String(")")))

parsers['braces']    = Seq(Named(".open", Regex(r"(#(:[^" + safe + r"]+)?)?\{")),
                           Named(".body", Repeat(Choice('_gap', '_form', 'error', Named("error", Regex(r"[^}]"))))),
                           Named('.close', String("}")))

parsers['tagged']    = Seq(String("#"),
                           Repeat('_gap'),
                           Named('.tag', 'token'),
                           Repeat('_gap'),
                           Named('.body', '_form'))

parsers['error']     = Regex(r"[^" + ws + r"\"()\[\]{}]+")

parsers['_form']     = Choice('meta',
                              'wrap',
                              'string',
                              'brackets',
                              'parens',
                              'braces',
                              'token',
                              'tagged')

parsers['source']    = Repeat(Choice('_gap', '_form', 'error', Named('error', Regex(r'.'))))

def parse(string):
    return get_parser('source').parse(string, 0)
