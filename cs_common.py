import time

try:
    import sublime
except:
    pass

def region(begin, end = None):
    return sublime.Region(begin, end or begin)

def settings():
    return sublime.load_settings("Clojure Sublimed.sublime-settings")

def setting(key, default = None):
    return settings().get(key, default)

class Measure:
    def __init__(self, format, *args):
        self.format = format
        self.args = args

    def __enter__(self):
        self.time = time.time()

    def __exit__(self, exc_type, exc_value, exc_tb):
        print("[ {:.2f} ms ]".format((time.time() - self.time) * 1000), self.format.format(*self.args))

