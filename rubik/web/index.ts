import "@xterm/xterm/css/xterm.css";
import { Terminal } from "@xterm/xterm";
import { CanvasAddon } from "@xterm/addon-canvas";

import { loadPyodide } from "pyodide";

class IO {
    encoder: TextEncoder;
    stdin_queue: string[];
    term: Terminal;

    constructor(term: Terminal) {
        this.encoder = new TextEncoder();
        this.stdin_queue = [];
        this.term = term;
        this.term.onData(this.pushIn);
    }

    pushIn = (key: string): void => {
        this.stdin_queue.push(key);
    }

    popIn = (buffer: Uint8Array): number => {
        if (this.stdin_queue.length === 0) {
            return 0;
        } else {
            buffer[0] = this.encoder.encode(this.stdin_queue.shift())[0];
            if (buffer[0] == 127) {
                // fix xtermjs backspace handling
                buffer[0] = 8;
            }
            return 1;
        }
    }

    pushOut = (buffer: Uint8Array): number => {
        // The "new Uint8Array" look superfluous here, but it's
        // actually important!  It creates a deep copy of the input,
        // and therefore it's safe when python uses the same buffer
        // quickly to pass even more data to print very soon.  We just
        // create deep copys of the buffers and therefore we have an
        // "output queue" with term.write.
        this.term.write(new Uint8Array(buffer));
        return buffer.length;
    }
}

async function main(): Promise<void> {
    const term = new Terminal({
        rows: 30,
        cols: 81,
        scrollback: 0,
    });
    term.open(document.getElementById("terminal")!);

    // Do not handle any keys with combinators, so the user can still use browser keyboard shortcuts.
    // The ev.key.length > 1 condition is mostly there for F12...
    term.attachCustomKeyEventHandler(ev => {
        if (ev.ctrlKey || ev.metaKey || ev.altKey || ev.key.length > 1)
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
    const preamble = `import os\nos.environ["RUBIK_IS_ON_THE_WEB"] = "1"\n`;
    const code = (await import("/public/rubik.py?raw")).default;

    document.addEventListener("click", (_evnt) => term.focus());
    term.focus();

    await pyodide.runPythonAsync(preamble + code);
}

console.log("Hello there, fancy that you know about the console, good job!");
main().catch(console.error);
