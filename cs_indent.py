import re
import sublime, sublime_plugin
from . import cs_cljfmt, cs_common, cs_parser, cs_printer

def search_path(node, pos):
    """
    Looks for the deepest node that wraps pos (start < pos < end).
    Returns full path to that node from the top
    """
    res = [node]
    for child in node.children:
        if child.start < pos < child.end:
            res += search_path(child, pos)
        elif pos < child.start:
            break
    return res

def indent(view, point, parsed = None):
    """
    Given point, returns (tag, row, indent) for that line, where indent
    is a correct indent based on the last unclosed paren before point.

    Tag could be 'string' (don't change anything, we're inside string),
    'top-level' (set to 0, we are at top level) or 'indent' (normal behaviour)

    Row is row number of the token for which this indent is based on (row of open paren)
    """
    parsed = parsed or cs_parser.parse(view.substr(sublime.Region(0, point)) + ' ')
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
            if first_form and cs_parser.is_symbol(first_form):
                offset = 1
            else:
                offset = 0
        return ('indent', row, col + offset)

def newline_indent(view, point):
    return indent(view, point)[2]

def skip_spaces(view, point):
    """
    Starting from point, skips as much spaces as it can without going to the new line,
    and returns new point
    """
    def is_space(point):
        s = view.substr(sublime.Region(point, point + 1))
        return s.isspace() and s not in ['\n', '\r']    
    while point < view.size() and is_space(point):
        point = point + 1
    return point

def indent_lines(view, selections, edit):
    """
    Given set of sorted ranges (`selections`), indents all lines touched by those selections
    """
    # Calculate all replacements first
    parsed = cs_parser.parse(view.substr(sublime.Region(0, view.size())) + ' ')
    replacements = {} # row -> (begin, delta_i)
    for sel in selections:
        for line in view.lines(sel):
            begin = line.begin()
            end   = skip_spaces(view, begin)
            # do not touch empty lines
            if end == line.end():
                continue
            row, _ = view.rowcol(begin)
            type, base_row, i = indent(view, begin, parsed)
            # do not re-indent multiline strings
            if type == 'string':
                continue
            # if we moved line before and depend on it, take that into account
            _, base_delta_i = replacements.get(base_row, (0, 0))
            delta_i = i - (end - begin) + base_delta_i
            if delta_i != 0:
                replacements[row] = (begin, delta_i)

    # Now apply all replacements, recalculating begins as we go
    delta_total = 0
    for row in replacements:
        begin, delta_i = replacements[row]
        begin = begin + delta_total
        delta_total += delta_i
        if delta_i < 0:
            view.replace(edit, sublime.Region(begin, begin - delta_i), "")
        else:
            view.replace(edit, sublime.Region(begin, begin), " " * delta_i)

class ClojureSublimedReindentBufferOnSave(sublime_plugin.EventListener):
    def on_pre_save(self, view):
        if cs_common.setting("format_on_save", False) and ('Clojure' in view.syntax().name or 'EDN' in view.syntax().name):
            view.run_command('clojure_sublimed_reindent_buffer')

class ClojureSublimedReindentBufferCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        with cs_common.Measure("Reindent Buffer {} chars", view.size()):
            if 'cljfmt' == cs_common.setting('formatter'):
                cs_cljfmt.indent_lines(view, [sublime.Region(0, view.size())], edit)
            else:
                indent_lines(view, [sublime.Region(0, view.size())], edit)

class ClojureSublimedReindentLinesCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        with cs_common.Measure("Reindent Lines {} chars", sum([r.size() for r in view.sel()])):
            if 'cljfmt' == cs_common.setting('formatter'):
                cs_cljfmt.indent_lines(view, view.sel(), edit)
            else:
                indent_lines(view, view.sel(), edit)

class ClojureSublimedReindentCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        if all(r.empty() for r in view.sel()):
            view.run_command('clojure_sublimed_reindent_buffer')
        else:
            view.run_command('clojure_sublimed_reindent_lines')

class ClojureSublimedPrettyPrintCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        change_id = view.change_id()
        for region in [r for r in view.sel()]:
            region = view.transform_region_from(region, change_id)
            if region.empty():
                region = cs_parser.topmost_form(view, region.begin())
            form = view.substr(region)
            node = cs_parser.parse(form)
            formatted = cs_printer.format(form, node, limit = cs_common.wrap_width(view))
            view.replace(edit, region, formatted)

class ClojureSublimedSelectTopmostFormCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        sel = view.sel()
        for region in [r for r in sel]:
            sel.add(cs_parser.topmost_form(view, region.begin()))

def cljfmt_indent(view, point):
    i = None
    try:
        i = cs_cljfmt.newline_indent(view, point)
    except:
        pass
    return newline_indent(view, point) if i is None else i

class ClojureSublimedInsertNewlineCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        newline_indent_fn = cljfmt_indent if 'cljfmt' == cs_common.setting('formatter') else newline_indent
        
        # Calculate all replacements first
        replacements = []
        for sel in view.sel():
            end = skip_spaces(view, sel.end())
            i = newline_indent_fn(view, sel.begin())
            replacements.append((sublime.Region(sel.begin(), end), "\n" + " " * i))

        # Now apply them all at once
        change_id_sel = view.change_id()
        view.sel().clear()
        for region, string in replacements:
            region = view.transform_region_from(region, change_id_sel)
            point = region.begin() + len(string)
            view.replace(edit, region, string)
            # Add selection at the end of newly inserted region
            view.sel().add(sublime.Region(point, point))
