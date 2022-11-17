import html, json, os, re, socket, sublime, sublime_plugin, threading, time
from collections import defaultdict
import operator as op
import functools as fn
from .src import bencode
from typing import Any, Dict, Tuple
import logging

ns = 'clojure-sublimed'

_log = logging.getLogger(__name__)


def settings():
    return sublime.load_settings("Clojure Sublimed.sublime-settings")

def format_time_taken(time_taken):
    threshold = settings().get("elapsed_threshold_ms")
    if threshold != None and time_taken != None:
        elapsed = time_taken / 1000000000
        if elapsed * 1000 >= threshold:
            if elapsed >= 10:
                return f"({'{:,.0f}'.format(elapsed)} sec)"
            elif elapsed >= 1:
                return f"({'{:.1f}'.format(elapsed)} sec)"
            elif elapsed >= 0.005:
                return f"({'{:.0f}'.format(elapsed * 1000)} ms)"
            else:
                return f"({'{:.2f}'.format(elapsed * 1000)} ms)"


def get_middleware_opts(conn):
    """Returns middleware options to send to nREPL as a dict.
    Currently only Clojure profile supports middleware.
    """
    if conn and conn.profile == Profile.CLOJURE:
        return {
            "nrepl.middleware.caught/caught": f"{ns}.middleware/print-root-trace",
            "nrepl.middleware.print/print": f"{ns}.middleware/pprint",
            "nrepl.middleware.print/quota": 4096
        }
    return {}


class Profile:
    CLOJURE = 'clojure'
    SHADOW_CLJS = 'shadow-cljs'


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
        self.value = None
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

    def update(self, status, value, region = None, time_taken = None):
        self.status = status
        self.value = value
        region = region or self.region()
        if region:
            scope, color = self.scope_color()
            if value:
                if (self.status in {"success", "exception"}) and (time := format_time_taken(time_taken)):
                    value = time + " " + value
                self.view.add_regions(self.value_key(), [region], scope, '', sublime.DRAW_NO_FILL + sublime.NO_UNDO, [html.escape(value)], color)
            else:
                self.view.erase_regions(self.value_key())
                self.view.add_regions(self.value_key(), [region], scope, '', sublime.DRAW_NO_FILL + sublime.NO_UNDO)

    def toggle_phantom(self, text, styles):
        if text:
            if self.phantom_id:
                self.view.erase_phantom_by_id(self.phantom_id)
                self.phantom_id = None
            else:
                body = f"""<body id='clojure-sublimed'>
                    { basic_styles(self.view) }
                    { styles }
                </style>"""
                for line in html.escape(text).split("\n"):
                    body += "<p>" + line.replace("\t", "&nbsp;&nbsp;").replace(" ", "&nbsp;") + "</p>"
                body += "</body>"
                region = self.region()
                if region:
                    point = self.view.line(region.end()).begin()
                    self.phantom_id = self.view.add_phantom(self.value_key(), sublime.Region(point, point), body, sublime.LAYOUT_BLOCK)

    def toggle_pprint(self):
        self.toggle_phantom(self.value, """
            .light body { background-color: hsl(100, 100%, 90%); }
            .dark body  { background-color: hsl(100, 100%, 10%); }
        """)
        
    def toggle_trace(self):
        self.toggle_phantom(self.trace, """
            .light body { background-color: hsl(0, 100%, 90%); }
            .dark body  { background-color: hsl(0, 100%, 10%); }
        """)

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
        Eval.next_id += 1
        self.update("pending", None)

    def region(self):
        return None

    def active_view(self):
        if window := sublime.active_window():
            return window.active_view()

    def update(self, status, value, region = None, time_taken = None):
        self.status = status
        self.value = value
        if self.active_view():
            if status in {"pending", "interrupt"}:
                self.active_view().set_status(self.value_key(), "⏳ " + self.code)
            elif "success" == status:
                if time := format_time_taken(time_taken):
                    value = time + ' ' + value
                self.active_view().set_status(self.value_key(), "✅ " + value)
            elif "exception" == status:
                if time := format_time_taken(time_taken):
                    value = time + ' ' + value
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
    evals_by_view: Dict[int, Dict[int, Eval]]
    last_view: sublime.View
    session: str
    eval_in_session: bool
    profile: Profile
    cljs_build: str

    def __init__(self):
        self.host = 'localhost'
        self.port = None
        self.evals = {}
        self.evals_by_view = defaultdict(dict)
        self.reset()
        self.last_view = window.active_view() if (window := sublime.active_window()) else None
        self.session = None
        self.eval_in_session = None
        self.profile = None
        self.cljs_build = None

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
        self.evals_by_view.clear()

    def add_eval(self, eval):
        self.evals[eval.id] = eval
        if view := eval.view:
            self.evals_by_view[view.id()][eval.id] = eval

    def erase_eval(self, eval):
        eval.erase()
        del self.evals[eval.id]
        if view := eval.view:
            del self.evals_by_view[view.id()][eval.id]
        if eval.status == "pending" and eval.session:
            conn.send({"op": "interrupt", "interrupt-id": eval.id, "session": eval.session})

    def find_eval(self, view, region):
        for eval in self.evals_by_view[view.id()].values():
            if regions_touch(eval.region(), region):
                return eval

    def erase_evals(self, predicate, view = None):
        evals = list(self.evals.items()) if view is None else list(self.evals_by_view[view.id()].items())
        for id, eval in evals:
            if predicate(eval):
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
        return True

def handle_value(msg):
    if "value" in msg and "id" in msg and msg["id"] in conn.evals:
        eval = conn.evals[msg["id"]]
        eval.update("success", msg.get("value"), time_taken = msg.get(f'{ns}.middleware/time-taken'))
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
            elif get("line") and get("column") and get("source"):
                text += " ({}:{}:{})".format(get("source"), get("line"), get("column"))
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
                for eval in list(conn.evals_by_view[view.id()].values()):
                    if eval.status == "pending":
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
    eval.msg["session"] = conn.session
    eval.msg.update(get_middleware_opts(conn))

    conn.add_eval(eval)
    conn.send(eval.msg)
    eval.update("pending", progress_thread.phase())

def eval(view, region, code=None):
    (line, column) = view.rowcol_utf16(region.begin())
    msg = {"op":     "eval" if (conn.profile == Profile.SHADOW_CLJS or conn.eval_in_session) else "clone-eval-close",
           "code":   view.substr(region) if code is None else code,
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
    # move left to first non-space
    if point >= view.size() or view.substr(sublime.Region(point, point + 1)).isspace():
        while point > 0 and view.substr(sublime.Region(point - 1, point)).isspace():
            point = point - 1

    region = expand_until(view, point, {'source.clojure '})
    if region \
       and view.substr(region).startswith("(comment") \
       and point >= region.begin() + len("(comment ") \
       and point < region.end():
        return expand_until(view, point, {'source.clojure meta.parens.clojure ',
                                          'source.clojure meta.parens.clojure punctuation.section.parens.end.clojure '})
    return region

class ClojureSublimedEval(sublime_plugin.TextCommand):
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

class ClojureSublimedEvalBufferCommand(sublime_plugin.TextCommand):
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

class ClojureSublimedEvalCodeCommand(sublime_plugin.ApplicationCommand):
    def run(self, code, ns = None):
        conn.erase_evals(lambda eval: isinstance(eval, StatusEval) and eval.status not in {"pending", "interrupt"})
        eval = StatusEval(code)
        if (not ns) and (view := eval.active_view()):
            ns = namespace(view, view.size())
        eval.msg = {"op": "eval",
                    "id": eval.id,
                    "ns": ns or 'user',
                    "code": code}
        eval.msg.update(get_middleware_opts(conn))        
        conn.add_eval(eval)
        conn.send(eval.msg)
        eval.update("pending", progress_thread.phase())

    def is_enabled(self):
        return conn.ready()

class ClojureSublimedCopyCommand(sublime_plugin.TextCommand):
    def eval(self):
        view = self.view
        return conn.find_eval(view, view.sel()[0])

    def run(self, edir):
        if conn.ready() and len(self.view.sel()) == 1 and self.view.sel()[0].empty() and (eval := self.eval()) and eval.value:
            sublime.set_clipboard(eval.value)
        else:
            self.view.run_command("copy", {})

class ClojureSublimedClearEvalsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        conn.erase_evals(lambda eval: eval.status not in {"pending", "interrupt"}, self.view)
        conn.erase_evals(lambda eval: isinstance(eval, StatusEval) and eval.status not in {"pending", "interrupt"})

class ClojureSublimedInterruptEvalCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        for eval in conn.evals_by_view[self.view.id()].values():
            if eval.status == "pending":
                conn.send({"op":           "interrupt",
                           "session":      eval.session,
                           "interrupt-id": eval.id})
                eval.update("interrupt", "Interrupting...")

    def is_enabled(self):
        return conn.ready()

class ClojureSublimedToggleTraceCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        point = view.sel()[0].begin()
        for eval in conn.evals_by_view[view.id()].values():
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
    body = f"""<body id='clojure-sublimed'>
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

def symbol_at_point(view, point):
    if point > 0 and view.match_selector(point - 1, 'source.symbol.clojure'):
        return view.extract_scope(point - 1)
    if view.match_selector(point, 'source.symbol.clojure'):
        return view.extract_scope(point)

class ClojureSublimedToggleSymbolCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        for sel in view.sel():
            eval = conn.find_eval(view, sel)
            if eval and eval.phantom_id:
                conn.erase_eval(eval)
            else:
                if region := symbol_at_point(view, sel.begin()) if sel.empty() else sel:
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

class ClojureSublimedToggleInfoCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        for sel in view.sel():
            eval = conn.find_eval(view, sel)
            if eval and eval.status == "exception":
                view.run_command("clojure_sublimed_toggle_trace", {})
            elif eval and eval.status == "success":
                if eval := conn.find_eval(view, sel):
                    print("eval.toggle_pprint()", eval, sel)
                    eval.toggle_pprint()
                    break
            else:
                view.run_command("clojure_sublimed_toggle_symbol", {})

    def is_enabled(self):
        return conn.ready()

class ClojureSublimedRequireNamespaceCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        for sel in view.sel():
            region = symbol_at_point(view, sel.begin()) if sel.empty() else sel
            # narrow down to the namespace part if present
            if region and (sym := view.substr(region).partition('/')[0]):
                region = sublime.Region(region.a, region.a + len(sym))
            if region:
                eval(view, region, code=f"(require '{sym})")

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


def get_shadow_repl_init_cmd(build):
    """Returns the command to initialise shadow-repl."""
    if build == "node-repl":
        return "(shadow.cljs.devtools.api/node-repl)"
    elif build == "browser-repl":
        return "(shadow.cljs.devtools.api/browser-repl)"
    else:
        return f"(shadow.cljs.devtools.api/repl {build})"


def handle_connect(msg):

    if conn.profile == Profile.SHADOW_CLJS:
        if 1 == msg.get("id") and "new-session" in msg:
            # Once we have the connnection to shadow's nrepl, we will 
            # tell shadow to watch the cljs build provided by the user.
            conn.session = msg["new-session"]
            conn.send({"op": "eval",
                       "session": conn.session,
                       "code": get_shadow_repl_init_cmd(conn.cljs_build),
                       "id": 2})
            return True

        elif 2 == msg.get("id") and msg.get("status") == ["done"]:
            conn.set_status(f"🌕 {conn.host or str()}:{conn.port}")
            return True

    if 1 == msg.get("id") and "new-session" in msg:
        conn.session = msg["new-session"]
        conn.send({"op": "load-file",
                   "session": conn.session,
                   "file": sublime.load_resource(f"Packages/{package}/src/middleware.clj"),
                   "id": 2})
        conn.set_status("🌓 Uploading middlewares")
        return True

    elif 2 == msg.get("id") and msg.get("status") == ["done"]:
        id = 3 if settings().get("eval_shared") else 4
        conn.send({"op":               "add-middleware",
                   "middleware":       [f"{ns}.middleware/clone-and-eval",
                                        f"{ns}.middleware/time-eval",
                                        f"{ns}.middleware/wrap-errors",
                                        f"{ns}.middleware/wrap-output"],
                   "extra-namespaces": [f"{ns}.middleware"],
                   "session":          conn.session,
                   "id":               id})
        conn.set_status("🌔 Adding middlewares")
        return True

    elif 3 == msg.get("id") and msg.get("status") == ["done"]:
        conn.send({"op":      "eval",
                   "code":    settings().get("eval_shared"), 
                   "session": conn.session,
                   "id":      4})

    elif 4 == msg.get("id") and msg.get("status") == ["done"]:
        conn.set_status(f"🌕 {conn.host or str()}:{conn.port}")
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

def connect(host, port, profile=Profile.CLOJURE, cljs_build=None):
    conn.host = host
    conn.port = port
    conn.profile = profile
    conn.cljs_build = cljs_build
    try:
        if _is_unix_domain_sock(conn.host):
            conn.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            conn.socket.connect(port)
        else:
            conn.socket = socket.create_connection((host, port))
        conn.reader = threading.Thread(daemon=True, target=read_loop)
        conn.reader.start()
    except Exception as e:
        _log.exception(e)
        conn.socket = None
        conn.set_status(None)
        if window := sublime.active_window():
            window.status_message(f"Failed to connect to {host}:{port}")


def _is_unix_domain_sock(host):
    return host is None


class ClojureSublimedHostPortInputHandler(sublime_plugin.TextInputHandler):
    def placeholder(self):
        return "host:port or /path/to/nrepl.sock"

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
        if conn.host:
            return conn.host + ":" + port

        return port

    def initial_selection(self):
        if conn.host:
            return [(len(conn.host + ":"), len(self.initial_text()))]

        return [(_inc(conn.port.rfind('/')), len(self.initial_text()))]

    def preview(self, text):
        if not self.validate(text):
            return "Expected <host>:<port> or <path>"

    def validate(self, text):
        text = text.strip()
        if re.fullmatch(r'[a-zA-Z0-9\.]+:\d{1,5}', text):
            host, port = text.split(':')
            port = int(port)

            return port in range(1, 65536)
        else:
            return bool(os.stat(text))


_inc = fn.partial(op.add, 1)


class ClojureSublimedShadowCljsBuildInputHandler(sublime_plugin.TextInputHandler):
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

    def next_input(self, args):
        return ClojureSublimedHostPortInputHandler()


class ClojureSublimedConnectShadowCljsCommand(sublime_plugin.ApplicationCommand):

    def run(self, clojure_sublimed_shadow_cljs_build, clojure_sublimed_host_port=''):
        host, port = clojure_sublimed_host_port.strip().split(':')
        port = int(port)
        connect(host, port, Profile.SHADOW_CLJS, clojure_sublimed_shadow_cljs_build)

    def input(self, args):
        if 'clojure_sublimed_shadow_cljs_build' not in args:
            return ClojureSublimedShadowCljsBuildInputHandler()

    def is_enabled(self):
        return conn.socket == None

class ClojureSublimedConnectCommand(sublime_plugin.ApplicationCommand):
    def run(self, clojure_sublimed_host_port):
        try:
            host, port = clojure_sublimed_host_port.strip().split(':', 1)
            port = int(port)
        except ValueError:
            host, port = None, clojure_sublimed_host_port
        connect(host, port)

    def input(self, args):
        return ClojureSublimedHostPortInputHandler()

    def is_enabled(self):
        return conn.socket == None

class ClojureSublimedDisconnectCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        conn.disconnect()

    def is_enabled(self):
        return conn.socket != None

class ClojureSublimedReconnectCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        conn.disconnect()
        connect(conn.host, conn.port, conn.profile, conn.cljs_build)

    def is_enabled(self):
        return conn.socket != None

def match_selectors(view, pos, selectors):
    return any(view.match_selector(pos, selector) for selector in selectors)

def reindent(view, edit, point, skip_blanks = True):
    line = view.line(point)
    text = view.substr(line)
    prefix = re.match(r"\s*", text).group(0)
    # Do not indent inside strings
    if view.match_selector(line.begin(), 'string') and not view.match_selector(line.begin(), 'punctuation.definition.string.begin'):
        pass
    # Do not reindent blank lines
    elif skip_blanks and len(prefix) == line.size():
        pass
    # Clear leading spaces at first line
    elif line.begin() == 0:
        if prefix:
            view.erase(edit, sublime.Region(0, len(prefix)))
    else:
        stack = []
        last_open = None
        pos = line.begin()
        while pos >= 0:
            pos = pos - 1
            ch = view.substr(pos)
            if match_selectors(view, pos, ['string', 'comment.line', 'constant.character']):
                pass
            # Short-circuit if outside of any parens
            elif not match_selectors(view, pos, ['meta.brackets', 'meta.braces', 'meta.parens']):
                break
            elif ch in [']', ')', '}']:
                stack.append(ch)
            elif ch not in ['(', '[', '{']:
                pass
            elif not stack:
                last_open = pos
                break
            elif {'[': ']', '(': ')', '{': '}'}[ch] == stack[-1]:
                stack.pop()
            else:
                pass

        replace = sublime.Region(line.begin(), line.begin() + len(prefix))
        # top-level form, everything before is balanced
        if last_open is None:
            view.replace(edit, replace, '')
            return line.begin()
        else:
            indent = last_open - view.line(last_open).begin()
            # list form that doesn’t start with paren. Indent to paren + 2
            if view.substr(last_open) == '(' and (last_open + 1 >= line.begin() or view.substr(last_open + 1) not in ['(', '[', '{']):
                view.replace(edit, replace, ' ' * (indent + 2))
                return line.begin() + indent + 2
            # everything else. Indent to paren + 1
            else:
                view.replace(edit, replace, ' ' * (indent + 1))
                return line.begin() + indent + 1
    return line.begin()


class ClojureSublimedReindentBufferOnSave(sublime_plugin.EventListener):
    def on_pre_save(self, view):
        if settings().get("format_on_save", False) and view.syntax().name == 'Clojure (Sublimed)':
            view.window().run_command('clojure_sublimed_reindent_buffer')

class ClojureSublimedReindentBufferCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        lines = view.lines(sublime.Region(0, view.size()))
        change_id = view.change_id()
        for line in lines:
            reindent(view, edit, view.transform_region_from(line, change_id).begin())

class ClojureSublimedReindentLinesCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        change_id_sel = view.change_id()
        for sel in view.sel():
            sel = view.transform_region_from(sel, change_id_sel)
            change_id_line = view.change_id()
            for line in view.lines(sel):
                line = view.transform_region_from(line, change_id_line)
                reindent(view, edit, line.begin())

class ClojureSublimedInsertNewlineCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        change_id_sel = view.change_id()
        ends = []
        for sel in view.sel():
            # sel = view.transform_region_from(sel, change_id_sel)
            view.replace(edit, sel, "\n")
            ends.append(reindent(view, edit, sel.begin() + 1, skip_blanks = False))

        view.sel().clear()
        for end in ends:
            view.sel().add(sublime.Region(end, end))

class ClojureSublimedEventListener(sublime_plugin.EventListener):
    def on_activated_async(self, view):
        conn.refresh_status()
        progress_thread.wake()

    def on_close(self, view):
        conn.erase_evals(lambda eval: True, view)

class ClojureSublimedViewEventListener(sublime_plugin.TextChangeListener):
    def on_text_changed_async(self, changes):
        view = self.buffer.primary_view()
        changed = [sublime.Region(x.a.pt, x.b.pt) for x in changes]
        def should_erase(eval):
            return not (reg := eval.region()) or any(reg.intersects(r) for r in changed) and view.substr(reg) != eval.code
        conn.erase_evals(should_erase, view)

def on_settings_change():
    Eval.colors.clear()
    progress_thread.update_phases(settings().get("progress_phases"), settings().get("progress_interval_ms"))
    conn.eval_in_session = settings().get("eval_in_session", False)

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
