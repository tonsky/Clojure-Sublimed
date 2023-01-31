import collections, html, os, re, socket, sublime, sublime_plugin, threading
from typing import Dict
from . import cs_bencode, cs_common, cs_eval, cs_parser, cs_progress

class Connection:
    host: str
    port: str
    status: str
    last_view: sublime.View
    session: str
    profile: cs_common.Profile
    cljs_build: str

    def __init__(self):
        self.host = 'localhost'
        self.port = None
        self.reset()
        self.last_view = window.active_view() if (window := sublime.active_window()) else None
        self.session = None
        self.profile = None
        self.cljs_build = None

    def set_status(self, status):
        self.status = status
        self.refresh_status()

    def refresh_status(self):
        if window := sublime.active_window():
            if view := window.active_view():
                if self.status:
                    view.set_status(cs_common.ns, self.status)
                else:
                    view.erase_status(cs_common.ns)
                self.last_view = view

    def send(self, msg):
        cs_common.debug("SND {}", msg)
        self.socket.sendall(cs_bencode.encode(msg).encode())

    def reset(self):
        self.socket = None
        self.reader = None
        self.session = None
        self.set_status(None)

    def disconnect(self):
        if self.socket:
            self.socket.close()
            self.reset()
            cs_eval.erase_evals()

    def ready(self):
        return bool(self.socket and self.session)

def handle_new_session(msg):
    if "new-session" in msg and "id" in msg and (eval := cs_eval.by_id(msg["id"])):
        eval.session = msg["new-session"]
        return True

def handle_value(msg):
    if "value" in msg and "id" in msg and (eval := cs_eval.by_id(msg["id"])):
        eval.update("success", msg.get("value"), time_taken = msg.get(f'{cs_common.ns}.middleware/time-taken'))
        return True

def set_selection(view, region):
    sel = view.sel()
    sel.clear()
    sel.add(region)
    view.show(region.a, show_surrounds = True, keep_to_left = True, animate = True)

def handle_exception(msg):
    if "id" in msg and (eval := cs_eval.by_id(msg["id"])):
        present = lambda key: (cs_common.ns + ".middleware/" + key) in msg
        get = lambda key: msg.get(cs_common.ns + ".middleware/" + key)
        if get("root-ex-class") and get("root-ex-msg"):
            text = get("root-ex-class") + ": " + get("root-ex-msg")
            region = None
            if get("root-ex-data"):
                text += " " + get("root-ex-data")
            if present("line") and present("column") and eval.view:
                line = get("line") - 1
                column = get("column")
                point = eval.view.text_point_utf16(line, column, clamp_column = True)
                region = sublime.Region(eval.view.line(point).begin(), eval.view.line(point).end())
                set_selection(eval.view, sublime.Region(point, point))
            elif present("line") and present("column") and get("source"):
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
            return True

def handle_lookup(msg):
    if "info" in msg and "id" in msg and (eval := cs_eval.by_id(msg["id"])):
        eval.update("lookup", None)
        view = eval.view
        body = format_lookup(view, msg["info"])
        point = view.line(eval.region().end()).begin()
        eval.phantom_id = view.add_phantom(eval.value_key(), sublime.Region(point, point), body, sublime.LAYOUT_BLOCK)
        return True

def get_shadow_repl_init_cmd(build):
    """Returns the command to initialise shadow-repl."""
    if build == "node-repl":
        return "(shadow.cljs.devtools.api/node-repl)"
    elif build == "browser-repl":
        return "(shadow.cljs.devtools.api/browser-repl)"
    else:
        return f"(shadow.cljs.devtools.api/repl {build})"

def _status_connected(conn):
    return "🌕 " + (conn.host + ":" if conn.host else "") + str(conn.port)

def handle_connect(msg):
    if cs_common.conn.profile == cs_common.Profile.SHADOW_CLJS:
        if 1 == msg.get("id") and "new-session" in msg:
            # Once we have the connnection to shadow's nrepl, we will 
            # tell shadow to watch the cljs build provided by the user.
            cs_common.conn.session = msg["new-session"]
            cs_common.conn.send({"op": "eval",
                       "session": cs_common.conn.session,
                       "code": get_shadow_repl_init_cmd(cs_common.conn.cljs_build),
                       "id": 2})
            return True

        elif 2 == msg.get("id") and msg.get("status") == ["done"]:
            cs_common.conn.set_status(_status_connected(cs_common.conn))
            return True

    if 1 == msg.get("id") and "new-session" in msg:
        global package
        cs_common.conn.session = msg["new-session"]
        cs_common.conn.send({"op": "load-file",
                             "session": cs_common.conn.session,
                             "file": sublime.load_resource(f"Packages/{package}/cs_middleware.clj"),
                             "id": 2})
        cs_common.conn.set_status("🌓 Uploading middlewares")
        return True

    elif 2 == msg.get("id") and msg.get("status") == ["done"]:
        id = 3 if cs_common.setting("eval_shared") else 4
        cs_common.conn.send({"op":               "add-middleware",
                   "middleware":       [f"{cs_common.ns}.middleware/clone-and-eval",
                                        f"{cs_common.ns}.middleware/time-eval",
                                        f"{cs_common.ns}.middleware/wrap-errors",
                                        f"{cs_common.ns}.middleware/wrap-output"],
                   "extra-namespaces": [f"{cs_common.ns}.middleware"],
                   "session":          cs_common.conn.session,
                   "id":               id})
        cs_common.conn.set_status("🌔 Adding middlewares")
        return True

    elif 3 == msg.get("id") and msg.get("status") == ["done"]:
        cs_common.conn.send({"op":      "eval",
                   "code":    cs_common.setting("eval_shared"), 
                   "session": cs_common.conn.session,
                   "id":      4})

    elif 4 == msg.get("id") and msg.get("status") == ["done"]:
        cs_common.conn.set_status(_status_connected(cs_common.conn))
        return True

def handle_done(msg):
    if "id" in msg and (eval := cs_eval.by_id(msg["id"])) and "status" in msg and "done" in msg["status"]:
        if eval.status not in {"success", "exception"}:
            eval.erase()

def handle_msg(msg):
    cs_common.debug("RCV {}", msg)

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
        cs_common.conn.send({"op": "clone", "id": 1})
        cs_common.conn.set_status(f"🌒 Cloning session")
        for msg in cs_bencode.decode_file(cs_common.SocketIO(cs_common.conn.socket)):
            handle_msg(msg)
    except OSError:
        pass
    cs_common.conn.disconnect()

def plugin_loaded():
    global package
    package_path = os.path.dirname(os.path.abspath(__file__))
    if os.path.isfile(package_path):
        # Package is a .sublime-package so get its filename
        package, _ = os.path.splitext(os.path.basename(package_path))
    elif os.path.isdir(package_path):
        # Package is a directory, so get its basename
        package = os.path.basename(package_path)
    cs_common.conn = Connection()

def plugin_unloaded():
    cs_common.conn.disconnect()
