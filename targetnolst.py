
""" Execute an interpreter that reads on stdin (REPL)
"""

#from nolst.sourceparser import main

# main()

from rpython.rlib.streamio import open_file_as_stream
from rpython.jit.codewriter.policy import JitPolicy
from nolst.interpreter import interpret
import sys
import os

def main(argv):
    #f = open_file_as_stream(argv[1])
    content = os.read(0, 4096)
    interpret(content)
    return 0

def target(driver, args):
    return main, None

def jitpolicy(driver):
    return JitPolicy()


if __name__ == '__main__':
    main(sys.argv)
