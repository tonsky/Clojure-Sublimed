#! /usr/bin/env python3
import os, random, re, sys, time

cwd = os.path.abspath(os.path.dirname(__file__))
os.chdir(cwd + "/../src")
sys.path.append(os.getcwd())
import clojure_parser as parser

if __name__ == '__main__':
    start = time.time()
    dir = cwd + "/../test_parser/"
    with open(dir + 'core.clj') as f:
        expr = f.read()
    parsed = parser.parse(expr)
    print("Parsed {}..{} in {} ms". format(parsed.start, parsed.end, (time.time() - start) * 1000))
