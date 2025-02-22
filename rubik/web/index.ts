import "@xterm/xterm/css/xterm.css";
import type { Instance } from "@wasmer/sdk";
import { Terminal } from "@xterm/xterm";
import { WebglAddon } from '@xterm/addon-webgl';

// What is this? Why is it needed? Without it the init fails.
// @ts-ignore
import WasmModule from "@wasmer/sdk/wasm?url";

async function main() {
    const { Directory, Wasmer, init } = await import("@wasmer/sdk");

    // const log = "trace";
    const log = undefined;
    await init({ log, module: WasmModule });

    const term = new Terminal({
        rows: 30,
        cols: 81,
        scrollback: 0,
        fontFamily: "Fira Mono, DejaVu Sans Mono, Noto Sans Mono, monospace",
        lineHeight: 1.0,
        convertEol: true,
    });
    term.open(document.getElementById("terminal")!);
    // Without this, there are gaps between the block characters.
    term.loadAddon(new WebglAddon());

    term.writeln("Loading...");
    const pkg = await Wasmer.fromRegistry("python/python");
    const home = new Directory();
    const rubik_py = await (await fetch("rubik.py")).text();
    await home.writeFile("main.py", rubik_py);

    term.writeln("Starting...");
    const instance = await pkg.entrypoint!.run({ args: ["main.py"], mount: { "/home": home }, cwd: "/home" });
    connectStreams(instance, term);

    document.addEventListener("click", (_evnt) => term.focus());
    term.focus();
}

const encoder = new TextEncoder();

function connectStreams(instance: Instance, term: Terminal) {
    const stdin = instance.stdin?.getWriter();
    term.onData(data => stdin?.write(encoder.encode(data)));
    instance.stdout.pipeTo(new WritableStream({ write: chunk => term.write(chunk) }));
    instance.stderr.pipeTo(new WritableStream({ write: chunk => term.write(chunk) }));
}

console.log("Hello there, fancy that you know about the console, good job!");
main().catch(console.error);
