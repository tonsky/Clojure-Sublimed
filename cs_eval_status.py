import sublime, sublime_plugin
from . import cs_common, cs_conn, cs_eval, cs_parser, cs_progress

status_key = 'clojure-sublimed-eval-status'
status_eval = None

class StatusEval:
    """
    Displays 'eval_code' command results in status bar
    """
    def __init__(self, code, id = None, batch_id = None):
        global status_eval
        if status_eval:
            status_eval.erase()

        self.id       = id or cs_eval.Eval.next_id()
        self.batch_id = batch_id or self.id
        self.code     = code
        self.session  = None
        
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

    def erase(self, interrupt = True):
        global status_eval
        cs_common.set_status(status_key, None)
        status_eval = None
        if interrupt and self.status == "pending" and self.session:
            cs_conn.conn.interrupt(self.id)

class ClojureSublimedEvalCodeCommand(sublime_plugin.ApplicationCommand):
    def run(self, code, ns = None):
        if (not ns) and (view := cs_common.active_view()):
            ns = cs_parser.namespace(view, view.size())
        cs_conn.conn.eval_status(code, ns or 'user')

    def is_enabled(self):
        if not cs_conn.ready():
            return False
        if status_eval and status_eval.status in {'pending', 'interrupt'}:
            return False
        return True
