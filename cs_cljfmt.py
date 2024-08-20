import os, re, sublime, subprocess
from . import cs_common, cs_parser

def format_string(view, text):
    try:
        cmd = 'cljfmt.exe' if 'windows' == sublime.platform() else 'cljfmt'
        cwd = None
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

def indent_lines(view, selections, edit):
    regions = [region for region in selections if not region.empty()]
    if not regions:
        regions = [sublime.Region(0, view.size())]
    replacements = []
    for region in regions:
        text = view.substr(region)
        if text_formatted := format_string(view, text):
            replacements.append((region, text_formatted))

    if replacements:
        selections = [(view.rowcol(r.a), view.rowcol(r.b)) for r in selections]
        change_id_sel = view.change_id()
        for region, string in replacements:
            transformed_region = view.transform_region_from(region, change_id_sel)
            view.replace(edit, transformed_region, string)

        selections.clear()
        for ((rowa, cola), (rowb, colb)) in selections:
            a = view.text_point(rowa, cola)
            b = view.text_point(rowb, colb)
            selections.add(sublime.Region(a, b))

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
    formatted = format_string(view, text)
    last_line = formatted.splitlines()[-1]
    indent = re.match(r"^\s*", last_line)[0]
    return len(indent)
