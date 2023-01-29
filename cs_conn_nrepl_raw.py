import sublime, sublime_plugin, threading
from . import cs_bencode, cs_common, cs_conn, cs_eval

class ConnectionNreplRaw(cs_conn.Connection):
    def __init__(self, addr):
        cs_conn.Connection.__init__(self)
        self.addr      = addr
        self.socket    = None
        self.reader    = None
        self.session   = None
        self.closing   = False

    def connect_impl(self):
        self.set_status(0, 'Connecting to {}', self.addr)
        self.socket = cs_common.socket_connect(self.addr)
        self.reader = threading.Thread(daemon=True, target=self.read_loop)
        self.reader.start()

    def disconnect_impl(self):
        if self.session:
            self.send({'op': 'close', 'session': self.session})
        self.socket.close()
        self.socket = None

    def read_loop(self):
        try:
            self.set_status(2, 'Cloning session')
            self.send({'op': 'clone', 'id': 1})
            for msg in cs_bencode.decode_file(cs_common.SocketIO(self.socket)):
                self.handle_msg(msg)
        except OSError:
            pass
        self.disconnect()

    def handle_connect(self, msg):
        if 1 == msg.get('id') and 'new-session' in msg:
            self.session = msg['new-session']
            self.set_status(4, self.addr)
            return True

    def send(self, msg):
        cs_common.debug('SND {}', msg)
        self.socket.sendall(cs_bencode.encode(msg).encode())

    def eval_impl(self, id, code, ns = 'user', line = None, column = None, file = None):
        msg = {'id':      id,
               'session': self.session,
               'op':      'eval',
               'code':    code,
               'ns':      ns}
        if line is not None:
            msg['line'] = line
        if column is not None:
            msg['column'] = column
        if file is not None:
            msg['file'] = file
        self.send(msg)

    def handle_value(self, msg):
        if 'value' in msg and (id := msg.get('id')):
            cs_eval.on_success(id, msg.get('value'))
            return True

    def handle_exception(self, msg):
        if (id := msg.get('id')):
            error = msg.get('root-ex') or msg.get('ex')
            if not error and 'status' in msg and 'namespace-not-found' in msg['status']:
                error = 'Namespace not found: ' + msg['ns']
            if error:
                cs_eval.on_exception(id, error)
                return True

    def handle_msg(self, msg):
        cs_common.debug('RCV {}', msg)
        self.handle_connect(msg) \
        or self.handle_value(msg) \
        or self.handle_exception(msg)

class ClojureSublimedConnectNreplRawCommand(sublime_plugin.ApplicationCommand):
    def run(self, address):
        if address == "auto":
            address = cs_conn.AddressInputHandler().initial_text()
        ConnectionNreplRaw(address).connect()

    def input(self, args):
        return cs_conn.AddressInputHandler()

    def is_enabled(self):
        return cs_conn.conn is None
