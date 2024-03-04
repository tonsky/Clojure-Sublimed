import json, os, re, sublime, sublime_plugin, threading
from . import cs_common, cs_conn, cs_eval, cs_eval_status, cs_parser, cs_warn

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
                    if '{"tag" "started"}' in line:
                        self.set_status(4, self.addr)
                        started = True
        except OSError:
            pass
        self.disconnect()

    def send(self, msg):
        cs_common.debug('SND {}', msg)
        self.socket.sendall(msg.encode())

    def eval_impl(self, form):
        msg = ('{' +
              f'"id" {form.id}, ' +
              f'"op" "eval", ' +
              f'"ns" "{form.ns}", ')

        code = form.code.replace('\\', '\\\\').replace('"', '\\"')
        msg += f'"code" "{code}"'

        if form.file:
            msg += f', "file" "{form.file}"'

        if form.line is not None:
            msg += f', "line" {form.line}'

        if form.column is not None:
            msg += f', "column" {form.column}'

        msg += '}'
        self.send(msg)

    def eval(self, view, sel):
        cs_warn.reset_warnings(self.window)
        for region in sel:
            # find regions to eval
            region = self.eval_region(region, view)

            start = region.begin()
            parsed = cs_parser.parse(view.substr(region))
            forms = [ \
                sublime.Region(start + child.start, start + child.end) \
                for child in parsed.children \
                if child.name not in {'comment', 'discard'} \
            ]
            
            # create evals
            batch_id = cs_eval.Eval.next_id()
            for idx, form in enumerate(forms):
                eval = cs_eval.Eval(view, form, id = f'{batch_id}.{idx}', batch_id = batch_id)

            # send msg
            (line, column) = view.rowcol_utf16(region.begin())
            form = cs_common.Form(
                id   = batch_id,
                code = view.substr(region),
                ns   = cs_parser.namespace(view, region.begin()) or 'user',
                line = line + 1,
                column = column,
                file = view.file_name()
            )
            self.eval_impl(form)

    def eval_status(self, code, ns):
        cs_warn.reset_warnings(self.window)
        batch_id = cs_eval.Eval.next_id()
        eval = cs_eval_status.StatusEval(code, id = f'{batch_id}.0', batch_id = batch_id)
        form = cs_common.Form(id = batch_id, code = code, ns = ns)
        self.eval_impl(form)

    def load_file(self, view):
        self.eval(view, [sublime.Region(0, view.size())])

    def lookup_impl(self, id, symbol, ns):
        msg = f'{{"id" {id}, "op" "lookup", "symbol" "{symbol}", "ns" "{ns}"}}'
        self.send(msg)

    def interrupt_impl(self, batch_id, id):
        msg = f'{{"id" {batch_id}, "op" "interrupt"}}'
        self.send(msg)

    def handle_value(self, msg):
        if 'ret' == msg['tag']:
            id   = msg.get('id')
            idx  = msg.get('idx')
            val  = msg.get('val')
            time = msg.get('time')
            cs_eval.on_success(f'{id}.{idx}', val, time = time)
            return True

    def handle_exception(self, msg):
        if 'ex' == msg['tag']:
            id      = msg.get('id')
            idx     = msg.get('idx')
            val     = msg.get('val')
            source  = msg.get('source')
            line    = msg.get('line')
            column  = msg.get('column')
            trace   = msg.get('trace')
            eval_id = f'{id}.{idx}' if idx is not None else id
            cs_eval.on_exception(eval_id, val, source = source, line = line, column = column, trace = trace)
            return True

    def handle_done(self, msg):
        if 'done' == msg['tag']:
            batch_id = msg.get('id')
            cs_eval.on_done(batch_id)
            return True

    def handle_lookup(self, msg):
        if 'lookup' == msg['tag']:
            id = msg.get('id')
            val = cs_parser.parse_as_dict(msg['val'])
            cs_eval.on_lookup(id, val)
            return True

    def handle_err(self, msg):
        if 'err' == msg['tag']:
            if msg['val'].startswith("Reflection warning"):
                cs_warn.add_warning(self.window)
            return True

    def handle_msg(self, msg):
        # cs_common.debug('MSG {}', msg)
        self.handle_value(msg) \
        or self.handle_exception(msg) \
        or self.handle_done(msg) \
        or self.handle_lookup(msg) \
        or self.handle_err(msg)

class ClojureSublimedConnectSocketReplCommand(sublime_plugin.WindowCommand):
    def run(self, address):
        state = cs_common.get_state(self.window)
        state.last_conn = ('clojure_sublimed_connect_socket_repl', {'address': address})
        if address == 'auto':
            address = cs_conn.AddressInputHandler(port_file = '.repl-port').initial_text()
        ConnectionSocketRepl(address).connect()

    def input(self, args):
        return cs_conn.AddressInputHandler(port_file = '.repl-port')

    def is_enabled(self):
        state = cs_common.get_state(self.window)
        return state.conn is None
