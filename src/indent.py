import sublime
from . import clojure_parser

def search_path(node, pos):
    res = [node]
    for child in node.children:
        if child.start < pos < child.end:
            res += search_path(child, pos)
        elif pos < child.start:
            break
    return res

def indent(view, point):
    parsed = clojure_parser.parse_tree(view)
    if path := search_path(parsed, point):
        node = None
        first_form = None

        # try finding unmatched open paren
        for child in path[-1].children:
            if child.start >= point:
                break
            if child.name == 'error' and child.text in ['(', '[', '{', '"']:
                node = child
                first_form = None
            elif first_form is None:
                first_form = child

        # try indent relative to wrapping paren
        if not node:
            for n in reversed(path):
                if n.name in ['string', 'parens', 'braces', 'brackets']:
                    node = n
                    first_form = node.body.children[0] if node.body and node.body.children else None
                    break

        # top level
        if not node:
            row, _ = view.rowcol(point)
            return ('top-level', row, 0)

        row, col = view.rowcol(node.open.end if node.open else node.end)
        offset = 0
        if node.name == 'string':
            return ('string', row, col)
        elif node.name == 'parens' or (node.name == 'error' and node.text == '('):
            if not first_form:
                offset = 0
            elif first_form.end <= point and first_form.name in ['parens', 'braces', 'brackets']:
                offset = 0
            else:
                offset = 1
        return ('indent', row, col + offset)

def skip_spaces(view, point):
    def is_space(point):
        s = view.substr(sublime.Region(point, point + 1))
        return s.isspace() and s not in ['\n', '\r']    
    while point < view.size() and is_space(point):
        point = point + 1
    return point

def insert_newline(view, edit):
    change_id_sel = view.change_id()
    replacements = []
    for sel in view.sel():
        end = skip_spaces(view, sel.end())
        _, _, i = indent(view, sel.begin())
        replacements.append((sublime.Region(sel.begin(), end), "\n" + " " * i))

    view.sel().clear()
    for region, string in replacements:
        region = view.transform_region_from(region, change_id_sel)
        point = region.begin() + len(string)
        view.replace(edit, region, string)
        view.sel().add(sublime.Region(point, point))

def indent_lines(view, selections, edit):
    change_id = view.change_id()
    replacements = {} # row -> (begin, delta_i)
    for sel in selections:
        for line in view.lines(sel):
            begin  = line.begin()
            end    = skip_spaces(view, begin)
            if end == line.end(): # do not touch empty lines
                continue
            row, _ = view.rowcol(begin)
            type, base_row, i = indent(view, begin)
            if type == 'string': # do not re-indent multiline strings
                continue
            _, base_delta_i = replacements.get(base_row, (0, 0))
            delta_i = i - (end - begin) + base_delta_i
            if delta_i != 0:
                replacements[row] = (begin, delta_i)
    for row in replacements:
        begin, delta_i = replacements[row]
        begin = view.transform_region_from(sublime.Region(begin, begin), change_id).begin()
        if delta_i < 0:
            view.replace(edit, sublime.Region(begin, begin - delta_i), "")
        else:
            view.replace(edit, sublime.Region(begin, begin), " " * delta_i)
