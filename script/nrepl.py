#! /usr/bin/env python3
import os, subprocess

if __name__ == '__main__':
  os.chdir(os.path.dirname(__file__))
  subprocess.check_call(['clojure',
    '-Sdeps', '{:deps {nrepl/nrepl {:mvn/version "0.8.3"}}}',
    '-M', '-m', 'nrepl.cmdline',
    '--port', '5555'
  ])
