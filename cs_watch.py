import re, sublime, sublime_plugin
from . import cs_common, cs_conn, cs_conn_socket_repl, cs_parser, cs_printer

class Watch:
    last_id: int = 0

    def next_id():
        Watch.last_id += 1
        return Watch.last_id

    def value_key(self):
        return f"{cs_common.ns}.watch-{self.id}"

    def update_region(self):
        regions = self.view.get_regions(self.value_key())
        if regions and len(regions) >= 1:
            self.region = regions[0]

    def __init__(self, view, region):
        self.id         = Watch.next_id()
        self.view       = view
        self.region     = region
        self.value      = None
        self.phantom_id = None
        state = cs_common.get_state(view.window())
        state.watches[self.id] = self
        self.update(None)

    def update(self, value):
        self.value = value
        scope, color = cs_common.scope_color(self.view, 'watch')
        self.view.erase_regions(self.value_key())
        self.view.add_regions(
            key              = self.value_key(),
            regions          = [self.region],
            scope            = scope, 
            flags            = sublime.DRAW_NO_FILL + sublime.NO_UNDO,
            annotations      = [cs_common.escape(value)] if value is not None else [],
            annotation_color = color if value is not None else ''
        )

    def erase(self):
        # print(f"Erasing {self.id}")
        state = cs_common.get_state(self.view.window())
        self.view.erase_regions(self.value_key())
        del state.watches[self.id]

    def toggle(self):
        if self.value is None:
            return

        node    = cs_parser.parse(self.value)
        string  = cs_printer.format(self.value, node, limit = cs_common.wrap_width(self.view))
        styles  = """
            .light body { background-color: hsl(285, 100%, 90%); }
            .dark body  { background-color: hsl(285, 100%, 10%); }
        """ 
        if phantom_styles := cs_common.phantom_styles(self.view, "phantom_success"):
            styles += f".light body, .dark body {{ { phantom_styles }; border: 4px solid #CC33CC; }}"

        if self.phantom_id:
            self.view.erase_phantom_by_id(self.phantom_id)
            self.phantom_id = None
        else:
            body = f"""<body id='clojure-sublimed'>
                { cs_common.basic_styles(self.view) }
                { styles }
            </style>"""
            limit = cs_common.wrap_width(self.view)
            for line in string.splitlines():
                line = cs_printer.wrap_string(line, limit = limit)
                line = cs_common.escape(line)
                body += "<p>" + line + "</p>"
            body += "</body>"
            point = self.view.line(self.region.end()).begin()
            self.phantom_id = self.view.add_phantom(
                key = self.value_key(),
                region = sublime.Region(point, point),
                content = body,
                layout = sublime.LAYOUT_BLOCK
            )

def on_watch(id, value):
    state = cs_common.get_state()
    if watch := state.watches.get(id):
        watch.update(value)

def erase_watches(predicate = lambda x: True, view = None):
    state = cs_common.get_state(view.window() if view else None)
    to_erase = list(watch for watch in state.watches.values() if predicate(watch) and (watch.view == view if view is not None else True))
    for watch in to_erase:
        watch.erase()

def by_region(view, region):
    state = cs_common.get_state(view.window())
    for watch in state.watches.values():
        if cs_common.regions_touch(watch.region, region):
            return watch

def transform(view):
    def transform_impl(code, **kwargs):
        state   = cs_common.get_state(view.window())
        region  = kwargs['eval_region']
        watches = list(w for w in state.watches.values() if w.view == view and region.contains(w.region))
        watches.sort(key = lambda w: w.region.begin())
        pos = region.begin()
        res = ''
        for w in watches:
            w_region = w.region
            res += view.substr(sublime.Region(pos, w_region.begin()))
            res += "(clojure-sublimed.socket-repl/watch " + str(w.id) + " "
            res += view.substr(w_region)
            res += ")"
            pos = w_region.end()
        res += view.substr(sublime.Region(pos, region.end()))
        return res
    return transform_impl

class ClojureSublimedAddWatchCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view   = self.view
        window = view.window()
        sel    = view.sel()[0]
        line   = view.line(sel)
        erase_watches(lambda w: w.region.intersects(line), view)
        top    = cs_parser.topmost_form(view, sel.begin())
        state  = cs_common.get_state(window)
        watch  = Watch(view, sel)
        state.conn.eval(view, [top])

    def is_enabled(self):
        view = self.view
        window = view.window()
        sel = view.sel()[0]
        state = cs_common.get_state(window)
        return bool(state.conn \
                    and state.conn.ready() \
                    and isinstance(state.conn, cs_conn_socket_repl.ConnectionSocketRepl) \
                    and len(view.sel()) == 1 \
                    and not sel.empty())

class EventListener(sublime_plugin.EventListener):
    def on_pre_close(self, view):
        erase_watches(view = view)

class TextChangeListener(sublime_plugin.TextChangeListener):
    def on_text_changed_async(self, changes):
        view    = self.buffer.primary_view()
        changed = [sublime.Region(x.a.pt, x.b.pt) for x in changes]
        def should_erase(watch):
            return any(watch.region.intersects(r) for r in changed)
        erase_watches(should_erase, view)
        state = cs_common.get_state(view.window())
        for watch in state.watches.values():
            watch.update_region()
