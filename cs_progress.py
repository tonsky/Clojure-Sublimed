import sublime, sublime_plugin, threading, time
from . import cs_common, cs_eval

class ProgressThread:
    """
    Thread that updates all pending evals spinners.
    Singleton, always running, but if no pending evals are present, sleeps
    """
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
                for eval in cs_eval.by_status(view, 'pending'):
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

thread = ProgressThread()

def phase():
    return thread.phase()

def wake():
    thread.wake()

class EventListener(sublime_plugin.EventListener):
    def on_activated_async(self, view):
        """
        On active view change
        """
        thread.wake()

def on_settings_change(settings):
    thread.update_phases(settings["progress_phases"], settings["progress_interval_ms"])

def plugin_loaded():
    cs_common.on_settings_change(__name__, on_settings_change)

def plugin_unloaded():
    thread.stop()
    cs_common.clear_settings_change(__name__)
