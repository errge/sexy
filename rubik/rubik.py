#!/usr/bin/python3

from copy import deepcopy
from itertools import product
from math import ceil
import os
from random import choice
import sys

import termios
import time
import tty

# By increasing stdout buffer, we reduce flickering, because only
# sys.stdout.flush will talk to the terminal in one big batch.
sys.stdout = open(1, "w", buffering = 10485760)

class ReadOrResize():
    def __init__(self):
        import signal
        import socket
        import selectors

        # Reopen stdin unbuffered binary, because otherwise if the user
        # is pressing buttons faster than the animation, then our selector
        # gets stuck.
        sys.stdin = os.fdopen(0, buffering=0, mode='rb')

        self.read, self.write = socket.socketpair()
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.read, selectors.EVENT_READ)
        self.selector.register(sys.stdin, selectors.EVENT_READ)
        self.handler = lambda _signal, _frame: self.tick()
        signal.signal(signal.SIGWINCH, self.handler)

    def tick(self):
        self.write.send(b'\0')

    def readOrResize(self):
        for key, _ in self.selector.select():
            if key.fileobj == sys.stdin:
                return sys.stdin.read(1).decode('ascii')
            else:
                self.read.recv(1)
                return "resize"

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

colors = {
    'W': (255, 255, 255),
    'G': (0, 155, 72),
    'O': (255, 88, 0),
    'Y': (255, 213, 0),
    'R': (183, 18, 52),
    'B': (0, 64, 173),
    ' ': (0, 0, 0),    # Use to print background, black
    'I': (102, 102, 102), # Instructions
}

def coloredtext(text, rgb):
    r, g, b = rgb
    print(chr(27) + f'[38;2;{r};{g};{b}m', end = '')

    return text

def whitetext(text):
    return coloredtext(text, colors['I'])

def colorchar(char, color_int):
    pr(coloredtext(char, colors[chr(color_int)]))

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
            case (4, 0, True):
                return 'a ', 0
            case (4, 1, True):
                return '◀◀', 0
            case (4, 0, False):
                return ' d'
            case (4, 1, False):
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
                msg = '  Slower  - + '
                return msg, 2
            case 6, 2, True:
                msg = '  Faster  - - '
                return msg, 2
            case 7, 1, True:
                msg = '  Shuffle - N '
                return msg, 2
            case 7, 2, True:
                msg = '  Undo    - x '
                return msg, 2
            case 8, 2, True:
                msg = '  Quit    - Q '
                return msg, 2
            case _, _, True:
                return '  ', 0
            case _, _, False:
                return '  '

    def draw(self):
        w, h = os.get_terminal_size()
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

        pr(hpad + whitetext(f'                      h   ▼ s ▼   l               {self.steps:4d} Steps   {f"Anim: {self.anim:.2f}s " if self.anim else "Anim off    "}') + hpad)
        for _ in range(vpad + 1):
            nextline()
            pr(' ' * w)
        sys.stdout.flush()

    def doanim(self, force = False):
        if self.anim:
            time.sleep(self.anim)
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

    def undo(self):
        if len(self.history) > 0:
            fn, mul = self.history.pop()
            fn(mul, True)

    def up(self, mul, undo = False):
        self.registermove(self.up, mul, undo)
        self.rotatestate(uprow, 1 * mul) + self.doanim()
        for i in range(2):
            self.rotatestate(uprow, 1 * mul)
            self.rotatestate(upside, -1 * mul) + self.doanim(True)

    def down(self, mul, undo = False):
        self.registermove(self.down, mul, undo)
        self.rotatestate(downrow, -1 * mul) + self.doanim()
        for i in range(2):
            self.rotatestate(downrow, -1 * mul)
            self.rotatestate(downside, -1 * mul) + self.doanim(True)

    def right(self, mul, undo = False):
        self.registermove(self.right, mul, undo)
        self.rotatestate(rightcol, 1 * mul) + self.doanim()
        for i in range(2):
            self.rotatestate(rightcol, 1 * mul)
            self.rotatestate(rightside, -1 * mul) + self.doanim(True)

    def left(self, mul, undo = False):
        self.registermove(self.left, mul, undo)
        self.rotatestate(leftcol, 1 * mul) + self.doanim()
        for i in range(2):
            self.rotatestate(leftcol, 1 * mul)
            self.rotatestate(leftside, 1 * mul) + self.doanim(True)

    def front(self, mul, undo = False):
        self.registermove(self.front, mul, undo)
        self.rotatestate(frontcirc, 1 * mul) + self.doanim()
        for i in range(2):
            self.rotatestate(frontcirc, 1 * mul)
            self.rotatestate(frontside, 1 * mul) + self.doanim(True)

    def back(self, mul, undo = False):
        self.registermove(self.back, mul, undo)
        self.rotatestate(backcirc, 1 * mul) + self.doanim()
        for i in range(2):
            self.rotatestate(backcirc, 1 * mul)
            self.rotatestate(backside, -1 * mul) + self.doanim(True)

    def cuberight(self, mul, undo = False):
        self.registermove(self.cuberight, mul, undo, False)
        for i in range(3):
            if i: self.rotatestate(upside, 1 * mul)
            if i: self.rotatestate(downside, -1 * mul)
            self.rotatestate(uprow, -1 * mul)
            self.rotatestate(midrow, -1 * mul)
            self.rotatestate(downrow, -1 * mul) + self.doanim(True)

    def cubeup(self, mul, undo = False):
        self.registermove(self.cubeup, mul, undo, False)
        for i in range(3):
            if i: self.rotatestate(leftside, 1 * mul)
            if i: self.rotatestate(rightside, -1 * mul)
            self.rotatestate(leftcol, 1 * mul)
            self.rotatestate(midcol, 1 * mul)
            self.rotatestate(rightcol, 1 * mul) + self.doanim(True)

# cbreak mode means, that we read characters from the terminal wo waiting for newline
# Have to use termios.tcgetattr instead of trusting return of tty.setcbreak (python 3.12 is still too new).
tty_attrs = termios.tcgetattr(1)
tty.setcbreak(1)
clearscreen()
wrapoff()
blackbackground()
hidecursor()

try:
    readOrResize = ReadOrResize()
    cube = Cube()
    cube.draw()
    while True:
        key = readOrResize.readOrResize()
        match key:
            case 'resize':
                cube.draw()
            case 'x':
                cube.undo()
            case 'Q':
                break
            case 'u':
                cube.up(1)
            case 'i':
                cube.up(-1)
            case 'k':
                cube.down(1)
            case 'j':
                cube.down(-1)
            case 'o':
                cube.right(1)
            case 'l':
                cube.right(-1)
            case 'y' | 'z':
                cube.left(1)
            case 'h':
                cube.left(-1)
            case 'n':
                cube.front(1)
            case 'm':
                cube.front(-1)
            case '7':
                cube.back(1)
            case '8':
                cube.back(-1)
            case 'd':
                cube.cuberight(1)
            case 'a':
                cube.cuberight(-1)
            case 'w':
                cube.cubeup(1)
            case 's':
                cube.cubeup(-1)
            case '+' | '=':
                cube.anim += 0.01
                cube.draw()
            case '-' | '_':
                cube.anim -= 0.01
                cube.anim = max(cube.anim, 0)
                cube.draw()
            case 'N':
                shuffle = list(product([cube.left, cube.front, cube.right, cube.up, cube.down, cube.back], [-1, 1, 2]))
                oldanim = cube.anim
                cube.anim = 0
                for s in range(100):
                    f, i = choice(shuffle)
                    f(i)
                cube.anim = oldanim
                cube.history, cube.steps = [], 0
                cube.draw()

finally:
    # restore input buffering
    termios.tcsetattr(1, termios.TCSAFLUSH, tty_attrs)
    wrapon()
    resetcolors()
    showcursor()
    # new line at end of program
    print()
    sys.stdout.flush()
