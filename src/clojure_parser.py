import re

DEBUG = False
INDENT = ""

class Debug:
    def __init__(self, name):
        self.name = name

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
        with Debug("Named '{}' at {}".format(self.name, pos)):
            node = self.parser.parse(string, pos)
            if not node:
                return None
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
    elif node.name: # and not node.name[0] == "_":
        children.append(node)
    else:
        for child in node.children:
            append_children(msg, children, child)

class Regex:
    def __init__(self, pattern_str):
        self.pattern_str = pattern_str
        self.pattern = re.compile(pattern_str)

    def parse(self, string, pos):
        with Debug("Regex '{}' at {}".format(self.pattern_str, pos)):
            if match := self.pattern.match(string, pos):
                return Node(match.start(), match.end(), children = [match.group(0)])

class String:
    def __init__(self, str):
        self.str = str
        self.len = len(str)

    def parse(self, string, pos):
        with Debug("String '{}' at {}".format(self.str, pos)):
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
        with Debug("Seq {}".format(self.parser_names)):
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
        with Debug("Choice {}".format(self.parser_names)):
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
        with Debug("Optional {}".format(self.parser_name)):
            return self.parser.parse(string, pos) or Node(pos, pos)

class Repeat:
    def __init__(self, parser_name):
        self.parser_name = parser_name
        self.parser = None

    def parse(self, string, pos):
        if not self.parser:
            self.parser = get_parser(self.parser_name)
        with Debug("Repeat {}".format(self.parser_name)):
            children = []
            end = pos
            while node := self.parser.parse(string, end):
                append_children(self, children, node)
                end = node.end
            return Node(pos, end, children)

# Whitespace
parsers['_ws']      = Regex(r"[\f\n\r\t, \u000B\u001C\u001D\u001E\u001F\u2028\u2029\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2008\u2009\u200a\u205f\u3000]+")
parsers['comment']  = Regex(r"(;|#!)[^\n]*\n?")
parsers['dis_expr'] = Seq(String("#_"), Repeat('_gap'), '_form')
parsers['_gap']     = Choice('_ws', 'comment', 'dis_expr')

# Numbers
num_hex             = Regex(r"0[xX][0-9a-fA-F]+N?")
num_octal           = Regex(r"0[0-7]+N?")
num_radix           = Regex(r"[0-9]+[rR][0-9a-zA-Z]+")
num_ratio           = Regex(r"[0-9]+/[0-9]+")
num_double          = Regex(r"[0-9]+(\.[0-9]*[eE][+-]?[0-9]+|\.[0-9]*|[eE][+-]?[0-9]+)M?")
num_int             = Regex(r"[0-9]+[MN]?")
parsers['num_lit']  = Seq(Optional(Regex(r"[+-]")), Choice(num_hex, num_octal, num_radix, num_ratio, num_double, num_int))

# Symbols
sym_head = r"[^\f\n\r\t \/()\[\]{}\"@~^;`\\,:#'0-9\u000B\u001C\u001D\u001E\u001F\u2028\u2029\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2008\u2009\u200a\u205f\u3000]"
sym_body = r"[^\f\n\r\t \/()\[\]{}\"@~^;`\\,\u000B\u001C\u001D\u001E\u001F\u2028\u2029\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2008\u2009\u200a\u205f\u3000]*" # allow :#'0-9
sym_ns_name = r"[^\f\n\r\t ()\[\]{}\"@~^;`\\,\u000B\u001C\u001D\u001E\u001F\u2028\u2029\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2008\u2009\u200a\u205f\u3000]+" # allow :#'0-9/

parsers['_sym_slash']       = Named('sym_name', String("/"))
parsers['_sym_unqualified'] = Named('sym_name', Regex(sym_head + sym_body))
parsers['_sym_qualified']   = Seq(Named('sym_ns', Regex(sym_head + sym_body)), String("/"), Named('sym_name', Regex(sym_ns_name)))
parsers['sym_lit'] = Choice('_sym_slash', "_sym_qualified", "_sym_unqualified")

# Keywords
kwd_head = r"[^\f\n\r\t ()\[\]{}\"@~^;`\\,:/\u000B\u001C\u001D\u001E\u001F\u2028\u2029\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2008\u2009\u200a\u205f\u3000]"
kwd_body = r"[^\f\n\r\t ()\[\]{}\"@~^;`\\,/\u000B\u001C\u001D\u001E\u001F\u2028\u2029\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2008\u2009\u200a\u205f\u3000]*" # allow :
kwd_ns_name = r"[^\f\n\r\t ()\[\]{}\"@~^;`\\,\u000B\u001C\u001D\u001E\u001F\u2028\u2029\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2008\u2009\u200a\u205f\u3000]+" # allow :/

parsers['_kwd_leading_slash'] = Seq(String("/"), Named('kwd_name', Regex(kwd_ns_name)))
parsers['_kwd_just_slash']    = Named('kwd_name', String("/"))
parsers['_kwd_unqualified']   = Named('kwd_name', Regex(kwd_head + kwd_body))
parsers['_kwd_qualified']     = Seq(Named('kwd_ns', Regex(kwd_head + kwd_body)), String("/"), Named('kwd_name', Regex(kwd_ns_name)))
parsers['kwd_lit'] = Seq(Named("kwd_marker", Regex("::?")), Choice('_kwd_leading_slash', '_kwd_just_slash', "_kwd_qualified", "_kwd_unqualified"))

# Strings
parsers['str_lit']   = Regex(r'"(\\.|[^"\\])*"')
parsers['regex_lit'] = Regex(r'#"(\\.|[^"\\])*"')

# Brackets
parsers['vec_lit']   = Seq(String("["), Repeat(Choice('_gap', '_form')), String("]"))
parsers['parens']    = Seq(Regex(r"(#\?@|#\?|#=|#)?\("), Repeat(Choice('_gap', '_form')), String(")"))
parsers['braces']    = Seq(Regex(r"#?\{"), Repeat(Choice('_gap', '_form')), String("}"))

# Forms
parsers['_form']     = Choice('num_lit', 'regex_lit', 'str_lit', 'kwd_lit', 'sym_lit', 'vec_lit', 'parens', 'braces')
parsers['source']    = Repeat(Choice('_gap', '_form'))

def parse(string):
    return get_parser('source').parse(string, 0)
