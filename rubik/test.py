#!/usr/bin/python3

# This is to demo, how do we write terminal python programs that work
# both on the web and in the command line.

# Instead of wasmer we use pyodide (wasmer is 200MB, pyodide is 15MB).

# We choose the easy setup of running pyodide on the main thread (not
# in a web worker), and we use pyodide without any posix in it (no
# WASI, WASIX, etc.), so we will have no terminal handling (cbreak).

# But xterm.js can still handle the color codes and cursor moving as
# expected, so apart from a little bit of differences, the code can be
# mostly shared between the web and console.

import os
web = bool(os.getenv('RUBIK_IS_ON_THE_WEB'))

import asyncio
import sys

if web:
    from js import getInput
else:
    sys.stdin = os.fdopen(0, buffering=0, mode='rb')
    async def getInput():
        # TODO: when games will support keys like UP
        # then we have to read out the full escape
        # sequence char-by-char (like a prefix code)
        return sys.stdin.read(1)

async def main():
    print('Started', end = '\r\n')
    while True:
        s = await getInput()
        if s == b'\x0c':
            s = '^L'
        print('YAY! You pressed ' + repr(s), end = '\r\n')
        print('Again, you pressed ' + repr(s), end = '\r\n')

if not web:
    import tty
    tty.setcbreak(1)
    try:
        asyncio.run(main())
    finally:
        print('finished')
# else postamble in web/index.ts
