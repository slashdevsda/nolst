# coding: utf-8
#from __future__ import print_function
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

    interactive = False
    for a in argv:
        if a in ('-i', '--interacive'):
            interactive = True

    p_count = 0
    content = ""
    # save context upon sequencial
    # executions
    frame = None

    while True:
        if interactive:
            os.write(1, '―→ ')
            #sys.stdout.flush()
        readed = os.read(0, 4096)

        if not readed or not len(readed):
            break

        for ch in readed:
            if ch == '(':
                p_count += 1
            elif ch == ')':
                p_count -= 1

        content += readed

        if p_count < 0:
            print("Error, unexpected ')'")
            content = ""
            p_count = 0

        if len(content.strip('\n')) and p_count == 0:
            frame = interpret(content, frame)
            content = ""
    return 0

def target(driver, args):
    return main, None

def jitpolicy(driver):
    return JitPolicy()


if __name__ == '__main__':
    main(sys.argv)
