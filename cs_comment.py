import re
import  sublime, sublime_plugin
from . import cs_parser

def search_point(node, pos):
    # no children
    if node.nested() is None:
        if node.start <= pos and pos <= node.end:
            return node
        else:
            return None

    # uncomment
    if node.is_terminal() and node.start <= pos and pos <= node.end:
        return node

    prev_child = None
    res = None
    for child in node.nested():
        # has children: between two (() () | ())
        # has children: before first ( | () () ())
        if child.start > pos:
            res = prev_child
            break

        # has children: at the start (() |() ())
        # has children: inside one (() (|) ())
        # has children: at the end (() ()| ())
        if child.start <= pos and pos <= child.end:
            res = search_point(child, pos)
            break

        prev_child = child

    if res:
        return res

    if node.start <= pos and pos <= node.end:
        return node

def search_range(node, start, end):
    if node.nested() is not None and node.start <= start and end <= node.end:
        if start <= node.start and node.end <= end:
            return [node]
        res = []
        for child in node.nested():
            if child.nested() is not None and child.start <= start and end <= child.end:
                return search_range(child, start, end)
            # (...)...[...] - no
            # (...[...)...]
            # [...(...)...]
            # [...(...]...)
            # [...]...(...) - no
            # (...[...]...)
            elif not child.end <= start and not child.start >= end:
                res.append(child)
        return res or [node]

class ClojureSublimedToggleCommentCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        parsed = cs_parser.parse_tree(view)
        sel = []
        offset = 0
        regions = [r for r in view.sel()]
        regions.sort(key = lambda r: r.begin())
        for region in regions:
            if region.empty():
                nodes = [search_point(parsed, region.begin())]
            else:
                nodes = search_range(parsed, region.begin(), region.end())
            a = region.a + offset
            b = region.b + offset
            if all(node.name == "comment" for node in nodes):
                # uncomment line comments
                for node in nodes:
                    m = re.match(r'^;+\s*', node.text)
                    r = sublime.Region(node.start + offset, node.start + offset + len(m[0]))
                    view.replace(edit, r, "")
                    a = a if a < r.begin() else r.begin() if a < r.end() else a - r.size()
                    b = b if b < r.begin() else r.begin() if b < r.end() else b - r.size()
                    offset -= r.size()
            elif all(node.name in ["discard", "comment"] for node in nodes):
                # uncomment discards only
                for node in nodes:
                    if node.name == "discard":
                        r = sublime.Region(node.start + offset, node.body.start + offset)
                        view.replace(edit, r, "")
                        a = a if a < r.begin() else r.begin() if a < r.end() else a - r.size()
                        b = b if b < r.begin() else r.begin() if b < r.end() else b - r.size()
                        offset -= r.size()
            else:
                for node in nodes:
                    if node.name not in ["discard", "comment"]:
                        # comment
                        r = sublime.Region(node.start + offset, node.start + offset)
                        view.replace(edit, r, "#_")
                        a = a if a < r.begin() else a + 2
                        b = b if b < r.begin() else b + 2
                        offset += 2
            sel.append(sublime.Region(a, b))
        view.sel().clear()
        view.sel().add_all(sel)
