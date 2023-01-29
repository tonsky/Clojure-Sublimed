import os, re, sublime, sublime_plugin
from . import cs_common, cs_eval

conn = None
status_key = 'clojure-sublimed-conn'
phases = ['🌑', '🌒', '🌓', '🌔', '🌕']
last_addr = 'localhost:'

def erase_status():
    if window := sublime.active_window():
        if view := window.active_view():
            view.erase_status(status_key)

def ready():
    return bool(conn and conn.status and conn.status[0] == phases[4])

class Connection:
    def __init__(self):
        self.status = None
        self.disconnecting = False

    def connect_impl(self):
        pass

    def connect(self):
        global conn
        try:
            self.connect_impl()
            conn = self
        except Exception as e:
            cs_common.error('Connection failed')
            self.disconnect()
            if window := sublime.active_window():
                window.status_message(f'Connection failed')

    def eval_impl(self, id, code, ns = 'user', line = None, column = None, file = None):
        pass

    def eval(self, id, code, ns = 'user', line = None, column = None, file = None):
        self.eval_impl(id, code, ns, line, column, file)

    def disconnect_impl(self):
        pass

    def disconnect(self):
        if self.disconnecting:
            return
        self.disconnecting = True
        self.disconnect_impl()
        global conn
        conn = None
        erase_status()
        cs_eval.erase_evals()

    def set_status(self, phase, message, *args):
        self.status = phases[phase] + ' ' + message.format(*args)
        self.refresh_status()

    def refresh_status(self):
        if window := sublime.active_window():
            if view := window.active_view():
                view.set_status(status_key, self.status)

class AddressInputHandler(sublime_plugin.TextInputHandler):
    def placeholder(self):
        return "host:port or /path/to/nrepl.sock"

    def initial_text(self):
        # .nrepl-port file present
        if window := sublime.active_window():
            for folder in window.folders():
                if os.path.exists(folder + "/.nrepl-port"):
                    with open(folder + "/.nrepl-port", "rt") as f:
                        content = f.read(10).strip()
                        if re.fullmatch(r'[1-9][0-9]*', content):
                            return f'localhost:{content}'

        return last_addr

    def initial_selection(self):
        text = self.initial_text()
        end = len(text)
        if ':' in text:
            return [text.rfind(':') + 1, end]
        elif '/' in text:
            return [text.rfind('/') + 1, end]

    def preview(self, text):
        if not self.validate(text):
            return "Expected <host>:<port> or <path>"

    def validate(self, text):
        text = text.strip()
        if "auto" == text:
            return True
        elif match := re.fullmatch(r'([a-zA-Z0-9\.]+):(\d{1,5})', text):
            _, port = match.groups()
            return int(port) in range(1, 65536)
        else:
            return os.path.isfile(text)

class ClojureSublimedDisconnectCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        global conn
        conn.disconnect()

    def is_enabled(self):
        global conn
        return conn is not None

class EventListener(sublime_plugin.EventListener):
    def on_activated_async(self, view):
        global conn
        if conn:
            conn.refresh_status()
        else:
            erase_status()

def plugin_unloaded():
    global conn
    if conn:
        conn.disconnect()
