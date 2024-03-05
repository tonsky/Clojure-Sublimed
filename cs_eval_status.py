import sublime, sublime_plugin
from . import cs_common, cs_conn, cs_eval, cs_parser, cs_progress

status_key = 'clojure-sublimed-eval-status'

class StatusEval:
    """
    Displays 'eval_code' command results in status bar
    """
    def __init__(self, code, id = None, batch_id = None):
        self.window = sublime.active_window()
        state = cs_common.get_state(self.window)
        
        if state.status_eval:
            state.status_eval.erase()

        self.id        = id or cs_eval.Eval.next_id()
        self.batch_id  = batch_id or self.id
        self.code      = code
        self.session   = None
        self.ex_source = None
        self.ex_line   = None
        self.ex_column = None
        self.trace     = None
        
        state.status_eval = self

        self.update('pending', cs_progress.phase())
        cs_progress.wake()

    def update(self, status, value, time_taken = None):
        self.status = status
        self.value = value
        if status in {"pending", "interrupt"}:
            cs_common.set_status(self.window, status_key, "⏳ " + self.code)
        elif "success" == status:
            if time := cs_common.format_time_taken(time_taken):
                value = time + ' ' + value
            cs_common.set_status(self.window, status_key, "✅ " + value)
        elif "failure" == status:
            if time := cs_common.format_time_taken(time_taken):
                value = time + ' ' + value
            cs_common.set_status(self.window, status_key, "❌ " + value)
        elif "exception" == status:
            if time := cs_common.format_time_taken(time_taken):
                value = time + ' ' + value
            msg = "❌ " + value
            if self.ex_source:
                msg += ", at " + self.ex_source
            if self.ex_line:
                msg += ":" + str(self.ex_line)
            if self.ex_column:
                msg += ":" + str(self.ex_column)
            cs_common.set_status(self.window, status_key, msg)

    def erase(self, interrupt = True):
        state = cs_common.get_state(self.window)
        cs_common.set_status(self.window, status_key, None)
        state.status_eval = None
        if interrupt and self.status == "pending" and self.session:
            state.conn.interrupt(self.id)

class ClojureSublimedEvalCodeCommand(sublime_plugin.WindowCommand):
    def run(self, code, ns = None):
        if (not ns) and (view := cs_common.active_view()):
            ns = cs_parser.namespace(view, view.size())
        state = cs_common.get_state(self.window)
        state.conn.eval_status(code, ns or 'user')

    def is_enabled(self):
        if not cs_conn.ready(self.window):
            return False
        state = cs_common.get_state(self.window)
        if state.status_eval and state.status_eval.status in {'pending', 'interrupt'}:
            return False
        return True
