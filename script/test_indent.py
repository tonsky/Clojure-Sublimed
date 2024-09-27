#! /usr/bin/env python3
import importlib, os, sys

dir = os.path.abspath(os.path.dirname(__file__) + "/..")
module = os.path.basename(dir)
sys.path.append(os.path.abspath(dir + "/.."))

cs_indent = importlib.import_module(module + '.cs_indent')
sublime = importlib.import_module(module + '.script.sublime')
test_core = importlib.import_module(module + '.script.test_core')

class View:
    def __init__(self, text=""):
        self.text = text

    def rowcol(self, point):
        lines = self.text[:point].split('\n')
        row = len(lines) - 1
        col = len(lines[-1]) if lines else 0
        return (row, col)

    def substr(self, region):
        return self.text[region.begin():region.end()]

    def size(self):
        return len(self.text)

    def replace(self, edit, region, new_text):
        self.text = self.text[:region.begin()] + new_text + self.text[region.end():]

    def lines(self, region):
        lines = self.text.split('\n')
        start = 0
        res = []
        for line in lines:
            if start + len(line) >= region.begin() or start < region.end():
                res.append(sublime.Region(start, start + len(line)))
            start += len(line) + 1
        return res

def test_printer():
    def test_fn(input):
        view = View(input)
        cs_indent.indent_lines(view, [sublime.Region(0, view.size())], None)
        return view.text
    test_core.run_tests(dir + "/test_indent/", test_fn, col_input = False)

if __name__ == '__main__':
    test_printer()
