FROM nilcons/debian
RUN apt-get update
RUN apt-get install -y nodejs

# Pyodide
RUN mkdir -p /data/public/assets ; cd /data/public/assets ; \
    wget -O pyodide-core.tbz2 https://github.com/pyodide/pyodide/releases/download/0.27.3/pyodide-core-0.27.3.tar.bz2 ; \
    tar --strip-components=1 -xvaf pyodide-core.tbz2 pyodide/python_stdlib.zip pyodide/pyodide.asm.wasm pyodide/pyodide.asm.js pyodide/pyodide-lock.json ; \
    rm -f pyodide-core.tbz2

RUN curl -fsSL https://get.pnpm.io/install.sh | PNPM_HOME=/pnpm bash
COPY web/package.json /data/
RUN cd /data && /pnpm/pnpm install
COPY web/index.html web/index.ts web/style.css /data/
COPY test.py rubik.py /data/public/
RUN cd /data && node_modules/.bin/vite build --base=/sexy/rubik/ && tar -c -f /output.tar dist
