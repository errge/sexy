import "@xterm/xterm/css/xterm.css";
import { Terminal } from "@xterm/xterm";
import { CanvasAddon } from "@xterm/addon-canvas";

import { loadPyodide } from "pyodide";

class IO {
    term: Terminal;

    stdin_queue: string[] = [];
    inputAvailable = () => { };

    constructor(term: Terminal) {
        this.term = term;
        this.term.onData(this.pushIn);
        window.getInput = this.getInput;
    }

    pushIn = (key: string): void => {
        this.stdin_queue.push(key);
        this.inputAvailable();
    }

    getInput = async (): Promise<string> => {
        if (this.stdin_queue.length === 0) {
            const { promise, resolve } = Promise.withResolvers();
            this.inputAvailable = resolve;
            await promise;
        }

        const ret: string = this.stdin_queue.shift();

        // TODO: what to do when we don't work char-by-char???
        if (ret.length === 1 && ret[0] == "\x7F") {
            // fix xtermjs backspace handling
            return "\b";
        }

        return ret;
    }

    // Runs inside Pyodide's code as a callback
    pushOut = (buffer: Uint8Array): number => {
        // The "new Uint8Array" look superfluous here, but it's
        // actually important!  It creates a deep copy of the input,
        // and therefore it's safe when python uses the same buffer
        // quickly to pass even more data to print very soon.  We just
        // create deep copys of the buffers and therefore we have an
        // "output queue" with term.write.
        this.term.write(new Uint8Array(buffer), () => {
            // Called when xterm MUCH later actually finishes drawing.
            // Maybe we could do something with this to optimize
            // out the GC regarding all the Uint8Array allocations.
        });
        return buffer.length;
    }
}

function autoSize(term) {
    term.options.fontSize = 6;
    while (term.element.clientHeight < window.innerHeight && term.element.clientWidth < window.innerWidth) {
        term.options.fontSize++;
    }
    term.options.fontSize--;
}

const term = new Terminal({
    rows: 30,
    cols: 81,
    scrollback: 0,
});

async function main() {
    term.open(document.getElementById("terminal"));
    autoSize(term)
    window.addEventListener('resize', () => autoSize(term));

    // Do not handle any keys with combinators, so the user can still use browser keyboard shortcuts.
    // The ev.key.length > 1 condition is mostly there for F12...
    term.attachCustomKeyEventHandler(ev => {
        // Backspace is undo, so we want to steal that from the browser
        if ((ev.ctrlKey || ev.metaKey || ev.altKey || ev.key.length > 1) && (ev.key !== "Backspace"))
            return false;
        else
            return true;
    });

    // Without this, there are gaps between the block characters and performance is not good enough.
    term.loadAddon(new CanvasAddon());

    const io = new IO(term);

    term.writeln("Loading...");
    let pyodide = await loadPyodide();
    pyodide.setStdin({ read: io.popIn });
    pyodide.setStdout({ write: io.pushOut });
    pyodide.setStderr({ write: io.pushOut });

    term.writeln("Starting...");
    // Preamble is intentionally a zero-liner, so line numbers are correct
    // in python exceptions that may happen on the python side.
    const preamble = `import os;os.environ["RUBIK_IS_ON_THE_WEB"] = "1";`;
    const code = (await import("/public/rubik.py?raw")).default;

    // Cannot put this in the real code, because top-level await is
    // python error even inside a never running if.
    const postamble = `await main()\n`;

    document.addEventListener("click", (_evnt) => term.focus());
    term.focus();

    return pyodide.runPythonAsync(preamble + code + postamble);
}

console.log("Hello there, fancy that you know about the console, good job!");
main().catch(res => term.writeln(res.toString().replaceAll("\n", "\r\n"))).then(res => term.writeln("Python finished"));
