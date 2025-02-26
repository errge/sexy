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

async def getChar():
    latency = 0.01
    while True:
        ret = sys.stdin.read(1)
        if ret: return ret
        await asyncio.sleep(latency)

async def main():
    while True:
        s = await getChar()
        print("YAY! You pressed " + s)
        print("Again, you pressed " + s)

if not web:
    import tty
    tty.setcbreak(1)
    try:
        asyncio.run(main())
    finally:
        print("finished")
else:
    asyncio.get_event_loop().run_until_complete(main())
