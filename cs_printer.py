import re

def safe_get(l, i, default = None):
    """
    Like dict.get(), but for lists
    """
    if i < len(l):
        return l[i]
    else:
        return default

def format_map(text, node, indent, limit):
    """
    Puts key-value pairs on separate line each. Aligns keys by longest one:
    {:a 1 :bbb 2 :cc 3} => {:a   1
                            :bbb 2
                            :cc  3}
    """
    res = node.open.text
    indent_keys = indent + len(node.open.text) * ' '
    keys = []
    vals = []
    if node.body:
        idxs = range(0, len(node.body.children), 2)
        keys = [node.body.children[i] for i in idxs]
        vals = [safe_get(node.body.children, i + 1) for i in idxs]
    key_strings = [format(text, k, indent_keys, limit) for k in keys]
    longest_key = max(len(ks) for ks in key_strings) if key_strings else 0
    indent_vals = indent_keys + longest_key * ' ' + ' '
    for i, ks, v in zip(range(0, len(keys)), key_strings, vals):
        if i > 0:
            res += '\n' + indent_keys
        res += ks
        if v is not None:
            vs = format(text, v, indent_keys, limit)
            if '\n' in vs:
                res += '\n' + indent_keys + vs
            elif len(indent_keys) + longest_key + 1 + len(vs) <= limit:
                res += (longest_key - len(ks)) * ' ' + ' ' + vs
            elif len(indent_keys) + len(ks) + 1 + len(vs) <= limit:
                res += ' ' + vs
            else:
                res += '\n' + indent_keys + vs
    if node.close:
        res += node.close.text
    return res

def format_list(text, node, indent, limit):
    """
    Everythin list-like: (...), [...], #{...}
    Puts as many children as it can on a line, then starts new one.
    """
    indent_children = indent + (len(node.open.text) * ' ')
    res = node.open.text
    force_newline = False
    is_first = True
    if node.body:
        for i, child in enumerate(node.body.children):
            if force_newline:
                res += '\n' + indent_children
                is_first = True
            
            child_str = format(text, child, indent_children, limit)
            if '\n' in child_str or child.name in {'brackets', 'parens', 'braces'} or len(child_str) > limit / 3:
                if not is_first:
                    res += '\n' + indent_children
                res += child_str
                force_newline = True
                is_first = True
                continue
            last_line = res[res.rfind('\n') + 1:]
            separator = '' if is_first else ' '
            if len(last_line) + len(separator) + len(child_str) > limit:
                res += '\n' + indent_children + child_str
            else:
                res += separator + child_str
            force_newline = False
            is_first = False
    close = node.close.text if node.close else ''
    res += close
    return res

def format_tagged(text, node, indent, limit):
    """
    #tag <some_value>
    """
    tag_string = format(text, node.tag, indent, limit)
    res = '#' + tag_string
    if node.body:
        value_indent = indent + ' ' + len(tag_string) * ' ' + ' '
        res += ' ' + format(text, node.body.children[0], value_indent, limit)
    return res

def wrap_string(s, limit = 80, indent = ''):
    space = limit - len(indent)
    length = len(s)
    if length <= space:
        return s
    if space < 10:
        return s
    res = ""
    for start in range(0, length, space):
        end = min(start + space, length)
        if start > 0:
            res += '\n' + indent
        res += s[start:end]
    return res

def format(text, node, indent = '', limit = 80):
    """
    Given text and its parsed AST as node, returns formatted (pretty-printed) string of that node
    """
    if node.name == 'source':
        return '\n'.join(format(text, n, '', limit) for n in node.children)
    elif node.name == 'braces' and node.open.text != '#{':
        return format_map(text, node, indent, limit)
    elif node.name in {'parens', 'brackets', 'braces'}:
        return format_list(text, node, indent, limit)
    elif node.name == 'tagged':
        return format_tagged(text, node, indent, limit)
    else:
        str = text[node.start:node.end]
        str = re.sub("(?<!\\\\)\\\\n", "\n", str)
        str = "\n".join(wrap_string(s, limit = limit, indent = indent) for s in str.split("\n"))
        return str
