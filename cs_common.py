import collections, math, os, re, socket, sublime, sublime_plugin, time, traceback

ns = 'clojure-sublimed'

package = None

class State:
  def __init__(self):
    self.statuses    = {}
    self.last_view   = None
    self.conn        = None
    self.last_conn   = None
    self.warnings    = 0
    self.status_eval = None

states = collections.defaultdict(lambda: State())

def get_state(window = None):
    if window is None:
        window = sublime.active_window()
    return states[window.id()]

class Form:
    def __init__(self, id = None, code = None, ns = 'user', line = None, column = None, file = None):
        self.id     = id
        self.code   = code
        self.ns     = ns
        self.line   = line
        self.column = column
        self.file   = file

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

def wrap_width(view):
    if (w := setting('wrap_width')):
        return w
    if not view:
        return 80
    return math.floor(view.viewport_extent()[0] / view.em_width()) - 3

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
        elapsed = time_taken / 1000
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
        body {{ margin: 0 0 {top+bottom}px 0; padding: {bottom}px 0 {top}px 0; }}
        p {{ margin: 0; padding: {top}px 0 {bottom}px 0; }}
    """

def clojure_source(file):
    file = sublime.load_resource(f'Packages/{package}/src_clojure/clojure_sublimed/' + file)
    return re.sub(r'(?m)^\s+', '', file).strip() + '\n'

def active_view():
    if window := sublime.active_window():
        return window.active_view()

def get_default(d, k, default):
    v = d.get(k, None)
    return v if v is not None else default

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

def socket_connect(addr):
    if match := re.fullmatch(r'\s*([^:]+):(\d+)\s*', addr):
        host, port = match.groups()
        port = int(port)
        return socket.create_connection((host, port))
    else: # path == unix domain socket
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(addr)
        return s

def set_status(window, key, value):
    """
    Sets persistent status that will travel when changing views.
    Pass value = None to erase
    """
    state = get_state(window)
    if view := active_view():
        if value is None:
            view.erase_status(key)
        else:
            view.set_status(key, value)
        state.statuses[key] = value
        if not state.last_view:
            state.last_view = view

class EventListener(sublime_plugin.EventListener):
    def on_activated_async(self, view):
        """
        When swithing to another view
        """
        state = get_state(view.window())
        global statuses, last_view
        if view != state.last_view:
            for key in state.statuses:
                state.last_view.erase_status(key)
                if (value := state.statuses.get(key)) is not None:
                    view.set_status(key, value)
            state.last_view = view

    def on_pre_close_window(self, window):
        state = get_state(window)
        if state.conn:
            state.conn.disconnect()
        del states[window.id()]

def plugin_loaded():
    global package
    package_path = os.path.dirname(os.path.abspath(__file__))
    if os.path.isfile(package_path):
        # Package is a .sublime-package so get its filename
        package, _ = os.path.splitext(os.path.basename(package_path))
    elif os.path.isdir(package_path):
        # Package is a directory, so get its basename
        package = os.path.basename(package_path)

def plugin_unloaded():
    for state in states.values(): 
        if view := state.last_view:
            for key in state.statuses:
                view.erase_status(key)
