import html, json, os, re, socket, sublime, sublime_plugin, threading
from collections import defaultdict
from .src import bencode
from typing import Any, Dict

ns = 'sublime-clojure'
package = 'Sublime Clojure'

class Eval:
    # class
    next_id:   int = 10

    # instance
    id:        int
    view:      sublime.View
    status:    str # "clone" | "eval" | "interrupt" | "success" | "exception"
    code:      str
    session:   str
    msg:       Dict[str, Any]
    trace:     str
    trace_key: int
    
    def __init__(self, view, region, status, value):
        self.id = Eval.next_id
        self.view = view
        self.status = status
        self.code = view.substr(region)
        self.session = None
        self.msg = None
        self.trace = None
        self.trace_key = None

        Eval.next_id += 1
        scope, color = self.scope_color()
        view.add_regions(self.value_key(), [region], scope, '', sublime.DRAW_NO_FILL, [value], color)

    def value_key(self):
        return f"{ns}.eval-{self.id}"

    def scope_color(self):
        if "success" == self.status:
            return ("region.greenish", '#7CCE9B')
        elif "exception" == self.status:
            return ("region.redish", '#DD1730')
        else:
            return ("region.bluish", '#7C9BCE')

    def region(self):
        regions = self.view.get_regions(self.value_key())
        if regions and len(regions) >= 1:
            return regions[0]

    def update(self, status, value, region = None):
        self.status = status
        region = region or self.region()
        if region:
            scope, color = self.scope_color()
            self.view.add_regions(self.value_key(), [region], scope, '', sublime.DRAW_NO_FILL, [value], color)            

    def toggle_trace(self):
        if self.trace:
            if self.trace_key:
                self.view.erase_phantom_by_id(self.trace_key)
                self.trace_key = None
            else:
                settings = self.view.settings()
                top = settings.get('line_padding_top', 0)
                bottom = settings.get('line_padding_bottom', 0)
                body = f"""<style>
                    body {{ background-color: #F7D3D5; padding-top: {top}px; padding-bottom: {bottom}px; }}
                    p {{ margin: 0; padding-top: {top}px; padding-bottom: {bottom}px; }}
                </style>"""
                for line in html.escape(self.trace).split("\n"):
                    body += "<p>" + line.replace("\t", "&nbsp;&nbsp;") + "</p>"
                region = self.region()
                if region:
                    point = self.view.line(region.end()).begin()
                    self.trace_key = self.view.add_phantom(self.value_key(), sublime.Region(point, point), body, sublime.LAYOUT_BLOCK)

    def erase(self):
        self.view.erase_regions(self.value_key())
        if self.trace_key:
            self.view.erase_phantom_by_id(self.trace_key)

class Connection:
    def __init__(self):
        self.host = 'localhost'
        self.port = 5555
        self.evals: dict[int, Eval] = {}
        self.reset()

    def set_status(self, status):
        self.status = status
        self.refresh_status()

    def refresh_status(self):
        if sublime.active_window():
            view = sublime.active_window().active_view()
            if view:
                view.set_status(ns, self.status)

    def send(self, msg):
        print(">>>", msg)
        self.socket.sendall(bencode.encode(msg).encode())

    def reset(self):
        self.socket = None
        self.reader = None
        self.session = None
        self.set_status('🌑 Offline')
        for id, eval in self.evals.items():
            eval.erase()
        self.evals.clear()

    def add_eval(self, eval):
        self.evals[eval.id] = eval

    def erase_eval(self, eval):
        eval.erase()
        del self.evals[eval.id]

    def erase_evals(self, predicate, view = None):
        for id, eval in list(self.evals.items()):
            if (view == None or view == eval.view) and predicate(eval):
                self.erase_eval(eval)

    def disconnect(self):
        if self.socket:
            self.socket.close()
            self.reset()

conn = Connection()

def handle_new_session(msg):
    if "new-session" in msg and "id" in msg and msg["id"] in conn.evals:
        eval = conn.evals[msg["id"]]
        eval.session = msg["new-session"]
        eval.msg["session"] = msg["new-session"]
        conn.send(eval.msg)
        eval.update("eval", "Evaluating...")
        return True

def handle_value(msg):
    if "value" in msg and "id" in msg and msg["id"] in conn.evals:
        eval = conn.evals[msg["id"]]
        eval.update("success", msg.get("value"))
        return True

def handle_exception(msg):
    if "id" in msg and msg["id"] in conn.evals:
        eval = conn.evals[msg["id"]]
        get = lambda key: msg.get(ns + ".middleware/" + key)
        if get("root-ex-class") and get("root-ex-msg"):
            text = get("root-ex-class") + ": " + get("root-ex-msg")
            region = None
            if get("root-ex-data"):
                text += " " + get("root-ex-data")
            if get("line") and get("column"):
                line = get("line")
                column = get("column")
                point = eval.view.text_point_utf16(line - 1, column - 1, clamp_column = True)
                region = sublime.Region(point, eval.view.line(point).end())
            eval.trace = get("trace")
            eval.update("exception", text, region)
            return True
        elif "root-ex" in msg:
            eval.update("exception", msg["root-ex"])
            return True
        elif "ex" in msg:
            eval.update("exception", msg["ex"])
            return True        
        elif "status" in msg and "namespace-not-found" in msg["status"]:
            eval.update("exception", f'Namespace not found: {msg["ns"]}')

def namespace(view, point):
    ns = None
    for region in view.find_by_selector("entity.name"):
        if region.end() <= point:
            begin = region.begin()
            while begin > 0 and view.match_selector(begin - 1, 'meta.parens'):
                begin -= 1
            if re.match(r"\([\s,]*ns[\s,]", view.substr(sublime.Region(begin, region.begin()))):
                ns = view.substr(region)
        else:
            break
    return ns

def eval_msg(view, region, msg):
    extended_region = view.line(region)
    conn.erase_evals(lambda eval: eval.region() and eval.region().intersects(extended_region), view)
    eval = Eval(view, region, "clone", "Cloning...")
    eval.msg = {k: v for k, v in msg.items() if v}
    eval.msg["id"] = eval.id
    eval.msg["nrepl.middleware.caught/caught"] = f"{ns}.middleware/print-root-trace"
    eval.msg["nrepl.middleware.print/quota"] = 300
    conn.add_eval(eval)
    conn.send({"op": "clone", "session": conn.session, "id": eval.id})

def eval(view, region):
    (line, column) = view.rowcol_utf16(region.begin())
    msg = {"op":     "eval",
           "code":   view.substr(region),
           "ns":     namespace(view, region.begin()) or 'user',
           "line":   line,
           "column": column,
           "file":   view.file_name()}
    eval_msg(view, region, msg)
    
def expand_until(view, point, scopes):
    if view.scope_name(point) in scopes and point > 0:
        point = point - 1
    if view.scope_name(point) not in scopes:
        begin = point
        while begin > 0 and view.scope_name(begin - 1) not in scopes:
            begin -= 1
        end = point
        while end < view.size() and view.scope_name(end) not in scopes:
            end += 1
        return sublime.Region(begin, end)

def topmost_form(view, point):
    region = expand_until(view, point, {'source.clojure '})
    if region \
       and view.substr(region).startswith("(comment") \
       and point >= region.begin() + len("(comment ") \
       and point < region.end():
        return expand_until(view, point, {'source.clojure meta.parens.clojure ',
                                          'source.clojure meta.parens.clojure punctuation.section.parens.end.clojure '})
    return region

class EvalTopmostFormCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        point = self.view.sel()[0].begin()
        region = topmost_form(self.view, point)
        if region:
            eval(self.view, region)

    def is_enabled(self):
        return conn.socket != None \
            and conn.session != None \
            and len(self.view.sel()) == 1

class EvalSelectionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        region = self.view.sel()[0]
        eval(self.view, region)
        
    def is_enabled(self):
        return conn.socket != None \
            and conn.session != None \
            and len(self.view.sel()) == 1 \
            and not self.view.sel()[0].empty()

class EvalBufferCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        region = sublime.Region(0, view.size())
        file_name = view.file_name()
        msg = {"op":        "load-file",
               "file":      view.substr(region),
               "file-path": file_name,
               "file-name": os.path.basename(file_name) if file_name else "NO_SOURCE_FILE.cljc"}
        eval_msg(view, region, msg)
        
    def is_enabled(self):
        return conn.socket != None \
            and conn.session != None

class ClearEvalsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        conn.erase_evals(lambda eval: eval.status in {"success", "exception"}, self.view)

class InterruptEvalCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        print("evals", conn.evals)
        for eval in conn.evals.values():
            if eval.status == "eval":
                conn.send({"op":           "interrupt",
                           "session":      eval.session,
                           "interrupt-id": eval.id})
                eval.update("interrupt", "Interrupting...")

    def is_enabled(self):
        return conn.socket != None \
            and conn.session != None

class ToggleTraceCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        point = view.sel()[0].begin()
        for eval in conn.evals.values():
            if eval.view == view:
                region = eval.region()
                if region and region.contains(point):
                    eval.toggle_trace()
                    break
        
    def is_enabled(self):
        return conn.socket != None \
            and conn.session != None \
            and len(self.view.sel()) == 1

def format_lookup(info):
    ns = info.get('ns')
    name = info['name']
    file = info.get('file')
    arglists = info.get('arglists')
    forms = info.get('forms')
    doc = info.get('doc')

    body = """<body>
              <style>
                body { padding: 0; margin: 0; }
                a { text-decoration: none; }
                p { margin: 0; padding: .25rem .5rem; }
                .arglists { color: color(var(--foreground) alpha(0.5)); }
              </style>"""

    body += "<p>"
    if file:
        body += f"<a href='{file}'>"
    if ns:
        body += html.escape(ns) + "/"
    body += html.escape(name)
    if file:
        body += f"</a>"
    body += "</p>"

    if arglists:
        body += f'<p class="arglists">{html.escape(arglists.strip("()"))}</p>'

    if forms:
        def format_form(form):
            if isinstance(form, str):
                return form
            else:
                return "(" + " ".join([format_form(x) for x in form]) + ")"
        body += '<p class="arglists">'
        body += html.escape(" ".join([format_form(form) for form in forms]))
        body += "</p>"

    if doc:
        body += "<p>" + html.escape(doc).replace("\n", "<br/>") + "</p>"

    body += "</body>"
    return body

def handle_lookup(msg):
    if "info" in msg:
        view = sublime.active_window().active_view()
        if msg["info"]:
            view.show_popup(format_lookup(msg["info"]), max_width=1024)
        else:
            view.show_popup("Not found")

class LookupSymbolCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        region = self.view.sel()[0]
        if region.empty():
            point = region.begin()
            if view.match_selector(point, 'source.symbol.clojure'):
                region = self.view.extract_scope(point)
            elif point > 0 and view.match_selector(point - 1, 'source.symbol.clojure'):
                region = self.view.extract_scope(point - 1)
        if not region.empty():
            conn.send({"op":      "lookup",
                       "sym":     view.substr(region),
                       "session": conn.session,
                       "id":      Eval.next_id,
                       "ns":      namespace(view, region.begin()) or 'user'})
            Eval.next_id += 1

    def is_enabled(self):
        if conn.socket == None or conn.session == None:
            return False
        view = self.view
        if len(view.sel()) > 1:
            return False
        region = view.sel()[0]
        if not region.empty():
            return True
        point = region.begin()
        if view.match_selector(point, 'source.symbol.clojure'):
            return True
        if point > 0 and view.match_selector(point - 1, 'source.symbol.clojure'):
            return True
        return False

class EventListener(sublime_plugin.EventListener):
    def on_activated(self, view):
        conn.refresh_status()

    def on_modified_async(self, view):
        conn.erase_evals(lambda eval: eval.region() and view.substr(eval.region()) != eval.code, view)

    def on_close(self, view):
        conn.erase_evals(lambda eval: True, view)

class SocketIO:
    def __init__(self, socket):
        self.socket = socket
        self.buffer = None
        self.pos = -1

    def read(self, n):
        if not self.buffer or self.pos >= len(self.buffer):
            self.buffer = self.socket.recv(4096)
            # print("<<<", self.buffer.decode())
            self.pos = 0
        begin = self.pos
        end = min(begin + n, len(self.buffer))
        self.pos = end
        return self.buffer[begin:end]

def handle_connect(msg):
    if 1 == msg.get("id") and "new-session" in msg:
        conn.session = msg["new-session"]
        conn.send({"op": "load-file",
                   "session": conn.session,
                   "file": sublime.load_resource(f"Packages/{package}/src/middleware.clj"),
                   "id": 2})
        conn.set_status("🌓 Uploading middlewares")
        return True

    elif 2 == msg.get("id") and msg.get("status") == ["done"]:
        conn.send({"op":               "add-middleware",
                   "middleware":       [f"{ns}.middleware/wrap-errors",
                                        f"{ns}.middleware/wrap-output"],
                   "extra-namespaces": [f"{ns}.middleware"],
                   "session":          conn.session,
                   "id":               3})
        conn.set_status("🌔 Adding middlewares")
        return True

    elif 3 == msg.get("id") and msg.get("status") == ["done"]:
        conn.set_status(f"🌕 {conn.host}:{conn.port}")
        return True

def handle_done(msg):
    if "id" in msg and msg["id"] in conn.evals and "status" in msg and "done" in msg["status"]:
        eval = conn.evals[msg["id"]]
        if eval.status not in {"success", "exception"}:
            conn.erase_eval(eval)

def handle_msg(msg):
    print("<<<", msg)

    for key in msg.get('nrepl.middleware.print/truncated-keys', []):
        msg[key] += '...'

    handle_connect(msg) \
    or handle_new_session(msg) \
    or handle_value(msg) \
    or handle_exception(msg) \
    or handle_lookup(msg) \
    or handle_done(msg)

def read_loop():
    try:
        conn.pending_id = 1
        conn.send({"op": "clone", "id": conn.pending_id})
        conn.set_status(f"🌒 Cloning session")
        for msg in bencode.decode_file(SocketIO(conn.socket)):
            handle_msg(msg)
    except OSError:
        pass
    conn.disconnect()

def connect(host, port):
    conn.host = host
    conn.port = port
    try:
        conn.socket = socket.create_connection((host, port))
        conn.reader = threading.Thread(daemon=True, target=read_loop)
        conn.reader.start()
    except Exception as e:
        print(e)
        conn.socket = None
        conn.set_status(f"🌑 {host}:{port}")

class HostPortInputHandler(sublime_plugin.TextInputHandler):
    def placeholder(self):
        return "host:port"

    def initial_text(self):
        if conn.host and conn.port:
            return f'{conn.host}:{conn.port}'

    def preview(self, text):
        if not self.validate(text):
            return "Invalid, expected <host>:<port>"

    def validate(self, text):
        text = text.strip()
        if not re.fullmatch(r'[a-zA-Z0-9\.]+:\d{1,5}', text):
            return False
        host, port = text.split(':')
        port = int(port)
        return 0 <= port and port <= 65536

class ConnectCommand(sublime_plugin.ApplicationCommand):
    def run(self, host_port):
        host, port = host_port.strip().split(':')
        port = int(port)
        connect(host, port)

    def input(self, args):
        return HostPortInputHandler()

    def is_enabled(self):
        return conn.socket == None

class DisconnectCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        conn.disconnect()

    def is_enabled(self):
        return conn.socket != None

class ReconnectCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        conn.disconnect()
        connect(conn.host, conn.port)

    def is_enabled(self):
        return conn.socket != None

def plugin_loaded():
    connect('localhost', 5555) # FIXME

def plugin_unloaded():
    conn.disconnect()


