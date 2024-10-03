import os, sublime, sublime_plugin
from . import cs_common, cs_conn, cs_conn_nrepl_raw, cs_eval

class ConnectionNreplJvm(cs_conn_nrepl_raw.ConnectionNreplRaw):
    """
    Enhanced nREPL connection that will work only on JVM
    """
    def __init__(self, addr):
        super().__init__(addr)
        self.eval_op = 'clone-eval-close'

    def send(self, msg):
        if self.ready():
            ns = cs_common.ns + '.middleware'
            msg['nrepl.middleware.caught/caught'] = ns + '/print-root-trace'
            if 'nrepl.middleware.print/quota' not in msg:
                msg['nrepl.middleware.print/quota'] = cs_common.setting('print_quota', 4096)
            if 0 == msg['nrepl.middleware.print/quota']:
                del msg['nrepl.middleware.print/quota']
        super().send(msg)

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
        if form.print_quota is not None:
            msg['nrepl.middleware.print/quota'] = form.print_quota
        self.send(msg)

    def interrupt_impl(self, batch_id, id):
        eval = cs_eval.by_id(id)
        msg = {'session':      eval.session or self.session,
               'op':           'interrupt',
               'interrupt-id': id}
        self.send(msg)

    def handle_connect(self, msg):
        if 1 == msg.get('id') and 'new-session' in msg:
            self.set_status(2, 'Uploading middleware 1/2...')
            self.session = msg['new-session']
            file = cs_common.clojure_source('core.clj')
            self.send({'id':      2,
                       'session': self.session,
                       'op':      'load-file',
                       'file':    file})
            return True

        if 2 == msg.get('id') and 'done' in msg.get('status', []):
            self.set_status(2, 'Uploading middleware 2/2...')
            file = cs_common.clojure_source('middleware.clj')
            self.send({'id':      3,
                       'session': self.session,
                       'op':      'load-file',
                       'file':    file})
            return True

        elif 3 == msg.get('id') and 'done' in msg.get('status', []):
            self.set_status(2, 'Adding middlewares...')
            eval_shared = cs_common.setting('eval_shared', '')
            ns = cs_common.ns + '.middleware'
            self.send({'id':               4 if eval_shared else 5,
                       'session':          self.session,
                       'op':               'add-middleware',
                       'middleware':       [ns + '/clone-and-eval',
                                            ns + '/time-eval',
                                            ns + '/wrap-errors',
                                            ns + '/wrap-output'],
                       'extra-namespaces': [cs_common.ns + '.exception', ns]})
            return True

        elif 4 == msg.get('id') and 'done' in msg.get('status', []):
            self.set_status(3, 'Evaluating session code...')
            eval_shared = cs_common.setting('eval_shared')
            self.send({'id':      5,
                       'session': self.session,
                       'op':      'eval',
                       'code':    eval_shared})
            return True

        elif 5 == msg.get('id') and 'done' in msg.get('status', []):
            self.set_status(4, self.get_addr())
            return True

    def handle_new_session(self, msg):
        if 'new-session' in msg and (id := msg.get('id')) and (eval := cs_eval.by_id(id)):
            eval.session = msg['new-session']
            return True

    def handle_value(self, msg):
        if 'value' in msg and (id := msg.get('id')):
            time = msg.get(cs_common.ns + '.middleware/time-taken')
            if time:
                time = time / 1000000
            cs_eval.on_success(id, msg.get('value'), time = time)
            return True

    def handle_exception(self, msg):
        if (id := msg.get('id')):
            ns = cs_common.ns + '.middleware/'
            present = lambda key: (ns + key) in msg
            get = lambda key: msg.get(ns + key)
            if get('root-ex-class') and get('root-ex-msg'):
                text = get('root-ex-class') + ': ' + get('root-ex-msg')
                line = None
                column = None
                if get('root-ex-data'):
                    text += ' ' + get('root-ex-data')
                if present('line') and present('column') and get('source'):
                    line   = get('line') - 1
                    column = get('column')
                    text   += f" ({get('source')}:{get('line')}:{get('column')})"
                cs_eval.on_exception(id, text, line = line, column = column, trace = get('trace'))
                return True
            else:
                return super().handle_exception(msg)

    def handle_msg(self, msg):
        cs_common.debug('RCV {}', msg)

        for key in msg.get('nrepl.middleware.print/truncated-keys', []):
            msg[key] += ' ...'

        self.handle_connect(msg) \
        or self.handle_disconnect(msg) \
        or self.handle_new_session(msg) \
        or self.handle_value(msg) \
        or self.handle_exception(msg) \
        or self.handle_lookup(msg) \
        or self.handle_done(msg)

class ClojureSublimedConnectNreplJvmCommand(sublime_plugin.WindowCommand):
    def run(self, address, timeout = 0):
        state = cs_common.get_state(self.window)
        state.last_conn = ('clojure_sublimed_connect_nrepl_jvm', {'address': address})
        if address == 'auto':
            address = self.input({}).initial_text()
        ConnectionNreplJvm(address).try_connect(timeout = timeout)

    def input(self, args):
        if 'address' not in args:
            return cs_conn.AddressInputHandler(port_files = ['.nrepl-port', '.shadow-cljs/nrepl.port'])

    def is_enabled(self):
        state = cs_common.get_state(self.window)
        return state.conn is None
