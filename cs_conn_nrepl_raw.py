import os, sublime, sublime_plugin, threading
from . import cs_bencode, cs_common, cs_conn, cs_eval

class ConnectionNreplRaw(cs_conn.Connection):
    """
    Raw nREPL connection: no extensions, no options, nothing. Bare-bones nREPL
    """
    def __init__(self, addr):
        super().__init__()
        self.addr      = addr
        self.socket    = None
        self.reader    = None
        self.session   = None
        self.closing   = False
        self.eval_op   = 'eval'

    def connect_impl(self):
        self.set_status(0, 'Connecting to {}...', self.addr)
        self.socket = cs_common.socket_connect(self.addr)
        self.reader = threading.Thread(daemon=True, target=self.read_loop)
        self.reader.start()

    def disconnect_impl(self):
        if self.session:
            self.send({'op': 'close', 'session': self.session})
        if self.socket:
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
            self.set_status(4, self.addr)
            return True

    def handle_value(self, msg):
        if 'value' in msg and (id := msg.get('id')):
            cs_eval.on_success(id, msg.get('value'))
            return True

    def handle_exception(self, msg):
        if (id := msg.get('id')):
            error = msg.get('root-ex') or msg.get('ex')
            if not error and 'status' in msg and 'namespace-not-found' in msg['status']:
                error = 'Namespace not found: ' + msg['ns']
            if not error and 'status' in msg and 'unknown-op' in msg['status']:
                error = 'Unknown op: ' + msg['op']
            if error:
                cs_eval.on_exception(id, error)
                return True

    def handle_lookup(self, msg):
        if 'info' in msg and (id := msg.get('id')):
            cs_eval.on_lookup(id, msg['info'])
            return True

    def handle_out(self, msg):
        if 'out' in msg:
            print(msg['out'], end = '')
            return True
        elif 'err' in msg:
            print(msg['err'], end = '')
            return True

    def handle_done(self, msg):
        if (id := msg.get('id')) and (status := msg.get('status')) and 'done' in status:
            cs_eval.on_done(id)

    def handle_msg(self, msg):
        cs_common.debug('RCV {}', msg)
        self.handle_connect(msg) \
        or self.handle_value(msg) \
        or self.handle_exception(msg) \
        or self.handle_lookup(msg) \
        or self.handle_out(msg) \
        or self.handle_done(msg)

class ClojureSublimedConnectNreplRawCommand(sublime_plugin.ApplicationCommand):
    def run(self, address):
        cs_conn.last_conn = ('clojure_sublimed_connect_nrepl_raw', {'address': address})
        if address == 'auto':
            address = cs_conn.AddressInputHandler().initial_text()
        ConnectionNreplRaw(address).connect()

    def input(self, args):
        return cs_conn.AddressInputHandler()

    def is_enabled(self):
        return cs_conn.conn is None
