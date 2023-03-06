#! /usr/bin/env python3
import os, subprocess

if __name__ == '__main__':
  os.chdir(os.path.dirname(__file__) + "/..")
  subprocess.check_call(['clojure',
    '-J--add-opens=java.base/java.io=ALL-UNNAMED',
    '-X', 'clojure.core.server/start-server',
    ':name', 'repl',
    ':port', '5555',
    ':accept', 'clojure.core.server/repl',
    ':server-daemon', 'false'
  ])
