import collections, html, os, re, sublime, sublime_plugin
from typing import Any, Dict, Tuple
from . import cs_common, cs_conn, cs_eval_status, cs_parser, cs_progress

evals = {} # Dict[int, Eval]
evals_by_view = collections.defaultdict(dict) # Dict[int, Dict[int, Eval]]

class Eval:
    """
    A region of evaluation, including symbol lookups.
    Has short .value region and longer .trace phantom and can toggle between them
    """
    # class
    next_id: int = 10
    colors:  Dict[str, Tuple[str, str]] = {}

    # instance
    id:         int
    view:       sublime.View
    status:     str # "pending" | "interrupt" | "success" | "exception" | "lookup"
    code:       str
    session:    str
    trace:      str
    phantom_id: int
    
    def __init__(self, view, region):
        extended_region = view.line(region)
        erase_evals(lambda eval: eval.region() and eval.region().intersects(extended_region), view)
        
        id = Eval.next_id
        self.id = id
        self.view = view
        self.code = view.substr(region)
        self.session = None
        self.trace = None
        self.phantom_id = None
        self.value = None
        
        Eval.next_id += 1
        evals[id] = self
        evals_by_view[view.id()][id] = self

        self.update("pending", cs_progress.phase(), region)
        cs_progress.wake()        

    def value_key(self):
        return f"{cs_common.ns}.eval-{self.id}"

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

    def escape(self, value):
        return html.escape(value).replace("\t", "&nbsp;&nbsp;").replace(" ", "&nbsp;")

    def update(self, status, value, region = None, time_taken = None):
        self.status = status
        self.value = value
        region = region or self.region()
        if region:
            scope, color = self.scope_color()
            if value:
                if (self.status in {"success", "exception"}) and (time := cs_common.format_time_taken(time_taken)):
                    value = time + " " + value
                self.view.add_regions(self.value_key(), [region], scope, '', sublime.DRAW_NO_FILL + sublime.NO_UNDO, [self.escape(value)], color)
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
                    { cs_common.basic_styles(self.view) }
                    { styles }
                </style>"""
                for line in self.escape(text).splitlines():
                    line = re.sub(r"(?<!\\)\\n", "<br>", line)
                    line = re.sub(r"(?<!\\)\\t", "&nbsp;&nbsp;", line)
                    body += "<p>" + line + "</p>"
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

        del evals[self.id]
        del evals_by_view[self.view.id()][self.id]
        if self.status == "pending" and self.session:
            cs_common.conn.send({"op": "interrupt", "interrupt-id": self.id, "session": self.session})

def by_id(id):
    """
    Find an eval by id. Might return status_eval
    """
    if (eval := cs_eval_status.status_eval) and id == eval.id:
        return eval
    return evals.get(id, None)

def by_region(view, region):
    """
    Find an eval touching region
    """
    for eval in evals_by_view[view.id()].values():
        if cs_common.regions_touch(eval.region(), region):
            return eval

def by_status(view, status):
    """
    Find evals by status
    """
    return (eval for eval in evals_by_view[view.id()].values() if eval.status == status)

def erase_evals(predicate = lambda x: True, view = None):
    """
    Kill evals based on predicate
    """
    if view:
        es = list(evals_by_view[view.id()].items())
    else:
        es = list(evals.items())
        if eval := cs_eval_status.status_eval:
            es += [(eval.id, eval)]
    for id, eval in es:
        if predicate(eval):
            eval.erase()

def on_success(id, value):
    """
    Callback to be called after conn.eval or conn.load_file
    """
    if (eval := by_id(id)):
        eval.update('success', value)

def on_exception(id, value, line = None, column = None, trace = None):
    """
    Callback to be called after conn.eval, conn.load_file or conn.interrupt
    """
    if (eval := by_id(id)):
        eval.trace = trace
        eval.update('exception', value)

def format_lookup(view, info):
    settings = view.settings()
    top = settings.get('line_padding_top', 0)
    bottom = settings.get('line_padding_bottom', 0)
    body = f"""<body id='clojure-sublimed'>
        {cs_common.basic_styles(view)}
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

        if forms and isinstance(forms, str):
            body += f'<p class="arglists">{html.escape(forms.strip("[]"))}</p>'
        elif forms:
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

def on_lookup(id, value):
    """
    Callback to be called after conn.lookup
    """
    if (eval := by_id(id)):
        eval.update('lookup', None)
        view = eval.view
        body = format_lookup(view, value)
        point = view.line(eval.region().end()).begin()
        eval.phantom_id = view.add_phantom(eval.value_key(), sublime.Region(point, point), body, sublime.LAYOUT_BLOCK)

def on_done(id):
    if (eval := by_id(id)) and eval.status not in {"success", "exception"}:
        eval.erase()

def eval(view, region, code = None):
    eval = Eval(view, region)
    if not code:
        code = view.substr(region)
    ns   = cs_parser.namespace(view, region.begin()) or 'user'
    (line, column) = view.rowcol_utf16(region.begin())
    line = line + 1
    file = view.file_name()
    cs_conn.conn.eval(eval.id, code, ns, line, column, file)

class ClojureSublimedEval(sublime_plugin.TextCommand):
    """
    Eval selected code or topmost form is selection is collapsed
    """
    def run(self, edit):
        covered = []
        for sel in self.view.sel():
            if all([not sel.intersects(r) for r in covered]):
                if sel.empty():
                    region = cs_parser.topmost_form(self.view, sel.begin())
                    if region:
                        covered.append(region)
                        eval(self.view, region)
                else:
                    covered.append(sel)
                    eval(self.view, sel)

    def is_enabled(self):
        return cs_conn.ready()

class ClojureSublimedEvalBufferCommand(sublime_plugin.TextCommand):
    """
    Eval whole buffer
    """
    def run(self, edit):
        view = self.view
        region = sublime.Region(0, view.size())
        eval = Eval(view, region)
        file = view.substr(region)
        path = view.file_name()
        cs_conn.conn.load_file(eval.id, file, path)
        
    def is_enabled(self):
        return cs_conn.ready()

class ClojureSublimedCopyCommand(sublime_plugin.TextCommand):
    """
    Copy .value of eval under cursor to clipboard
    """
    def eval(self):
        view = self.view
        return by_region(view, view.sel()[0])

    def run(self, edir):
        if cs_conn.ready() and len(self.view.sel()) == 1 and self.view.sel()[0].empty() and (eval := self.eval()) and eval.value:
            sublime.set_clipboard(eval.value)
        else:
            self.view.run_command("copy", {})

class ClojureSublimedToggleTraceCommand(sublime_plugin.TextCommand):
    """
    Show/hide extended stacktrace
    """
    def run(self, edit):
        view = self.view
        sel = view.sel()[0]
        if eval := by_region(view, sel):
            eval.toggle_trace()
        
    def is_enabled(self):
        return cs_conn.ready() and len(self.view.sel()) == 1

class ClojureSublimedToggleSymbolCommand(sublime_plugin.TextCommand):
    """
    Show/hide symbol info
    """
    def run(self, edit):
        view = self.view
        sel = view.sel()[0]
        eval = by_region(view, sel)
        if eval and eval.phantom_id:
            eval.erase()
        else:
            if region := cs_parser.symbol_at_point(view, sel.begin()) if sel.empty() else sel:
                symbol = view.substr(region)
                ns = cs_parser.namespace(view, region.begin()) or 'user'
                eval = Eval(view, region)
                cs_conn.conn.lookup(eval.id, symbol, ns)

    def is_enabled(self):
        return cs_conn.ready() and len(self.view.sel()) == 1

class ClojureSublimedToggleInfoCommand(sublime_plugin.TextCommand):
    """
    Universal show/hide, depends on where it was called. Can expand stacktrace,
    successfull eval or look up symbol
    """
    def run(self, edit):
        view = self.view
        sel = view.sel()[0]
        if eval := by_region(view, sel):
            if eval.status == "exception":
                eval.toggle_trace()
            elif eval.status == "success":
                eval.toggle_pprint()
            elif eval.status == 'lookup':
                eval.erase()
        else:
            view.run_command("clojure_sublimed_toggle_symbol", {})

    def is_enabled(self):
        return cs_conn.ready() and len(self.view.sel()) == 1

class ClojureSublimedClearEvalsCommand(sublime_plugin.TextCommand):
    """
    Clear all completed evals in current view
    """
    def run(self, edit):
        erase_evals(lambda eval: eval.status not in {"pending", "interrupt"}, self.view)
        if (eval := cs_eval_status.status_eval) and eval.status not in {"pending", "interrupt"}:
            eval.erase()

class ClojureSublimedInterruptEvalCommand(sublime_plugin.TextCommand):
    """
    Interrupt first pending eval in current view
    """
    def run(self, edit):
        es = list(by_status(self.view, 'pending'))
        if (eval := cs_eval_status.status_eval) and eval.status not in {"pending", "interrupt"}:
            es += [eval]
        if len(es) > 0:
            if eval := min(es, key = lambda eval: eval.id):
                cs_conn.conn.interrupt(eval.id)
                eval.update('interrupt', "Interrupting...")

    def is_enabled(self):
        return cs_conn.ready()

class ClojureSublimedRequireNamespaceCommand(sublime_plugin.TextCommand):
    """
    On namespace-qualified symbol, require its namespace
    """
    def run(self, edit):
        view = self.view
        for sel in view.sel():
            region = cs_parser.symbol_at_point(view, sel.begin()) if sel.empty() else sel
            # narrow down to the namespace part if present
            if region and (sym := view.substr(region).partition('/')[0]):
                region = sublime.Region(region.a, region.a + len(sym))
            if region:
                eval(view, region, code=f"(require '{sym})")

    def is_enabled(self):
        return cs_conn.ready()

class EventListener(sublime_plugin.EventListener):
    def on_close(self, view):
        erase_evals(view = view)

class TextChangeListener(sublime_plugin.TextChangeListener):
    def on_text_changed_async(self, changes):
        view = self.buffer.primary_view()
        changed = [sublime.Region(x.a.pt, x.b.pt) for x in changes]
        def should_erase(eval):
            return not (reg := eval.region()) or any(reg.intersects(r) for r in changed) and view.substr(reg) != eval.code
        erase_evals(should_erase, view)

def on_settings_change(settings):
    Eval.colors.clear()

def plugin_loaded():
    cs_common.on_settings_change(__name__, on_settings_change)

def plugin_unloaded():
    erase_evals()
    cs_common.clear_settings_change(__name__)
