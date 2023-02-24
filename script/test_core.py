import os, re, sys

def print_table(titles, cols):
    """
    Given multi-line cols, formats them nicely in a table:
    
    print_table(["Title", "Another title"], ["First row\nSecond row", "One row"])
    
    ↓
    
    ┌────────────┬───────────────┐
    │ Title      │ Another title │
    ├────────────┼───────────────┤
    │ First row  │ One row       │
    │ Second row │               │
    └────────────┴───────────────┘
    """
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

def run_tests(dir, test_fn, col_input = True):
    """
    Looks for all *.txt files in dir, parses them as `input` + `expected`,
    then compares `expected` to `test_fn(input)`. Prints errors and execution stats
    """
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
            input = match.group(2).strip('\n')
            expected = match.group(3).strip('\n')
            expected = "\n".join(line.rstrip(' ') for line in expected.split('\n'))
            actual = test_fn(input)
            if actual != expected:
                failed += 1
                print("F", end = "")
                failures.append((name, input, expected, actual))
            else:
                print(".", end = "")
            sys.stdout.flush()
        print("]")
        for (name, input, expected, actual) in failures:
            if col_input:
                print_table([name, "Expected", "Actual"], [input, expected, actual])
            else:
                print_table([name + ": Expected", "Actual"], [expected, actual])
    print("Tests: {}, failed: {}\n".format(tests, failed), flush=True)
