import sublime, time, traceback

ns = 'clojure-sublimed'

def settings():
    """
    Plugin settings
    """
    return sublime.load_settings("Clojure Sublimed.sublime-settings")

def setting(key, default = None):
    """
    Shortcut to get value of a particular plugin setting
    """
    return settings().get(key, default)

def on_settings_change(tag, callback):
    """
    Subscribe to settings change
    """
    settings().add_on_change(tag, lambda: callback(settings()))
    callback(settings())

def clear_settings_change(tag):
    """
    Unsubscribe from settings change
    """
    settings().clear_on_change(tag)

def debug(format, *args):
    """
    Print to console if 'debug' is set to True. Format as in `str.format`
    """
    if setting('debug'):
        print('[ Clojure Sublimed ]', format.format(*args))

def error(format, *args):
    """
    Print error and stacktrace to console. Format as in `str.format`
    """
    print('[ Clojure Sublimed ] ERROR:', format.format(*args))
    traceback.print_exc()

class Measure:
    """
    Measure and print (if debug) execution time of with block. Format as in `str.format`
    """
    def __init__(self, format, *args):
        self.format = "{:.2f} ms " + format
        self.args = args

    def __enter__(self):
        self.time = time.time()

    def __exit__(self, exc_type, exc_value, exc_tb):
        debug(self.format, (time.time() - self.time) * 1000, *self.args)

def format_time_taken(time_taken):
    """
    Human-readable time taken (ms or sec)
    """
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

def regions_touch(r1, r2):
    """
    True iff regions intersect or touch
    """
    return r1 != None and r2 != None and not r1.end() < r2.begin() and not r1.begin() > r2.end()

def basic_styles(view):
    """
    Used to format phantoms, to achieve ~line height as in the main editor
    """
    settings = view.settings()
    top = settings.get('line_padding_top', 0)
    bottom = settings.get('line_padding_bottom', 0)
    return f"""<style>
        body {{ margin: 0 0 {top+bottom}px 0; padding: {bottom}px 1rem {top}px 1rem; }}
        p {{ margin: 0; padding: {top}px 0 {bottom}px 0; }}
    """

class SocketIO:
    """
    Simple buffered interface around socket that let you read N bytes at a time
    """
    def __init__(self, socket):
        self.socket = socket
        self.buffer = None
        self.pos = -1

    def read(self, n):
        if not self.buffer or self.pos >= len(self.buffer):
            self.buffer = self.socket.recv(4096)
            self.pos = 0
        begin = self.pos
        end = min(begin + n, len(self.buffer))
        self.pos = end
        return self.buffer[begin:end]

class Profile:
    CLOJURE = 'clojure'
    SHADOW_CLJS = 'shadow-cljs'
