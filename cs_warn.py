import sublime, sublime_plugin
from . import cs_common

status_key = 'clojure-sublimed-warn-status'

def add_warning(window):
    state = cs_common.get_state(window)
    state.warnings += 1
    suffix = 's' if state.warnings > 0 else ''
    cs_common.set_status(window, status_key, f'⚠️ {state.warnings} warning{suffix}')

def reset_warnings(window):
    state = cs_common.get_state(window)
    state.warnings = 0
    cs_common.set_status(window, status_key, None)