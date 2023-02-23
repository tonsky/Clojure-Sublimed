import os, re, sublime, sublime_plugin
from . import cs_common, cs_conn, cs_conn_nrepl_raw, cs_eval

class ConnectionShadowCljs(cs_conn_nrepl_raw.ConnectionNreplRaw):
    """
    Shadow CLJS connnection. Requires an additional argument: build
    """
    def __init__(self, addr, build):
        super().__init__(addr)
        self.build = build

    def handle_connect(self, msg):
        if 1 == msg.get('id') and 'new-session' in msg:
            self.session = msg['new-session']
            self.set_status(2, 'Upgrading REPL')

            if self.build == 'node-repl':
                code = '(shadow.cljs.devtools.api/node-repl)'
            elif self.build == 'browser-repl':
                code = '(shadow.cljs.devtools.api/browser-repl)'
            else:
                code = f'(shadow.cljs.devtools.api/repl {self.build})'
            self.send({'id': 2,
                       'session': self.session,
                       'op':      'eval',
                       'code':    code})

            return True
        elif 2 == msg.get('id') and msg.get('status') == ['done']:
            self.set_status(4, self.addr)
            return True

    def handle_value(self, msg):
        if 'value' in msg and (id := msg.get('id')):
            eval = cs_eval.by_id(id)
            value = msg.get('value')
            if eval and eval.status == 'exception' and value in {'nil', ':repl/exception!'}:
                pass
            else:
                cs_eval.on_success(id, msg.get('value'))
            return True

    def handle_err(self, msg):
        if 'err' in msg and (id := msg.get('id')):
            trace = msg['err']
            error = re.sub(r'\s*------+\s*', '', trace)
            cs_eval.on_exception(id, error, trace = trace)
            return True

    def load_file_impl(self, id, file, path):
        msg = {'id':        id,
               'session':   self.session,
               'op':        'load-file',
               'file':      file,
               'file-name': os.path.basename(path) if path else "NO_SOURCE_FILE.cljc"}
        if path:
            msg['file-path'] = path
        self.send(msg)

    def load_file(self, view):
        if view.file_name():
            super().load_file(view)
        else:
            self.eval(view, [sublime.Region(0, view.size())])


class BuildInputHandler(sublime_plugin.TextInputHandler):
    def initial_text(self):
        return ':app'

    def preview(self, text):
        return sublime.Html("""
        <html>
            <body>
            Provide the cljs build for shadow to watch. 
            <br>
            Valid options are <b>node-repl</b>, <b>browser-repl</b> or the build defined in shadow-cljs.edn / project.clj
            For more info check <a href="https://shadow-cljs.github.io/docs/UsersGuide.html#_repl_2"> Shadow Documentation </a>
            </body>
        </html>
        """)

class ClojureSublimedConnectShadowCljsCommand(sublime_plugin.ApplicationCommand):
    def run(self, address, build):
        cs_conn.last_conn = ('clojure_sublimed_connect_shadow_cljs', {'address': address, 'build': build})
        ConnectionShadowCljs(address, build).connect()

    def input(self, args):
        if 'build' not in args:
            return cs_conn.AddressInputHandler(next_input = BuildInputHandler())
        else:
            return cs_conn.AddressInputHandler()

    def is_enabled(self):
        return cs_conn.conn is None
