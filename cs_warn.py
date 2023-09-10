import sublime, sublime_plugin
from . import cs_common

status_key = 'clojure-sublimed-warn-status'
warnings = 0

def add_warning():
    global warnings
    warnings += 1
    suffix = 's' if warnings > 0 else ''
    cs_common.set_status(status_key, f'⚠️ {warnings} warning{suffix}')

def reset_warnings():
    global warnings
    warnings = 0
    cs_common.set_status(status_key, None)