#! /usr/bin/env python3
import importlib, os, sys

dir = os.path.abspath(os.path.dirname(__file__) + "/..")
module = os.path.basename(dir)
sys.path.append(os.path.abspath(dir + "/.."))

cs_indent = importlib.import_module(module + '.cs_indent')
sublime = importlib.import_module(module + '.script.sublime')
test_core = importlib.import_module(module + '.script.test_core')

def test():
    def test_fn(input):
        view = sublime.View(input)
        cs_indent.indent_lines(view, [sublime.Region(0, view.size())], None)
        return view.text
    test_core.run_tests(dir + "/test_indent/", test_fn, col_input = False)

def bench():
    import time
    start_time = time.time()
    with open("/Users/tonsky/work/core.clj") as f:
        content = f.read()
    view = sublime.View(content)
    cs_indent.indent_lines(view, [sublime.Region(0, view.size())], None)
    end_time = time.time()
    print(f"Execution time: {end_time - start_time} seconds")

if __name__ == '__main__':
    test()
