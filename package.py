import html, json, os, re, socket, sublime, sublime_plugin, threading, time
from collections import defaultdict
from .src import bencode
from typing import Any, Dict, Tuple

ns = 'sublime-clojure'

def settings():
    return sublime.load_settings("Sublime Clojure.sublime-settings")

class Eval:
    # class
    next_id:   int = 10
    colors:    Dict[str, Tuple[str, str]] = {}

    # instance
    id:         int
    view:       sublime.View
    status:     str # "pending" | "interrupt" | "success" | "exception" | "lookup"
    code:       str
    session:    str
    msg:        Dict[str, Any]
    trace:      str
    phantom_id: int
    
    def __init__(self, view, region):
        self.id = Eval.next_id
        self.view = view
        self.code = view.substr(region)
        self.session = None
        self.msg = None
        self.trace = None
        self.phantom_id = None
        self.start_time = None
        Eval.next_id += 1
        self.update("pending", None, region)

    def value_key(self):
        return f"{ns}.eval-{self.id}"

    def scope_color(self):
        if not Eval.colors:
            default = self.view.style_for_scope("source")
            def try_scopes(*scopes):
                for scope in scopes:
                    colors = self.view.style_for_scope(scope)
                    if colors != default:
                        return (scope, colors["foreground"])
            Eval.colors["pending"]   = try_scopes("region.eval.pending",   "region.bluish")
            Eval.colors["interrupt"] = try_scopes("region.eval.interrupt", "region.eval.pending", "region.bluish")
            Eval.colors["success"]   = try_scopes("region.eval.success",   "region.greenish")
            Eval.colors["exception"] = try_scopes("region.eval.exception", "region.redish")
            Eval.colors["lookup"]    = try_scopes("region.eval.lookup",    "region.eval.pending",   "region.bluish")
        return Eval.colors[self.status]

    def region(self):
        regions = self.view.get_regions(self.value_key())
        if regions and len(regions) >= 1:
            return regions[0]

    def update(self, status, value, region = None):
        self.status = status
        region = region or self.region()
        if region:
            scope, color = self.scope_color()
            if value:
                threshold = settings().get("elapsed_threshold_ms")
                if threshold != None and self.start_time and self.status in {"success", "exception"}:
                    elapsed = time.perf_counter() - self.start_time
                    if elapsed * 1000 >= threshold:
                        if elapsed >= 10:
                            value = f"({'{:,.0f}'.format(elapsed)} sec) {value}"
                        elif elapsed >= 1:
                            value = f"({'{:.1f}'.format(elapsed)} sec) {value}"
                        elif elapsed >= 0.005:
                            value = f"({'{:.0f}'.format(elapsed * 1000)} ms) {value}"
                        else:
                            value = f"({'{:.2f}'.format(elapsed * 1000)} ms) {value}"
                self.view.add_regions(self.value_key(), [region], scope, '', sublime.DRAW_NO_FILL, [html.escape(value)], color)
            else:
                self.view.erase_regions(self.value_key())
                self.view.add_regions(self.value_key(), [region], scope, '', sublime.DRAW_NO_FILL)

    def toggle_trace(self):
        if self.trace:
            if self.phantom_id:
                self.view.erase_phantom_by_id(self.phantom_id)
                self.phantom_id = None
            else:
                body = f"""<body id='sublime-clojure'>
                    { basic_styles(self.view) }
                    .light body {{ background-color: hsl(0, 100%, 90%); }}
                    .dark body  {{ background-color: hsl(0, 100%, 10%); }}
                </style>"""
                for line in html.escape(self.trace).split("\n"):
                    body += "<p>" + line.replace("\t", "&nbsp;&nbsp;") + "</p>"
                body += "</body>"
                region = self.region()
                if region:
                    point = self.view.line(region.end()).begin()
                    self.phantom_id = self.view.add_phantom(self.value_key(), sublime.Region(point, point), body, sublime.LAYOUT_BLOCK)

    def erase(self):
        self.view.erase_regions(self.value_key())
        if self.phantom_id:
            self.view.erase_phantom_by_id(self.phantom_id)

class StatusEval(Eval):
    def __init__(self, code):
        self.id = Eval.next_id
        self.view = None
        self.code = code
        self.session = None
        self.msg = None
        self.trace = None
        self.start_time = None
        Eval.next_id += 1
        self.update("pending", None)

    def region(self):
        return None

    def active_view(self):
        if window := sublime.active_window():
            return window.active_view()

    def update(self, status, value, region = None):
        self.status = status
        self.value = value
        if self.active_view():
            if status in {"pending", "interrupt"}:
                self.active_view().set_status(self.value_key(), "⏳ " + self.code)
            elif "success" == status:
                self.active_view().set_status(self.value_key(), "✅ " + value)
            elif "exception" == status:
                self.active_view().set_status(self.value_key(), "❌ " + value)

    def erase(self):
        if self.active_view():
            self.active_view().erase_status(self.value_key())

def regions_touch(r1, r2):
    return r1 != None and r2 != None and not r1.end() < r2.begin() and not r1.begin() > r2.end()

class Connection:
    host: str
    port: str
    status: str
    evals: Dict[int, Eval]
    last_view: sublime.View

    def __init__(self):
        self.host = 'localhost'
        self.port = None
        self.evals = {}
        self.reset()
        self.last_view = window.active_view() if (window := sublime.active_window()) else None

    def set_status(self, status):
        self.status = status
        self.refresh_status()

    def refresh_status(self):
        if window := sublime.active_window():
            if view := window.active_view():
                if self.status:
                    view.set_status(ns, self.status)
                else:
                    view.erase_status(ns)
                for eval in self.evals.values():
                    if isinstance(eval, StatusEval):
                        if self.last_view and view != self.last_view:
                            self.last_view.erase_status(eval.value_key())
                        eval.update(eval.status, eval.value)
            self.last_view = view

    def send(self, msg):
        if settings().get("debug"):
            print("SND", msg)
        self.socket.sendall(bencode.encode(msg).encode())

    def reset(self):
        self.socket = None
        self.reader = None
        self.session = None
        self.set_status(None)
        for id, eval in self.evals.items():
            eval.erase()
        self.evals.clear()

    def add_eval(self, eval):
        self.evals[eval.id] = eval

    def erase_eval(self, eval):
        eval.erase()
        del self.evals[eval.id]

    def find_eval(self, view, region):
        for eval in self.evals.values():
            if eval.view == view and regions_touch(eval.region(), region):
                return eval

    def erase_evals(self, predicate, view = None):
        for id, eval in list(self.evals.items()):
            if (view == None or view == eval.view) and predicate(eval):
                self.erase_eval(eval)

    def disconnect(self):
        if self.socket:
            self.socket.close()
            self.reset()

    def ready(self):
        return bool(self.socket and self.session)

def handle_new_session(msg):
    if "new-session" in msg and "id" in msg and msg["id"] in conn.evals:
        eval = conn.evals[msg["id"]]
        eval.session = msg["new-session"]
        eval.msg["session"] = msg["new-session"]
        eval.start_time = time.perf_counter()
        conn.send(eval.msg)
        eval.update("pending", progress_thread.phase())
        return True

def handle_value(msg):
    if "value" in msg and "id" in msg and msg["id"] in conn.evals:
        eval = conn.evals[msg["id"]]
        eval.update("success", msg.get("value"))
        return True

def set_selection(view, region):
    sel = view.sel()
    sel.clear()
    sel.add(region)
    view.show(region, show_surrounds = True, keep_to_left = True, animate = True)

def handle_exception(msg):
    if "id" in msg and msg["id"] in conn.evals:
        eval = conn.evals[msg["id"]]
        get = lambda key: msg.get(ns + ".middleware/" + key)
        if get("root-ex-class") and get("root-ex-msg"):
            text = get("root-ex-class") + ": " + get("root-ex-msg")
            region = None
            if get("root-ex-data"):
                text += " " + get("root-ex-data")
            if get("line") and get("column") and eval.view:
                line = get("line")
                column = get("column")
                point = eval.view.text_point_utf16(line - 1, column - 1, clamp_column = True)
                region = sublime.Region(point, eval.view.line(point).end())
                set_selection(eval.view, sublime.Region(point, point))
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

class ProgressThread:
    def __init__(self):
        self.running = False
        self.condition = threading.Condition()
        self.phases = None
        self.phase_idx = 0
        self.interval = 100

    def update_phases(self, phases, interval):
        self.phases = phases
        self.phase_idx = 0
        self.interval = interval
        if len(phases) > 1:
            self.start()
        else:
            self.stop()

    def phase(self):
        return self.phases[self.phase_idx]

    def run_loop(self):
        while True:
            if not self.running:
                break
            time.sleep(self.interval / 1000.0)
            updated = False
            if (window := sublime.active_window()) and (view := window.active_view()):
                for eval in list(conn.evals.values()):
                    if eval.view == view and eval.status == "pending":
                        eval.update(eval.status, self.phase())
                        updated = True
            if updated:
                self.phase_idx = (self.phase_idx + 1) % len(self.phases)
            else:
                with self.condition:
                    self.condition.wait()

    def start(self):
        if not self.running:
            self.running = True
            threading.Thread(daemon=True, target=self.run_loop).start()

    def wake(self):
        if self.running:
            with self.condition:
                self.condition.notify_all()

    def stop(self):
        self.running = False
        with self.condition:
            self.condition.notify_all()
        
def eval_msg(view, region, msg):
    extended_region = view.line(region)
    conn.erase_evals(lambda eval: eval.region() and eval.region().intersects(extended_region), view)
    eval = Eval(view, region)
    progress_thread.wake()
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

class SublimeClojureEval(sublime_plugin.TextCommand):
    def run(self, edit):
        covered = []
        for sel in self.view.sel():
            if all([not sel.intersects(r) for r in covered]):
                if sel.empty():
                    region = topmost_form(self.view, sel.begin())
                    if region:
                        covered.append(region)
                        eval(self.view, region)
                else:
                    covered.append(sel)
                    eval(self.view, sel)

    def is_enabled(self):
        return conn.ready()

class SublimeClojureEvalBufferCommand(sublime_plugin.TextCommand):
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
        return conn.ready()

class SublimeClojureEvalCodeCommand(sublime_plugin.ApplicationCommand):
    def run(self, code):
        conn.erase_evals(lambda eval: isinstance(eval, StatusEval) and eval.status not in {"pending", "interrupt"})
        eval = StatusEval(code)
        ns = 'user'
        view = eval.active_view()
        if view:
            ns = namespace(view, view.size()) or 'user'
        eval.msg = {"op": "eval",
                    "id": eval.id,
                    "ns": ns,
                    "code": code,
                    "nrepl.middleware.caught/caught": f"{ns}.middleware/print-root-trace",
                    "nrepl.middleware.print/quota": 300}
        conn.add_eval(eval)
        conn.send({"op": "clone", "session": conn.session, "id": eval.id})

    def is_enabled(self):
        return conn.ready()

class SublimeClojureClearEvalsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        conn.erase_evals(lambda eval: eval.status not in {"pending", "interrupt"}, self.view)
        conn.erase_evals(lambda eval: isinstance(eval, StatusEval) and eval.status not in {"pending", "interrupt"})

class SublimeClojureInterruptEvalCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        for eval in conn.evals.values():
            if eval.status == "pending":
                conn.send({"op":           "interrupt",
                           "session":      eval.session,
                           "interrupt-id": eval.id})
                eval.update("interrupt", "Interrupting...")

    def is_enabled(self):
        return conn.ready()

class SublimeClojureToggleTraceCommand(sublime_plugin.TextCommand):
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
        return conn.ready() and len(self.view.sel()) == 1

def basic_styles(view):
    settings = view.settings()
    top = settings.get('line_padding_top', 0)
    bottom = settings.get('line_padding_bottom', 0)
    return f"""<style>
        body {{ margin: 0 0 {top+bottom}px 0; padding: {bottom}px 1rem {top}px 1rem; }}
        p {{ margin: 0; padding: {top}px 0 {bottom}px 0; }}
    """

def format_lookup(view, info):
    settings = view.settings()
    top = settings.get('line_padding_top', 0)
    bottom = settings.get('line_padding_bottom', 0)
    body = f"""<body id='sublime-clojure'>
        {basic_styles(view)}
        .dark body  {{ background-color: color(var(--background) blend(#FFF 90%)); }}
        .light body {{ background-color: color(var(--background) blend(#000 95%)); }}
        a           {{ text-decoration: none; }}
        .arglists   {{ color: color(var(--foreground) alpha(0.5)); }}
    </style>"""

    if not info:
        body += "<p>Not found</p>"
    else:
        ns = info.get('ns')
        name = info['name']
        file = info.get('file')
        arglists = info.get('arglists')
        forms = info.get('forms')
        doc = info.get('doc')

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
            body += "<p>" + "</p><p>".join(html.escape(doc).split("\n")) + "</p>"
    body += "</div>"
    return body

def handle_lookup(msg):
    if "info" in msg and "id" in msg and msg["id"] in conn.evals:
        eval = conn.evals[msg["id"]]
        eval.update("lookup", None)
        view = eval.view
        body = format_lookup(view, msg["info"])
        point = view.line(eval.region().end()).begin()
        eval.phantom_id = view.add_phantom(eval.value_key(), sublime.Region(point, point), body, sublime.LAYOUT_BLOCK)
        return True

class SublimeClojureToggleSymbolCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        for sel in view.sel():
            eval = conn.find_eval(view, sel)
            if eval and eval.phantom_id:
                conn.erase_eval(eval)
            else:
                region = sel
                if region.empty():
                    point = region.begin()
                    if view.match_selector(point, 'source.symbol.clojure'):
                        region = self.view.extract_scope(point)
                    elif point > 0 and view.match_selector(point - 1, 'source.symbol.clojure'):
                        region = self.view.extract_scope(point - 1)

                if region:
                    line = view.line(region)
                    conn.erase_evals(lambda eval: eval.region() and eval.region().intersects(line), view)
                    eval = Eval(view, region)
                    progress_thread.wake()
                    conn.add_eval(eval)
                    conn.send({"op":      "lookup",
                               "sym":     view.substr(region),
                               "session": conn.session,
                               "id":      eval.id,
                               "ns":      namespace(view, region.begin()) or 'user'})

    def is_enabled(self):
        return conn.ready()

class SublimeClojureToggleInfoCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        for sel in view.sel():
            eval = conn.find_eval(view, sel)
            if eval and eval.status == "exception":
                view.run_command("sublime_clojure_toggle_trace", {})
            else:
                view.run_command("sublime_clojure_toggle_symbol", {})

    def is_enabled(self):
        return conn.ready()

class SocketIO:
    def __init__(self, socket):
        self.socket = socket
        self.buffer = None
        self.pos = -1

    def read(self, n):
        if not self.buffer or self.pos >= len(self.buffer):
            self.buffer = self.socket.recv(4096)
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
    if settings().get("debug"):
        print("RCV", msg)

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
        conn.socket = None
        conn.set_status(None)
        if window := sublime.active_window():
            window.status_message(f"Failed to connect to {host}:{port}")

class SublimeClojureHostPortInputHandler(sublime_plugin.TextInputHandler):
    def placeholder(self):
        return "host:port"

    def initial_text(self):
        port = ''
        if conn.port:
            port = str(conn.port)
        if window := sublime.active_window():
            for folder in window.folders():
                if os.path.exists(folder + "/.nrepl-port"):
                    with open(folder + "/.nrepl-port", "rt") as f:
                        content = f.read(10).strip()
                        if re.fullmatch(r'[1-9][0-9]*', content):
                            port = content
        return conn.host + ":" + port

    def initial_selection(self):
        return [(len(conn.host + ":"), len(self.initial_text()))]

    def preview(self, text):
        if not self.validate(text):
            return "Expected <host>:<port>"

    def validate(self, text):
        text = text.strip()
        if not re.fullmatch(r'[a-zA-Z0-9\.]+:\d{1,5}', text):
            return False
        host, port = text.split(':')
        port = int(port)
        return 0 <= port and port <= 65536

class SublimeClojureConnectCommand(sublime_plugin.ApplicationCommand):
    def run(self, sublime_clojure_host_port):
        host, port = sublime_clojure_host_port.strip().split(':')
        port = int(port)
        connect(host, port)

    def input(self, args):
        return SublimeClojureHostPortInputHandler()

    def is_enabled(self):
        return conn.socket == None

class SublimeClojureDisconnectCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        conn.disconnect()

    def is_enabled(self):
        return conn.socket != None

class SublimeClojureReconnectCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        conn.disconnect()
        connect(conn.host, conn.port)

    def is_enabled(self):
        return conn.socket != None

class SublimeClojureEventListener(sublime_plugin.EventListener):
    def on_activated_async(self, view):
        conn.refresh_status()
        progress_thread.wake()

    def on_modified_async(self, view):
        conn.erase_evals(lambda eval: not eval.region() or view.substr(eval.region()) != eval.code, view)

    def on_close(self, view):
        conn.erase_evals(lambda eval: True, view)

def on_settings_change():
    Eval.colors.clear()
    progress_thread.update_phases(settings().get("progress_phases"), settings().get("progress_interval_ms"))

def plugin_loaded():
    global package, conn, progress_thread

    package_path = os.path.dirname(os.path.abspath(__file__))
    if os.path.isfile(package_path):
        # Package is a .sublime-package so get its filename
        package, _ = os.path.splitext(os.path.basename(package_path))
    elif os.path.isdir(package_path):
        # Package is a directory, so get its basename
        package = os.path.basename(package_path)

    conn = Connection()
    progress_thread = ProgressThread()

    sublime.load_settings("Preferences.sublime-settings").add_on_change(ns, on_settings_change)
    settings().add_on_change(ns, on_settings_change)
    on_settings_change()

def plugin_unloaded():
    progress_thread.stop()
    conn.disconnect()
    sublime.load_settings("Preferences.sublime-settings").clear_on_change(ns)
    settings().clear_on_change(ns)
