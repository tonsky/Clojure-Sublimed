import logging, time

try:
    import sublime
except:
    pass

_log = logging.getLogger(__name__)

def region(begin, end = None):
    return sublime.Region(begin, end or begin)

def settings():
    return sublime.load_settings("Clojure Sublimed.sublime-settings")

def setting(key, default = None):
    return settings().get(key, default)

class Measure:
    def __init__(self, format, *args):
        self.format = "%.2f ms " + format
        self.args = args

    def __enter__(self):
        self.time = time.time()

    def __exit__(self, exc_type, exc_value, exc_tb):
        _log.debug(self.format, (time.time() - self.time) * 1000, *self.args)

def format_time_taken(time_taken):
    threshold = setting("elapsed_threshold_ms")
    if threshold != None and time_taken != None:
        elapsed = time_taken / 1000000000
        if elapsed * 1000 >= threshold:
            if elapsed >= 10:
                return f"({'{:,.0f}'.format(elapsed)} sec)"
            elif elapsed >= 1:
                return f"({'{:.1f}'.format(elapsed)} sec)"
            elif elapsed >= 0.005:
                return f"({'{:.0f}'.format(elapsed * 1000)} ms)"
            else:
                return f"({'{:.2f}'.format(elapsed * 1000)} ms)"
