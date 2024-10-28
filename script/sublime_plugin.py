class EventListener:
    pass

class TextCommand:
    def __init__(self, view):
        self.view: sublime.View = view
