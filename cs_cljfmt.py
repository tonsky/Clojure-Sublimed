import difflib, os, re, sublime, subprocess
from . import cs_common, cs_parser

def format_string(text, view = None, cwd = None):
    try:
        cmd = 'cljfmt.exe' if 'windows' == sublime.platform() else 'cljfmt'
        if not cwd:
            if file := view.file_name():
                cwd = os.path.dirname(file)
            elif folders := view.window().folders():
                cwd = folders[0]

        proc = subprocess.run([cmd, 'fix', '-'],
                 input = text,
                 text = True,
                 capture_output = True,
                 check = True,
                 cwd = cwd)
    except FileNotFoundError:
        sublime.error_message(f'`{cmd}` is not on $PATH')
        raise
    if 'Failed' not in proc.stderr:
        return proc.stdout

def indent_lines(view, regions, edit):
    regions = [region for region in regions if not region.empty()]
    if not regions:
        regions = [sublime.Region(0, view.size())]
    replacements = []
    for region in regions:
        text = view.substr(region)
        if text_formatted := format_string(text, view = view):
            pos = region.begin()
            diff = difflib.ndiff(text.splitlines(keepends=True), text_formatted.splitlines(keepends=True))
            for line in diff:
                if line[:2] == '- ':
                    replacements.append((sublime.Region(pos, pos + len(line) - 2), ''))
                    pos = pos + len(line) - 2
                elif line[:2] == '+ ':
                    replacements.append((sublime.Region(pos, pos), line[2:]))
                elif line[:2] == '  ':
                    pos = pos + len(line) - 2
                elif line[:2] == '? ':
                    pass
    if replacements:
        selections_before = [(view.rowcol(r.a), view.rowcol(r.b)) for r in view.sel()]
        delta = 0
        for region, string in replacements:
            transformed_region = sublime.Region(region.a + delta, region.b + delta)
            view.replace(edit, transformed_region, string)
            delta = delta - region.size() + len(string)

        view.sel().clear()
        for ((rowa, cola), (rowb, colb)) in selections_before:
            a = view.text_point(rowa, cola)
            b = view.text_point(rowb, colb)
            view.sel().add(sublime.Region(a, b))

def newline_indent(view, point):
    text = view.substr(sublime.Region(0, point))
    parsed = cs_parser.parse(text)
    to_close = []
    node = parsed
    start = node.children[-1].start if node.children else 0
    while node:
        if 'string' == node.name and node.open and not node.close:
            to_close.insert(0, '"')
        elif 'parens' == node.name and node.open and not node.close:
            to_close.insert(0, ')')
        elif 'braces' == node.name and node.open and not node.close:
            to_close.insert(0, '}')
        elif 'brackets' == node.name and node.open and not node.close:
            to_close.insert(0, ']')
        node = node.children[-1] if node.children else None
    if to_close and '"' == to_close[0]:
        return None
    text = text[start:] + "\nCLOJURE_SUBLIMED_SYM" + "".join(to_close)
    formatted = format_string(text, view = view)
    last_line = formatted.splitlines()[-1]
    indent = re.match(r"^\s*", last_line)[0]
    return len(indent)
