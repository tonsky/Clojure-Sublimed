import os, sublime, sublime_plugin, threading
from . import cs_bencode, cs_colors, cs_common, cs_conn, cs_eval

class ConnectionNreplRaw(cs_conn.Connection):
    """
    Raw nREPL connection: no extensions, no options, nothing. Bare-bones nREPL
    """
    def __init__(self, addr):
        super().__init__()
        self.addr        = addr
        self.socket      = None
        self.reader      = None
        self.session     = None
        self.closing     = False
        self.eval_op     = 'eval'
        self.output_view = None

    def connect_impl(self):
        self.set_status(0, 'Connecting to {}...', self.get_addr())
        self.socket = cs_common.socket_connect(self.get_addr())
        self.reader = threading.Thread(daemon=True, target=self.read_loop)
        self.reader.start()

    def disconnect_impl(self):
        if self.socket:
            if self.session:
                self.send({'op': 'close', 'session': self.session})
            else:
                self.socket.close()
                self.socket = None

    def read_loop(self):
        try:
            self.set_status(1, 'Cloning session')
            self.send({'op': 'clone', 'id': 1})
            for msg in cs_bencode.decode_file(cs_common.SocketIO(self.socket)):
                self.handle_msg(msg)
        except OSError:
            pass
        self.disconnect()

    def send(self, msg):
        cs_common.debug('SND {}', msg)
        self.socket.sendall(cs_bencode.encode(msg).encode())

    def eval_impl(self, form):
        msg = {'id':      form.id,
               'session': self.session,
               'op':      self.eval_op,
               'code':    form.code,
               'ns':      form.ns}
        if (line := form.line) is not None:
            msg['line'] = line
        if (column := form.column) is not None:
            msg['column'] = column
        if (file := form.file) is not None:
            msg['file'] = file
        self.send(msg)

    def load_file_impl(self, id, file, path):
        msg = {'id':        id,
               'session':   self.session,
               'op':        'load-file',
               'file':      file,
               'file-name': os.path.basename(path) if path else "NO_SOURCE_FILE.cljc"}
        if path:
            msg['file-path'] = path
        self.send(msg)

    def lookup_impl(self, id, symbol, ns):
        msg = {'id':      id,
               'session': self.session,
               'op':      'lookup',
               'sym':     symbol,
               'ns':      ns}
        self.send(msg)

    def interrupt_impl(self, batch_id, id):
        msg = {'session':      self.session,
               'op':           'interrupt',
               'interrupt-id': id}
        self.send(msg)

    def handle_connect(self, msg):
        if 1 == msg.get('id') and 'new-session' in msg:
            self.session = msg['new-session']
            self.set_status(4, self.get_addr())
            return True

    def handle_disconnect(self, msg):
        if self.session == msg.get('session') and 'session-closed' in msg.get('status', []):
            self.socket.close()
            self.socket = None
            return True

    def handle_value(self, msg):
        if 'value' in msg and (id := msg.get('id')):
            if isinstance(id, str) and id.endswith('.e'):
                id = int(id[:-2])
                if (eval := cs_eval.by_id(id)) and eval.status == 'exception' and not eval.trace:
                    eval.trace = msg['value']
            else:
                cs_eval.on_success(id, msg.get('value'))
            return True

    def handle_exception(self, msg):
        if (id := msg.get('id')):
            error = msg.get('root-ex') or msg.get('ex')
            if error:
                self.eval_impl(cs_common.Form(id = f'{id}.e', code = '*e'))
            if not error:
                if 'namespace-not-found' in msg.get('status', []):
                    error = 'Namespace not found: ' + msg.get('ns', '')
                elif 'unknown-op' in msg.get('status', []):
                    error = 'Unknown op: ' + msg.get('op', '')
            if error:
                cs_eval.on_exception(id, error)
                return True

    def handle_lookup(self, msg):
        if 'info' in msg and (id := msg.get('id')):
            cs_eval.on_lookup(id, msg['info'])
            return True

    def get_output_view(self):
        window = self.window
        if not self.output_view:
            self.output_view = window.find_output_panel('repl')
            if self.output_view:
                self.output_view.run_command("clojure_sublimed_clear_output_panel")
            else:
                self.output_view = window.create_output_panel('repl')
        return self.output_view

    def handle_out(self, msg):
        if 'out' in msg:
            self.window.run_command("show_panel", {"panel": "output.repl"})
            cs_colors.write(self.get_output_view(), msg['out'])
            return True

    def handle_err(self, msg):
        if 'err' in msg:
            self.window.run_command("show_panel", {"panel": "output.repl"})
            cs_colors.write(self.get_output_view(), msg['err'])
            return True

    def handle_done(self, msg):
        if (id := msg.get('id')) and (status := msg.get('status')) and 'done' in status:
            cs_eval.on_done(id)

    def handle_msg(self, msg):
        cs_common.debug('RCV {}', msg)
        self.handle_connect(msg) \
        or self.handle_disconnect(msg) \
        or self.handle_value(msg) \
        or self.handle_exception(msg) \
        or self.handle_lookup(msg) \
        or self.handle_out(msg) \
        or self.handle_err(msg) \
        or self.handle_done(msg)

class ClojureSublimedConnectNreplRawCommand(sublime_plugin.WindowCommand):
    def run(self, address, timeout = 0):
        state = cs_common.get_state(self.window)
        state.last_conn = ('clojure_sublimed_connect_nrepl_raw', {'address': address})
        if address == 'auto':
            address = self.input({}).initial_text()
        while not state.conn:
            ConnectionNreplRaw(address).try_connect(timeout = timeout)

    def input(self, args):
        if 'address' not in args:
            return cs_conn.AddressInputHandler(port_files = ['.nrepl-port', '.shadow-cljs/nrepl.port'])

    def is_enabled(self):
        state = cs_common.get_state(self.window)
        return state.conn is None

class ClojureSublimedClearOutputPanelCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.erase(edit, sublime.Region(0, self.view.size()))

class ClojureSublimedToggleOutputPanelCommand(sublime_plugin.WindowCommand):
    def run(self):
        window = self.window
        if window.active_panel() == "output.repl":
            window.run_command("hide_panel", {"cancel": False})
        else:
            window.run_command("show_panel", {"panel": "output.repl"})

    def is_enabled(self):
        state = cs_common.get_state(self.window)
        return bool(state.conn and state.conn.ready() and isinstance(state.conn, ConnectionNreplRaw))
