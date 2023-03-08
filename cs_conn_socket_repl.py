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
            self.send(cs_common.clojure_source('core.clj'))
            self.send(cs_common.clojure_source('socket_repl.clj'))
            if shared := cs_common.setting('eval_shared'):
                self.send(shared)
            self.send("(repl)\n")
            started = False
            for line in lines(self.socket):
                cs_common.debug('RCV {}', line)
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

    def eval(self, view, sel):
        regions = []
        for region in sel:
            if region.empty():
                region = cs_parser.topmost_form(view, region.begin())
                regions.append(region)
            else:
                start = region.begin()
                parsed = cs_parser.parse(view.substr(region))
                regions += [sublime.Region(start + child.start, start + child.end) for child in parsed.children]

        forms = []
        batch_id = cs_eval.Eval.next_id()
        for region in regions:
            eval = cs_eval.Eval(view, region, batch_id = batch_id)
            (line, column) = view.rowcol_utf16(region.begin())
            line = line + 1
            form = cs_common.Form(
                    id     = eval.id,
                    code   = view.substr(region),
                    ns     = cs_parser.namespace(view, region.begin()) or 'user',
                    line   = line,
                    column = column,
                    file   = view.file_name())
            forms.append(form)

        msg = f'{{:id {batch_id}, :op :eval, :forms ['
        for form in forms:
            code = form.code.replace('\\', '\\\\').replace('"', '\\"')
            msg += f'{{:id {form.id}, :code "{code}", :ns {form.ns}'
            if (line := form.line) is not None:
                msg += f', :line {line}'
            if (column := form.column) is not None:
                msg += f', :column {column}'
            if (file := form.file) is not None:
                msg += f', :file "{file}"'
            msg += f'}}, '
        msg += f"]}}"
        self.send(msg)

    def load_file(self, view):
        self.eval(view, [sublime.Region(0, view.size())])

    def lookup_impl(self, id, symbol, ns):
        msg = f'{{:id {id}, :op :lookup, :symbol "{symbol}", :ns {ns}}}'
        self.send(msg)

    def interrupt_impl(self, batch_id, id):
        msg = f'{{:id {batch_id}, :op :interrupt}}'
        self.send(msg)

    def handle_value(self, msg):
        if ':ret' == msg[':tag'] and (id := msg.get(':id')):
            cs_eval.on_success(id, msg.get(':val'), time = msg.get(':time'))
            return True

    def handle_exception(self, msg):
        if ':ex' == msg[':tag'] and (id := msg.get(':id')):
            cs_eval.on_exception(id, msg.get(':val'), line = msg.get(':line'), column = msg.get(':column'), trace = msg.get(':trace'))
            return True

    def handle_done(self, msg):
        if ':done' == msg[':tag'] and (batch_id := msg.get(':id')):
            cs_eval.on_done(batch_id)

    def handle_lookup(self, msg):
        if ':lookup' == msg[':tag'] and (id := msg.get(':id')):
            val = cs_parser.parse_as_dict(msg[':val'])
            cs_eval.on_lookup(id, val)
            return True

    def handle_msg(self, msg):
        cs_common.debug('MSG {}', msg)
        self.handle_value(msg) \
        or self.handle_exception(msg) \
        or self.handle_done(msg) \
        or self.handle_lookup(msg)

class ClojureSublimedConnectSocketReplCommand(sublime_plugin.ApplicationCommand):
    def run(self, address):
        cs_conn.last_conn = ('clojure_sublimed_connect_socket_repl', {'address': address})
        ConnectionSocketRepl(address).connect()

    def input(self, args):
        return cs_conn.AddressInputHandler(search_nrepl = False)

    def is_enabled(self):
        return cs_conn.conn is None
