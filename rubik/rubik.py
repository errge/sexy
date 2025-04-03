#!/usr/bin/python3

import os
web = bool(os.getenv('RUBIK_IS_ON_THE_WEB'))

import asyncio
from copy import deepcopy
from itertools import product
from math import ceil
from random import choice
import sys

class ReadOrResize():
    def __init__(self):
        # By increasing stdout buffer, we reduce flickering, because only
        # sys.stdout.flush will talk to the terminal in one big batch.
        sys.stdout = open(1, 'w', buffering = 10485760)
        # This most likely is not strictly necessary anymore for us
        # with asyncio, but why not, sounds like the correct thing to do.
        sys.stdin = os.fdopen(0, buffering=0, mode='rb')
        self.initscreen()
        if web: return
        import tty
        import termios
        # Have to use termios.tcgetattr instead of return value of tty.setcbreak (python 3.12 is still too new).
        # The cbreak mode means, that we read characters from the terminal wo waiting for newline.
        self.tty_attrs = termios.tcgetattr(1)
        tty.setcbreak(1)
        import atexit
        atexit.register(self.cleanup)
        self.loop = asyncio.get_running_loop()
        self.queue = asyncio.Queue()
        import signal
        self.loop.add_signal_handler(signal.SIGWINCH, self.resize)
        self.loop.add_reader(sys.stdin, self.stdin)

    def initscreen(self):
        clearscreen()
        wrapoff()
        blackbackground()
        hidecursor()

    def cleanup(self):
        import termios
        termios.tcsetattr(1, termios.TCSAFLUSH, self.tty_attrs)
        wrapon()
        resetcolors()
        showcursor()
        print() # new line before exit, so next bash prompt is at the beginning
        sys.stdout.flush()

    def stdin(self):
        data = sys.stdin.read(1).decode('latin-1')
        if len(data) == 0 or data == '\x04':
            # \x04 is EOT, we get that on EOF from TTY in cbreak mode
            data = 'eof'
        self.loop.call_soon(self.queue.put_nowait, data)

    def resize(self):
        self.loop.call_soon(self.queue.put_nowait, 'resize')

    async def readOrResize(self):
        if web:
            from js import getInput
            return await getInput()
        else:
            try:
                return await self.queue.get()
            except KeyboardInterrupt:
                return 'eof'
            except asyncio.exceptions.CancelledError:
                return 'eof'

def pr(str):
    print(str, end = '')

# Good VT100 description: http://www.braun-home.net/michael/info/misc/VT100_commands.htm
def cursorhome():
    pr(chr(27) + '[H')

def clearscreen():
    pr(chr(27) + '[2J')

def wrapoff():
    pr(chr(27) + '[?7l')

def wrapon():
    pr(chr(27) + '[?7h')

def blackbackground():
    pr(chr(27) + '[48;2;0;0;0m')

def resetcolors():
    pr(chr(27) + '[0m')

def hidecursor():
    pr(chr(27) + '[?25l')

def showcursor():
    pr(chr(27) + '[?25h')

def strcursorleft(i):
    return chr(27) + f'[{i}D'

def nextline():
    # A very safe next line: go one line down and 1000 characters to the left.
    # But all these movement commands NEVER scroll (not even on the last line).
    # So we can accidentally overrun, and still no flickering of the screen.
    pr(chr(27) + '[1B' + chr(27) + '[1000D')

colors = [ # White, Green, Orange, Yellow, Red, Blue, Background, Instructions
    {
        'name': 'Original',
        'W': (255, 255, 255),
        'G': (0, 155, 72),
        'O': (255, 88, 0),
        'Y': (255, 213, 0),
        'B': (0, 64, 173),
        'R': (183, 18, 52),
        ' ': (0, 0, 0),
        'I': (102, 102, 102),
    },
    {
        # https://www.reddit.com/r/Cubers/comments/m9isgu/color_blind_cube_for_deuteranopia/
        'name': 'Colorblind',
        'W': (255, 255, 255),
        'G': (135, 62, 35),  # brown
        'O': (140, 140, 140),
        'Y': (255, 204, 0),
        'B': (0, 102, 255),
        'R': (40, 40, 40),
        ' ': (0, 0, 0),
        'I': (102, 102, 102),
    },
    {
        'name': 'Challenging',
        'W': (255, 255, 255),
        'G': (150, 150, 150),
        'O': (100, 100, 100),
        'Y': ( 60,  60,  60),
        'B': ( 40,  40,  40),
        'R': (  0,   0,   0),
        ' ': (0, 0, 0),
        'I': (102, 102, 102),
    },
    {
        'name': 'Hungarian',
        'W': (183, 18, 52),
        'G': (255, 255, 255),
        'O': (255, 88, 0),
        'Y': (0, 155, 72),
        'B': (255, 213, 0),
        'R': (0, 64, 173),
        ' ': (0, 0, 0),
        'I': (102, 102, 102),
    },
]

colorindex = 0

def colorswitch(diff):
    global colorindex
    colorindex += diff
    colorindex %= len(colors)

def coloredtext(text, rgb):
    r, g, b = rgb
    return chr(27) + f'[38;2;{r};{g};{b}m' + text

def whitetext(text):
    return coloredtext(text, colors[colorindex]['I'])

def colorchar(char, color_int):
    pr(coloredtext(char, colors[colorindex][chr(color_int)]))

upside    = [(0, 3), (0, 4), (0, 5), (1, 5), (2, 5), (2,4), (2, 3), (1, 3)]
uprow     = [(3, x) for x in range(12)]
midrow    = [(4, x) for x in range(12)]
midcol    = [(y, 4) for y in range(9)] + [(5, 10), (4, 10), (3, 10)]
downrow   = [(5, x) for x in range(12)]
downside  = [(y + 6, x) for (y, x) in upside]
rightside = [(3, 6), (3, 7), (3, 8), (4, 8), (5, 8), (5, 7), (5, 6), (4, 6)]
rightcol  = [(y, 5) for y in range(9)] + [(5, 9), (4, 9), (3, 9)]
leftside  = [(y, x - 6) for (y, x) in rightside]
leftcol   = [(y, 3) for y in range(9)] + [(5, 11), (4, 11), (3, 11)]
frontside = [(3, 3), (3, 4), (3, 5), (4, 5), (5, 5), (5, 4), (5, 3), (4, 3)]
frontcirc = [(2, 3), (2, 4), (2, 5), (3, 6), (4, 6), (5, 6), (6, 5), (6, 4), (6, 3), (5, 2), (4, 2), (3, 2)]
backside  = [(y, x + 6) for (y, x) in frontside]
backcirc  = [(0, 3), (0, 4), (0, 5), (3, 8), (4, 8), (5, 8), (8, 5), (8, 4), (8, 3), (5, 0), (4, 0), (3, 0)]

class Cube:
    def __init__(self):
        self.anim = 0.05
        self.state = []
        self.steps = 0
        self.history = [] # tuples of (self.move_fn, mul)
        for i in range(3):
            self.state.append(bytearray(' ' * 3 + 'W' * 3 + ' ' * 6, encoding = 'ascii'))
        for i in range(3):
            self.state.append(bytearray('O' * 3 + 'G' * 3 + 'R' * 3 + 'B' * 3, encoding = 'ascii'))
        for i in range(3):
            self.state.append(bytearray(' ' * 3 + 'Y' * 3 + ' ' * 6, encoding = 'ascii'))

    # Very hacky API: if begin is True, we return a tuple, where the second item is how many tiles to skip from the cube
    def instruction(self, row, rowrepeat, begin):
        match row, rowrepeat, begin:
            case 3, 0, True:
                return 'u ', 0
            case 3, 0, False:
                return ' i'
            case 4, 0, True:
                return 'a ', 0
            case 4, 1, True:
                return '◀◀', 0
            case 4, 0, False:
                return ' d'
            case 4, 1, False:
                return '▶▶'
            case 5, 1, True:
                return 'j ', 0
            case 5, 1, False:
                return ' k'
            case 0, 0, True:
                msg = '  Front   - m '
                return msg, 2
            case 0, 1, True:
                msg = "  Front'  - n "
                return msg, 2
            case 0, 2, True:
                msg = '  Back    - 7 '
                return msg, 2
            case 1, 0, True:
                msg = "  Back'   - 8 "
                return msg, 2
            case 1, 2, True:
                msg = "  Sexy    - ouli    "
                return msg, 3
            case 2, 0, True:
                msg = "  Sexy'   - uoil    "
                return msg, 3
            case 6, 1, True:
                msg = '  Shuffle - N '
                return msg, 2
            case 6, 2, True:
                msg = '  Undo    - x '
                return msg, 2
            case 7, 1, True:
                msg = '  Slower  - + '
                return msg, 2
            case 7, 2, True:
                msg = '  Faster  - - '
                return msg, 2
            case 8, 0, True:
                msg = '  Theme   - t/T     '
                return msg, 3
            case 8, 1, True:
                global colorindex
                msg = f"    {colors[colorindex]['name']:16s}"
                return msg, 3
            case 8, 2, True:
                if web:
                    msg = '  Restart - Q '
                else:
                    msg = '  Quit    - Q '
                return msg, 2
            case _, _, True:
                return '  ', 0
            case _, _, False:
                return '  '

    def draw(self):
        # Has to be kept in sync with web/index.ts
        w, h = (81, 30) if web else os.get_terminal_size()
        dw, dh = 75, 30
        vpad = int((h - dh) / 2)
        hpad = ' ' * ceil((w - dw) / 2)
        cursorhome()
        for _ in range(vpad):
            pr(' ' * w)
            nextline()
        pr(hpad + whitetext('                     y/z  ▲ w ▲   o                                        ') + hpad)
        nextline()
        for ri in range(len(self.state)):
            r = self.state[ri]
            for repeat in range(3):
                instruction, instruction_skip = self.instruction(ri, repeat, True)
                pr(hpad + whitetext(instruction))
                for c in r[instruction_skip:]:
                    if repeat == 0:
                        colorchar('▇▇▇▇▇ ', c)
                    if repeat == 1:
                        colorchar('█████ ', c)
                    if repeat == 2:
                        colorchar('▀▀▀▀▀ ', c)
                pr(strcursorleft(1) + whitetext(self.instruction(ri, repeat, False)) + hpad)
                nextline()

        pr(hpad + whitetext(f'                      h   ▼ s ▼   l               {self.steps:4d} Steps   {f"Anim: {self.anim:.2f}s " if self.anim > 0 else "Anim off    "}') + hpad)
        for _ in range(vpad + 1):
            nextline()
            pr(' ' * w)
        sys.stdout.flush()

    async def doanim(self, force = False):
        if self.anim == -1:
            # During shuffle we are skipping a lot of animations, so the shuffle finishes faster
            if self.steps % 10 == 0:
                self.draw()
                if web:
                    # Give xterm.js some time to draw
                    await asyncio.sleep(0)
            return 0
        if self.anim:
            await asyncio.sleep(self.anim)
            self.draw()
        elif force:
            self.draw()
        return 0

    def rotatestate(self, how, howmuch):
        newstate = deepcopy(self.state)
        for i in range(len(how)):
            y, x = how[i]
            y_, x_ = how[(i+howmuch) % len(how)]
            newstate[y][x] = self.state[y_][x_]
        self.state = newstate
        return 0

    def registermove(self, fn, mul, undo, counts = True):
        if undo:
            if counts: self.steps -= 1
        else:
            if counts: self.steps += 1
            self.history.append((fn, -mul))

    async def undo(self):
        if len(self.history) > 0:
            fn, mul = self.history.pop()
            await fn(mul, True)

    async def up(self, mul, undo = False):
        self.registermove(self.up, mul, undo)
        self.rotatestate(uprow, 1 * mul) + await self.doanim()
        for i in range(2):
            self.rotatestate(uprow, 1 * mul)
            self.rotatestate(upside, -1 * mul) + await self.doanim(True)

    async def down(self, mul, undo = False):
        self.registermove(self.down, mul, undo)
        self.rotatestate(downrow, -1 * mul) + await self.doanim()
        for i in range(2):
            self.rotatestate(downrow, -1 * mul)
            self.rotatestate(downside, -1 * mul) + await self.doanim(True)

    async def right(self, mul, undo = False):
        self.registermove(self.right, mul, undo)
        self.rotatestate(rightcol, 1 * mul) + await self.doanim()
        for i in range(2):
            self.rotatestate(rightcol, 1 * mul)
            self.rotatestate(rightside, -1 * mul) + await self.doanim(True)

    async def left(self, mul, undo = False):
        self.registermove(self.left, mul, undo)
        self.rotatestate(leftcol, 1 * mul) + await self.doanim()
        for i in range(2):
            self.rotatestate(leftcol, 1 * mul)
            self.rotatestate(leftside, 1 * mul) + await self.doanim(True)

    async def front(self, mul, undo = False):
        self.registermove(self.front, mul, undo)
        self.rotatestate(frontcirc, 1 * mul) + await self.doanim()
        for i in range(2):
            self.rotatestate(frontcirc, 1 * mul)
            self.rotatestate(frontside, 1 * mul) + await self.doanim(True)

    async def back(self, mul, undo = False):
        self.registermove(self.back, mul, undo)
        self.rotatestate(backcirc, 1 * mul) + await self.doanim()
        for i in range(2):
            self.rotatestate(backcirc, 1 * mul)
            self.rotatestate(backside, -1 * mul) + await self.doanim(True)

    async def cuberight(self, mul, undo = False):
        self.registermove(self.cuberight, mul, undo, False)
        for i in range(3):
            if i: self.rotatestate(upside, 1 * mul)
            if i: self.rotatestate(downside, -1 * mul)
            self.rotatestate(uprow, -1 * mul)
            self.rotatestate(midrow, -1 * mul)
            self.rotatestate(downrow, -1 * mul) + await self.doanim(True)

    async def cubeup(self, mul, undo = False):
        self.registermove(self.cubeup, mul, undo, False)
        for i in range(3):
            if i: self.rotatestate(leftside, 1 * mul)
            if i: self.rotatestate(rightside, -1 * mul)
            self.rotatestate(leftcol, 1 * mul)
            self.rotatestate(midcol, 1 * mul)
            self.rotatestate(rightcol, 1 * mul) + await self.doanim(True)

async def main():
    readOrResize = ReadOrResize()
    cube = Cube()
    cube.draw()
    while True:
        key = await readOrResize.readOrResize()
        match key:
            case 'resize':
                cube.draw()
            case 'x' | '\x7f' | '\x08':
                await cube.undo()
            case 'Q' | 'eof':
                if web:
                    # No quitting on the web, just restarting
                    cube.__init__()
                    cube.draw()
                else:
                    break
            case 'u':
                await cube.up(1)
            case 'i':
                await cube.up(-1)
            case 'k':
                await cube.down(1)
            case 'j':
                await cube.down(-1)
            case 'o':
                await cube.right(1)
            case 'l':
                await cube.right(-1)
            case 'y' | 'z':
                await cube.left(1)
            case 'h':
                await cube.left(-1)
            case 'n':
                await cube.front(1)
            case 'm':
                await cube.front(-1)
            case '7':
                await cube.back(1)
            case '8':
                await cube.back(-1)
            case 'd':
                await cube.cuberight(1)
            case 'a':
                await cube.cuberight(-1)
            case 'w':
                await cube.cubeup(1)
            case 's':
                await cube.cubeup(-1)
            case '+' | '=':
                cube.anim += 0.01
                cube.draw()
            case 't':
                colorswitch(1)
                cube.draw()
            case 'T':
                colorswitch(-1)
                cube.draw()
            case '-' | '_':
                cube.anim -= 0.01
                cube.anim = max(cube.anim, 0)
                cube.draw()
            case 'N':
                shuffle = list(product([cube.left, cube.front, cube.right, cube.up, cube.down, cube.back], [-1, 1, 2]))
                oldanim = cube.anim
                cube.anim = -1
                for s in range(400):
                    f, i = choice(shuffle)
                    await f(i)
                cube.anim = oldanim
                cube.history, cube.steps = [], 0
                cube.draw()
            case 'L' | '\x0c': # Ctrl-L
                readOrResize.initscreen()
                cube.draw()
            # case 'W': # put some waste, so we can test Ctrl-l
            #     pr(whitetext('xxx\n'))
            #     pr(whitetext('xxx\n'))
            #     pr(whitetext('xxx\n'))
            #     pr(whitetext('xxx\n'))
            #     sys.stdout.flush()

if not web:
    asyncio.run(main())
# else postamble in web/index.ts
