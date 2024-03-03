import os, re, sublime, sublime_plugin
from . import cs_common, cs_eval, cs_eval_status, cs_parser, cs_warn

status_key = 'clojure-sublimed-conn'
phases = ['🌑', '🌒', '🌓', '🌔', '🌕']

def ready(window = None):
    """
    When connection is fully initialized
    """
    state = cs_common.get_state(window)
    return bool(state.conn and state.conn.ready())

class Connection:
    def __init__(self):
        self.status = None
        self.disconnecting = False
        self.window = sublime.active_window()

    def connect_impl(self):
        pass

    def connect(self):
        """
        Connect to address specified during construction
        """
        state = cs_common.get_state()
        try:
            self.connect_impl()
            state.conn = self
        except Exception as e:
            cs_common.error('Connection failed')
            self.disconnect()
            if window := sublime.active_window():
                window.status_message(f'Connection failed')

    def ready(self):
        return bool(self.status and self.status[0] == phases[4])

    def eval_impl(self, form):
        pass

    def eval_region(self, region, view):
        if region.empty():
            if eval := cs_eval.by_region(view, region):
                return eval.region()
            return cs_parser.topmost_form(view, region.begin())
        return region

    def eval(self, view, sel, wrap_fstr=None):
        """
        Eval code and call `cs_eval.on_success(id, value)` or `cs_eval.on_exception(id, value, trace)`
        """
        for region in sel:
            region = self.eval_region(region, view)
            eval = cs_eval.Eval(view, region)
            (line, column) = view.rowcol_utf16(region.begin())
            line = line + 1

            code = view.substr(region)
            if wrap_fstr is not None:
                code = wrap_fstr%code

            form = cs_common.Form(
                    id     = eval.id,
                    code   = code,
                    ns     = cs_parser.namespace(view, region.begin()) or 'user',
                    line   = line,
                    column = column,
                    file   = view.file_name())
            self.eval_impl(form)

    def eval_status(self, code, ns):
        eval = cs_eval_status.StatusEval(code)
        form = cs_common.Form(id = eval.id, code = code, ns = ns)
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

    def lookup(self, view, region):
        """
        Look symbol up and call `cs_eval.on_lookup(id, value)`
        """
        symbol = view.substr(region)
        ns     = cs_parser.namespace(view, region.begin()) or 'user'
        eval   = cs_eval.Eval(view, region)
        self.lookup_impl(eval.id, symbol, ns)

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
        state = cs_common.get_state()
        state.conn = None
        cs_common.set_status(self.window, status_key, None)
        cs_eval.erase_evals(lambda eval: eval.window == self.window)
        cs_warn.reset_warnings(self.window)

    def set_status(self, phase, message, *args):
        status = phases[phase] + ' ' + message.format(*args)
        self.status = status
        cs_common.set_status(self.window, status_key, status)

class AddressInputHandler(sublime_plugin.TextInputHandler):
    def __init__(self, port_file = None, next_input = None):
        self.port_file = port_file
        self.next = next_input

    """
    Reusable InputHandler that remembers last address and can also look for .nrepl-port file
    """
    def placeholder(self):
        return "host:port or /path/to/nrepl.sock"

    def initial_text(self):
        # .nrepl-port file present
        if self.port_file and (window := sublime.active_window()):
            for folder in window.folders():
                if os.path.exists(folder + "/" + self.port_file):
                    with open(folder + "/" + self.port_file, "rt") as f:
                        content = f.read(10).strip()
                        if re.fullmatch(r'[1-9][0-9]*', content):
                            return f'localhost:{content}'
        state = cs_common.get_state()
        return state.last_conn[1]['address'] if state.last_conn else 'localhost:'

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

class ClojureSublimedReconnectCommand(sublime_plugin.WindowCommand):
    def run(self):
        state = cs_common.get_state(self.window)
        if state.conn:
            sublime.run_command('clojure_sublimed_disconnect', {})
        sublime.run_command(*state.last_conn)

    def is_enabled(self):
        state = cs_common.get_state(self.window)
        return state.last_conn is not None

class ClojureSublimedDisconnectCommand(sublime_plugin.WindowCommand):
    def run(self):
        state = cs_common.get_state(self.window)
        state.conn.disconnect()

    def is_enabled(self):
        state = cs_common.get_state(self.window)
        return state.conn is not None

def plugin_unloaded():
    for state in cs_common.states.values():
        if state.conn:
            state.conn.disconnect()
