#! /usr/bin/env python3
import os, sys

cwd = os.path.dirname(__file__)
os.chdir(os.path.abspath(cwd + "/.."))
sys.path.append(os.getcwd())
import cs_parser, cs_printer
import script.test_core as test_core

def test_printer():
    dir = cwd + "/../test_printer/"
    def test_fn(input):
        node = cs_parser.parse(input)
        return cs_printer.format(input, node)
    test_core.run_tests(dir, test_fn, col_input = False)

if __name__ == '__main__':
    test_printer()
