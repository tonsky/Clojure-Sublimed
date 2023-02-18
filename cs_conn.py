import os, re, sublime, sublime_plugin
from . import cs_common, cs_eval, cs_parser

# Global connection instance
conn = None

status_key = 'clojure-sublimed-conn'
phases = ['🌑', '🌒', '🌓', '🌔', '🌕']
last_conn = None

def ready():
    """
    When connection is fully initialized
    """
    return bool(conn and conn.ready())

class Connection:
    def __init__(self):
        self.status = None
        self.disconnecting = False

    def connect_impl(self):
        pass

    def connect(self):
        """
        Connect to address specified during construction
        """
        global conn
        try:
            self.connect_impl()
            conn = self
        except Exception as e:
            cs_common.error('Connection failed')
            self.disconnect()
            if window := sublime.active_window():
                window.status_message(f'Connection failed')

    def ready(self):
        return bool(self.status and self.status[0] == phases[4])

    def eval_impl(self, form):
        pass

    def eval(self, view, sel):
        """
        Eval code and call `cs_eval.on_success(id, value)` or `cs_eval.on_exception(id, value, trace)`
        """
        for region in sel:
            if region.empty():
                region = cs_parser.topmost_form(view, region.begin())
            eval = cs_eval.Eval(view, region)
            (line, column) = view.rowcol_utf16(region.begin())
            line = line + 1
            form = cs_common.Form(
                    id     = eval.id,
                    code   = view.substr(region),
                    ns     = cs_parser.namespace(view, region.begin()) or 'user',
                    line   = line,
                    column = column,
                    file   = view.file_name())
            self.eval_impl(form)

    def load_file_impl(self, id, file, path):
        pass

    def load_file(self, view):
        """
        Load whole file (~load-file nREPL command). Same callbacks as `eval`
        """
        region = sublime.Region(0, view.size())
        eval = cs_eval.Eval(view, region)
        self.load_file_impl(eval.id, view.substr(region), view.file_name())

    def lookup_impl(self, id, symbol, ns):
        pass

    def lookup(self, id, symbol, ns = 'user'):
        """
        Look symbol up and call `cs_eval.on_lookup(id, value)`
        """
        self.lookup_impl(id, symbol, ns)

    def interrupt_impl(self, batch_id, id):
        pass

    def interrupt(self, batch_id, id):
        """
        Interrupt currently executing eval with id = id.
        Will probably call `cs_eval.on_exception(id, value, trace)` on interruption
        """
        self.interrupt_impl(batch_id, id)

    def disconnect_impl(self):
        pass

    def disconnect(self):
        """
        Disconnect from REPL
        """
        if self.disconnecting:
            return
        self.disconnecting = True
        self.disconnect_impl()
        global conn
        conn = None
        cs_common.set_status(status_key, None)
        cs_eval.erase_evals()

    def set_status(self, phase, message, *args):
        status = phases[phase] + ' ' + message.format(*args)
        self.status = status
        cs_common.set_status(status_key, status)

class AddressInputHandler(sublime_plugin.TextInputHandler):
    def __init__(self, search_nrepl = True, next_input = None):
        self.search_nrepl = search_nrepl
        self.next = next_input

    """
    Reusable InputHandler that remembers last address and can also look for .nrepl-port file
    """
    def placeholder(self):
        return "host:port or /path/to/nrepl.sock"

    def initial_text(self):
        # .nrepl-port file present
        if self.search_nrepl and (window := sublime.active_window()):
            for folder in window.folders():
                if os.path.exists(folder + "/.nrepl-port"):
                    with open(folder + "/.nrepl-port", "rt") as f:
                        content = f.read(10).strip()
                        if re.fullmatch(r'[1-9][0-9]*', content):
                            return f'localhost:{content}'

        return last_conn[1]['address'] if last_conn else 'localhost:'

    def initial_selection(self):
        text = self.initial_text()
        end = len(text)
        if ':' in text:
            return [(text.rfind(':') + 1, end)]
        elif '/' in text:
            return [(text.rfind('/') + 1, end)]

    def preview(self, text):
        if not self.validate(text):
            return 'Expected <host>:<port> or <path>'

    def validate(self, text):
        text = text.strip()
        if 'auto' == text:
            return True
        elif match := re.fullmatch(r'([a-zA-Z0-9\.]+):(\d{1,5})', text):
            _, port = match.groups()
            return 1 <= int(port) and int(port) < 65536
        else:
            return os.path.isfile(text)

    def next_input(self, args):
        return self.next

class ClojureSublimedReconnectCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        if conn:
            sublime.run_command('clojure_sublimed_disconnect', {})
        sublime.run_command(*last_conn)

    def is_enabled(self):
        return last_conn is not None

class ClojureSublimedDisconnectCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        global conn
        conn.disconnect()

    def is_enabled(self):
        global conn
        return conn is not None

def plugin_unloaded():
    global conn
    if conn:
        conn.disconnect()
