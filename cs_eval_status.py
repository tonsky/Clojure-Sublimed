import sublime, sublime_plugin
from . import cs_common, cs_conn, cs_eval, cs_parser, cs_progress

status_key = 'clojure-sublimed-eval-status'
status_eval = None

class StatusEval:
    """
    Displays 'eval_code' command results in status bar
    """
    def __init__(self, code):
        global status_eval
        if status_eval:
            status_eval.erase()

        id           = cs_eval.Eval.next_id
        self.id      = id
        self.code    = code
        self.session = None
        
        cs_eval.Eval.next_id += 1
        status_eval  = self

        self.update('pending', cs_progress.phase())
        cs_progress.wake()

    def update(self, status, value, time_taken = None):
        self.status = status
        self.value = value
        if status in {"pending", "interrupt"}:
            cs_common.set_status(status_key, "⏳ " + self.code)
        elif "success" == status:
            if time := cs_common.format_time_taken(time_taken):
                value = time + ' ' + value
            cs_common.set_status(status_key, "✅ " + value)
        elif "exception" == status:
            if time := cs_common.format_time_taken(time_taken):
                value = time + ' ' + value
            cs_common.set_status(status_key, "❌ " + value)

    def erase(self):
        global status_eval
        cs_common.set_status(status_key, None)
        status_eval = None
        if self.status == "pending" and self.session:
            cs_conn.conn.interrupt(self.id)

class ClojureSublimedEvalCodeCommand(sublime_plugin.ApplicationCommand):
    def run(self, code, ns = None):        
        eval = StatusEval(code)
        if (not ns) and (view := eval.active_view()):
            ns = cs_parser.namespace(view, view.size())
        cs_conn.conn.eval(eval.id, code, ns or 'user')

    def is_enabled(self):
        if not cs_conn.ready():
            return False
        if status_eval and status_eval.status in {'pending', 'interrupt'}:
            return False
        return True
