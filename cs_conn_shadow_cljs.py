import os, sublime, sublime_plugin, threading
from . import cs_bencode, cs_common, cs_conn, cs_conn_nrepl_raw, cs_eval

class ConnectionShadowCLJS(cs_conn_nrepl_raw.ConnectionNreplRaw):
    """
    Raw nREPL connection: no extensions, no options, nothing. Bare-bones nREPL
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
        ConnectionShadowCLJS(address, build).connect()

    def input(self, args):
        # if 'build' not in args:
        return cs_conn.AddressInputHandler(BuildInputHandler())
        # else:
        #     return cs_conn.AddressInputHandler()

    def is_enabled(self):
        return cs_conn.conn is None
