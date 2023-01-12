#! /usr/bin/env python3
import os, random, re, sys, time

cwd = os.path.abspath(os.path.dirname(__file__))
os.chdir(cwd + "/../src")
sys.path.append(os.getcwd())
import clojure_parser as parser

def print_table(titles, cols):
    cols = [col.split('\n') for col in cols]
    widths = [max([len(line) for line in col] + [len(title)]) for col, title in zip(cols, titles)]
    height = max(len(col) for col in cols)
    
    print("┌", end = "")
    for i, width in enumerate(widths):
        print("".join(['─'] * (width + 2)), end = "┬" if i < len(widths) - 1 else "┐")
    print()

    print("│", end = "")
    for title, width in zip(titles, widths):
        print(" " + title.ljust(width) + " ", end = "│")
    print()

    print("├", end = "")
    for i, width in enumerate(widths):
        print("".join(['─'] * (width + 2)), end = "┼" if i < len(widths) - 1 else "┤")
    print()

    for row in range(height):
        print("│", end = "")
        for col in range(len(cols)):
            str = cols[col][row] if row < len(cols[col]) else ""
            print(" " + str.ljust(widths[col]) + " ", end = "│")
        print()

    print("└", end = "")
    for i, width in enumerate(widths):
        print("".join(['─'] * (width + 2)), end = "┴" if i < len(widths) - 1 else "┘")
    print("\n")

if __name__ == '__main__':
    dir = cwd + "/../test_parser/"
    files = [file for file in os.listdir(dir) if file.endswith(".txt")]
    width = max(len(file) for file in files)
    tests = 0
    failed = 0
    for file in files:
        with open(dir + file) as f:
            content = f.read()
        print(file.ljust(width), "[", end = "")
        failures = []
        for match in re.finditer("={80}\n(.+)\n={80}\n\n((?:.+\n)+)\n-{80}\n\n((?:.+\n)+)", content):
            tests += 1
            name = match.group(1)
            expr = match.group(2).strip('\n')
            expected = match.group(3).strip('\n')
            expected = "\n".join(line.rstrip(' ') for line in expected.split('\n'))
            parsed = parser.parse(expr)
            actual = parsed.serialize(expr)
            if parsed.end < len(expr):
                failed += 1
                print("F", end = "")
                failures.append((name, expr, "(source 0..{})".format(len(expr)), actual))
            elif actual != expected:
                failed += 1
                print("F", end = "")
                failures.append((name, expr, expected, actual))
            else:
                print(".", end = "")
            sys.stdout.flush()
        print("]")
        for (name, expr, expected, actual) in failures:
            print_table([name, "Expected", "Actual"], [expr, expected, actual])
    print("Tests: {}, failed: {}".format(tests, failed), flush=True)

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
        parsed = parser.parse(expr)
        if parsed.end < len(expr):
            failed += 1
            print(" [ FAIL ]", flush = True)
            print(parsed.serialize(expr))
            break
        else:
            print(" [ OK ] in {} ms".format((time.time() - start) * 1000), flush = True)
    print("Parsing clojure.core: {}, failed: {}".format(tests, failed), flush=True)
    
    if failed == 0:
        alphabet = r'019`~!@#$%^&*()_+-=[]{}\\|;:\'",.<>/?aAeEmMnNxXzZ '
        tests = 0
        failed = 0
        for i in range(0, 10000):
            tests += 1
            expr = "".join(random.choices(alphabet, k = random.randint(1, 50)))
            parsed = parser.parse(expr)
            # if i < 10:
            #     actual = parsed.serialize(expr)
            #     print_table(["Expr", "Actual"], ["'" + expr + "'", actual])
            if parsed.end < len(expr):
                failed += 1
                actual = parsed.serialize(expr)
                if failed == 1:
                    print_table(["Expr", "Expected", "Actual"], [expr, "(source 0..{})".format(len(expr)), actual])
        print("Randomized tests: {}, failed: {}".format(tests, failed), flush=True)

