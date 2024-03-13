#! /usr/bin/env python3
import os, random, subprocess

if __name__ == '__main__':
  os.chdir(os.path.dirname(__file__) + "/..")
  
  port = random.randint(1025, 65535)
  print(f"Starting Server Socket REPL at port {port}", flush = True)
  with open(".repl-port", "w") as file:
    file.write(str(port))
  
  subprocess.check_call(['clojure',
    '-J--add-opens=java.base/java.io=ALL-UNNAMED',
    '-X', 'clojure.core.server/start-server',
    ':name', 'repl',
    ':port', str(port),
    ':accept', 'clojure.core.server/repl',
    ':server-daemon', 'false'
  ])

  os.remove(".repl-port")