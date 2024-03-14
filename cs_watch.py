import collections, re, sublime, sublime_plugin
from . import cs_common, cs_conn, cs_parser, cs_printer

watches = {} # Dict[int, Watch]
watches_by_view = collections.defaultdict(dict) # Dict[int, Dict[int, Watch]]

class Watch:
    last_id: int = 0

    def next_id():
        Watch.last_id += 1
        return Watch.last_id

    def region_key(self):
        return f"{cs_common.ns}.watch-{self.id}"

    def value(self):
        return self.values[-1] if len(self.values) > 0 else None

    def update_region(self):
        regions = self.view.get_regions(self.region_key())
        if regions and len(regions) >= 1:
            self.region = regions[0]

    def __init__(self, view, region):
        self.id         = Watch.next_id()
        self.view       = view
        self.region     = region
        self.values     = collections.deque(maxlen = 10)
        self.phantom_id = None
        watches[self.id] = self
        watches_by_view[view.id()][self.id] = self
        self.update(recursive = False)

    def __lt__(self, other):
        return self.region.begin() < other.region.begin()

    def update(self, value = None, recursive = True):
        view = self.view
        if value is not None:
            self.values.append(value)
        scope, color = cs_common.scope_color(self.view, 'watch')
        view.erase_regions(self.region_key())

        line = view.line(self.region)
        same_line_watches = list(w for w in watches_by_view[view.id()].values() if view.line(w.region) == line)
        same_line_watches.sort()
        if same_line_watches[0] == self:
            display = " · ".join(cs_common.escape(w.value()) for w in same_line_watches if w.value())
            self.view.add_regions(
                key              = self.region_key(),
                regions          = [self.region],
                scope            = scope, 
                flags            = sublime.DRAW_NO_FILL + sublime.NO_UNDO,
                annotations      = [display] if display else [],
                annotation_color = color if display else ''
            )
        else:
            self.view.add_regions(
                key     = self.region_key(),
                regions = [self.region],
                scope   = scope, 
                flags   = sublime.DRAW_NO_FILL + sublime.NO_UNDO
            )
            if recursive:
                same_line_watches[0].update()

    def erase(self):
        self.view.erase_regions(self.region_key())
        if self.phantom_id:
            self.view.erase_phantom_by_id(self.phantom_id)
        del watches[self.id]
        del watches_by_view[self.view.id()][self.id]

    def toggle(self):
        if self.value() is None:
            return

        if self.phantom_id:
            self.view.erase_phantom_by_id(self.phantom_id)
            self.phantom_id = None
            return

        limit = cs_common.wrap_width(self.view)

        string = ""
        for index, value in enumerate(reversed(self.values)):
            node   = cs_parser.parse(value)
            prefix = f" i-{index}" if index > 0 else "last"
            string += f"{prefix}: {cs_printer.format(value, node, limit = limit)}\n"

        styles  = """
            .light body { background-color: hsl(285, 100%, 90%); }
            .dark body  { background-color: hsl(285, 100%, 10%); }
        """ 
        if phantom_styles := cs_common.phantom_styles(self.view, "phantom_success"):
            styles += f".light body, .dark body {{ { phantom_styles }; border: 4px solid #CC33CC; }}"

        body = f"""<body id='clojure-sublimed'>
            { cs_common.basic_styles(self.view) }
            { styles }
        </style>"""
        
        for line in string.splitlines():
            line = cs_printer.wrap_string(line, limit = limit)
            line = cs_common.escape(line)
            body += "<p>" + line + "</p>"
        body += "</body>"
        point = self.view.line(self.region.end()).begin()
        self.phantom_id = self.view.add_phantom(
            key = self.region_key(),
            region = sublime.Region(point, point),
            content = body,
            layout = sublime.LAYOUT_BLOCK
        )

def on_watch(id, value):
    if w := watches.get(id):
        w.update(value)

def erase_watches(predicate = lambda x: True, view = None):
    if view:
        to_erase = list(w for w in watches_by_view[view.id()].values() if predicate(w))
    else:
        to_erase = list(w for w in watches.values() if predicate(w))
    for w in to_erase:
        w.erase()

def by_region(view, region):
    for w in watches_by_view[view.id()].values():
        if cs_common.regions_touch(w.region, region):
            return w

def transform(view):
    def transform_impl(code, **kwargs):
        region  = kwargs['eval_region']
        watches = list(w for w in watches_by_view[view.id()].values() if region.contains(w.region))
        watches.sort()
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
        if ws := list(w for w in watches_by_view[view.id()].values() if w.region == sel):
            ws[0].erase()
        else:
            erase_watches(lambda w: w.region.intersects(sel), view)
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
                    and type(state.conn).__name__ == 'ConnectionSocketRepl' \
                    and len(view.sel()) == 1 \
                    and not sel.empty())

class EventListener(sublime_plugin.EventListener):
    def on_pre_close(self, view):
        erase_watches(view = view)

class TextChangeListener(sublime_plugin.TextChangeListener):
    def on_text_changed_async(self, changes):
        view    = self.buffer.primary_view()
        changed = [sublime.Region(x.a.pt, x.b.pt) for x in changes]
        
        def should_erase(w):
            return any(w.region.intersects(r) for r in changed)
        erase_watches(should_erase, view)
        
        lines = list(view.line(r) for r in changed)
        def should_update(w):
            return any(r.contains(w.region.begin()) for r in lines)
        need_update = list(w for w in watches_by_view[view.id()].values() if should_update(w))

        for w in watches_by_view[view.id()].values():
            w.update_region()

        for w in need_update:
            w.update(recursive = False)

def plugin_unloaded():
    erase_watches()
