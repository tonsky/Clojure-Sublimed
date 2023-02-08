import json, os, re, sublime, sublime_plugin, threading
from . import cs_common, cs_conn, cs_eval, cs_parser

def lines(socket):
    buffer = b''
    while True:
        more = socket.recv(4096)
        if more:
            buffer += more
        while b'\n' in buffer:
            (line, buffer) = buffer.split(b'\n', 1)
            yield line.decode()
        if not more:
            break
    if buffer:
        yield buffer.decode()

class ConnectionSocketRepl(cs_conn.Connection):
    """
    Upgraded Socket REPL: does what nREPL JVM does, but without extra dependencies
    """
    def __init__(self, addr):
        super().__init__()
        self.addr      = addr
        self.socket    = None
        self.reader    = None
        self.closing   = False

    def connect_impl(self):
        self.set_status(0, 'Connecting to {}', self.addr)
        self.socket = cs_common.socket_connect(self.addr)
        self.reader = threading.Thread(daemon=True, target=self.read_loop)
        self.reader.start()

    def disconnect_impl(self):
        if self.socket:
            self.socket.close()
            self.socket = None

    def read_loop(self):
        try:
            self.set_status(1, 'Upgrading REPL')
            self.socket.sendall(cs_common.clojure_source('exception.clj').encode())
            self.socket.sendall(cs_common.clojure_source('socket_repl.clj').encode())
            if shared := cs_common.setting('eval_shared'):
                self.socket.sendall(shared.encode())
            self.socket.sendall("(repl)\n".encode())
            started = False
            for line in lines(self.socket):
                print("RCV", started, line)
                if started:
                    msg = cs_parser.parse_as_dict(line)
                    self.handle_msg(msg)
                else:
                    if '{:tag :started}' in line:
                        self.set_status(4, self.addr)
                        started = True
        except OSError:
            pass
        self.disconnect()

    def send(self, msg):
        cs_common.debug('SND {}', msg)
        self.socket.sendall(msg.encode())

    def eval_impl(self, id, code, ns = 'user', line = None, column = None, file = None):
        code = code.replace('\\', '\\\\').replace('"', '\\"')
        msg = f'{{:id {id}, :op :eval, :code "{code}", :ns {ns}'
        if line is not None:
            msg += f', :line {line}'
        if column is not None:
            msg += f', :column {column}'
        if file is not None:
            msg += f', :file "{file}"'
        msg += f"}}"
        self.send(msg)

    def load_file(self, id, file, path):
        self.eval(id, file, file = path)

    def lookup_impl(self, id, symbol, ns):
        msg = f'{{:id {id}, :op :lookup, :symbol "{symbol}", :ns {ns}}}'
        self.send(msg)

    # def interrupt_impl(self, id):
    #     msg = {'session':      self.session,
    #            'op':           'interrupt',
    #            'interrupt-id': id}
    #     self.send(msg)

    def handle_value(self, msg):
        if ':ret' == msg[':tag'] and (id := msg.get(':id')):
            cs_eval.on_success(id, msg.get(':val'))
            return True

    def handle_exception(self, msg):
        if ':ex' == msg[':tag'] and (id := msg.get(':id')):
            cs_eval.on_exception(id, msg.get(':val'), line = msg.get(':line'), column = msg.get(':column'), trace = msg.get(':trace'))
            return True

    def handle_lookup(self, msg):
        if ':lookup' == msg[':tag'] and (id := msg.get(':id')):
            val = cs_parser.parse_as_dict(msg[':val'])
            cs_eval.on_lookup(id, val)
            return True

    def handle_msg(self, msg):
        cs_common.debug('MSG {}', msg)
        self.handle_value(msg) \
        or self.handle_exception(msg) \
        or self.handle_lookup(msg)

class ClojureSublimedConnectSocketReplCommand(sublime_plugin.ApplicationCommand):
    def run(self, address):
        if address == 'auto':
            address = cs_conn.AddressInputHandler().initial_text()
        ConnectionSocketRepl(address).connect()

    def input(self, args):
        return cs_conn.AddressInputHandler()

    def is_enabled(self):
        return cs_conn.conn is None
