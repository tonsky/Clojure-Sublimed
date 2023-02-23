def safe_get(l, i, default = None):
    """
    Like dict.get(), but for lists
    """
    if i < len(l):
        return l[i]
    else:
        return default

def right_boundary(indent, s):
    """
    Given (potentially) multiline s, figures out max right offset,
    considering it starts at `indent`
    """
    if '\n' in s:
        return max(len(line) for line in s.split('\n'))
    else:
        return len(indent) + len(s)

def end_offset(indent, s):
    """
    Given (potentially) multiline s, figures out where end index will be,
    considering it starts at `indent`
    """
    if '\n' in s:
        return len(s.split('\n')[-1])
    else:
        return len(indent) + len(s)

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
            vs = format(text, v, indent_vals, limit)
            if right_boundary(indent_vals, vs) <= limit:
                res += (longest_key - len(ks)) * ' ' + ' ' + vs
            else:
                indent = indent_keys + len(ks) * ' ' + ' '
                vs = format(text, v, indent, limit)
                if right_boundary(indent, vs) <= limit:
                    res += ' ' + vs
                else:
                    vs = format(text, v, indent_keys, limit)
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
    if node.body:
        offset = len(indent_children)
        for i, child in enumerate(node.body.children):
            separator = 0
            if i > 0 and offset > len(indent_children):
                offset += 1
                separator = 1
            indent_child = offset * ' '
            child_str = format(text, child, indent_child, limit)
            if right_boundary(indent_child, child_str) <= limit:
                res += separator * ' '
                res += child_str
                offset = end_offset(indent_child, child_str)
            else:
                child_str = format(text, child, indent_children, limit)
                res += '\n' + indent_children + child_str
                offset = end_offset(indent_children, child_str)
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
        return text[node.start:node.end]
