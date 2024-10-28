#! /usr/bin/env python3
import importlib, os, sys

dir = os.path.abspath(os.path.dirname(__file__) + "/..")
module = os.path.basename(dir)
sys.path.append(os.path.abspath(dir + "/.."))

cs_comment = importlib.import_module(module + '.cs_comment')
cs_parser = importlib.import_module(module + '.cs_parser')
sublime = importlib.import_module(module + '.script.sublime')
test_core = importlib.import_module(module + '.script.test_core')

def gen_test_case_reversible(name, input, expected):
    return [(name, input, expected),
            (name + " (reversed)", expected, input)]

def find_one(str, substrs, start):
    res = -1
    for substr in substrs:
        pos = str.find(substr, start)
        if pos != -1 and (res == -1 or pos < res):
            res = pos
    return res

def test_fn(input):
    # parse input
    text = ""
    sel = []
    pos = 0
    cnt = 0
    while True:
        pos2 = find_one(input, ["|", "→"], pos)
        if pos2 == -1:
            text = text + input[pos:]
            break
        elif input[pos2] == "|":
            sel.append(sublime.Region(pos2 - cnt, pos2 - cnt))
            text = text + input[pos:pos2]
            pos = pos2 + 1
            cnt += 1
        elif input[pos2] == "→":
            pos3 = find_one(input, ["←"], pos2 + 1)
            sel.append(sublime.Region(pos2 - cnt, pos3 - cnt - 1))
            text = text + input[pos:pos2] + input [pos2 + 1:pos3]
            pos = pos3 + 1
            cnt += 2
    if not sel:
        raise Exception("No selection")

    # run command
    view = sublime.View(text, sel)
    cmd = cs_comment.ClojureSublimedToggleCommentCommand(view)
    cmd.run(None)

    # format output
    text = ""
    pos = 0
    for r in view.sel():
        if r.empty():
            text = text + view.text[pos:r.begin()]
            text = text + "|"
            pos = r.begin()
        else:
            text = text + view.text[pos:r.begin()]
            text = text + "→"
            text = text + view.text[r.begin():r.end()]
            text = text + "←"
            pos = r.end()
    text = text + view.text[pos:]

    return text

if __name__ == '__main__':
    test_core.run_tests(dir + "/test_comment/comment.txt", test_fn)
    test_core.run_tests(dir + "/test_comment/comment_reversible.txt", test_fn, gen_test_case = gen_test_case_reversible)
