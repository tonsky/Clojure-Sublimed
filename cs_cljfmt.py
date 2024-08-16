import os, sublime, subprocess

def indent_lines(view, selections, edit):
    regions = [region for region in selections if not region.empty()]
    if not regions:
      regions = [sublime.Region(0, view.size())]
    replacements = []
    for region in regions:
      text = view.substr(region)
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
        replacements.append((region, proc.stdout))

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
