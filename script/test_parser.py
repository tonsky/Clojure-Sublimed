#! /usr/bin/env python3
import os, random, sys, time

cwd = os.path.dirname(__file__)
os.chdir(os.path.abspath(cwd + "/.."))
sys.path.append(os.getcwd())
import cs_parser
import script.test_core as test_core

def test_parse_trees():
    dir = cwd + "/../test_parser/"
    def test_fn(input):
        return str(cs_parser.parse(input))
    test_core.run_tests(dir, test_fn)

def test_clojure():
    dir = cwd + "/../test_parser/"
    files = [file for file in os.listdir(dir) if file.endswith(".clj")]
    width = max(len(file) for file in files)
    tests = 0
    failed = 0
    for file in files:
        with open(dir + file) as f:
            expr = f.read()
        print(file.ljust(width), end = "", flush = True)
        tests += 1
        start = time.time()
        parsed = cs_parser.parse(expr)
        if parsed.end < len(expr):
            failed += 1
            print(" [ FAIL ]", flush = True)
            print(str(parsed))
            break
        else:
            print(" [ OK ] in {} ms".format((time.time() - start) * 1000), flush = True)
    print("Parsing *.clj: {}, failed: {}\n".format(tests, failed), flush=True)
    
def test_random():
    alphabet = r'019`~!@#$%^&*()_+-=[]{}\\|;:\'",.<>/?aAeEmMnNxXzZ '
    tests = 0
    failed = 0
    for i in range(0, 10000):
        tests += 1
        expr = "".join(random.choices(alphabet, k = random.randint(1, 50)))
        parsed = cs_parser.parse(expr)
        # if i < 10:
        #     actual = str(parsed)
        #     test_core.print_table(["Expr", "Actual"], ["'" + expr + "'", actual])
        if parsed.end < len(expr):
            failed += 1
            actual = str(parsed)
            if failed == 1:
                test_core.print_table(["Expr", "Expected", "Actual"], [expr, "(source 0..{})".format(len(expr)), actual])
    print("Randomized tests: {}, failed: {}\n".format(tests, failed), flush=True)

if __name__ == '__main__':
    test_parse_trees()
    test_clojure()
    test_random()
