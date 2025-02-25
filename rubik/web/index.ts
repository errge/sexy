import "@xterm/xterm/css/xterm.css";
import type { Instance } from "@wasmer/sdk";
import { Terminal } from "@xterm/xterm";
import { CanvasAddon } from "@xterm/addon-canvas";

async function main() {
    // From: https://github.com/wasmerio/wasmer-js/blob/905e9a8a4cf09486abfe14f9ec2adc242574d24a/examples/wasmer.sh/index.ts
    // Note: We dynamically import the Wasmer SDK to make sure the bundler puts
    // it in its own chunk. This works around an issue where just importing xterm.js
    // runs top-level code which accesses the DOM, and if it's in the same chunk
    // as @wasmer/sdk, each Web Worker will try to run this code and crash.
    // See https://github.com/wasmerio/wasmer-js/issues/373
    const { Directory, Wasmer, init } = await import("@wasmer/sdk");
    await init();

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
    term.loadAddon(new CanvasAddon());

    term.writeln("Loading...");
    const pkg = await Wasmer.fromRegistry("python/python");
    const home = new Directory();
    const rubik_py = (await import('/public/rubik.py?raw')).default;
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
