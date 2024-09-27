#! /usr/bin/env python3
import importlib, os, sys

dir = os.path.abspath(os.path.dirname(__file__) + "/..")
module = os.path.basename(dir)
sys.path.append(os.path.abspath(dir + "/.."))

cs_cljfmt = importlib.import_module(module + '.cs_cljfmt')
sublime = importlib.import_module(module + '.script.sublime')
test_core = importlib.import_module(module + '.script.test_core')

def test_printer():
    def test_fn(input):
        return cs_cljfmt.format_string(input, cwd = dir)
    test_core.run_tests(dir + "/test_indent/", test_fn, col_input = False)

if __name__ == '__main__':
    test_printer()
