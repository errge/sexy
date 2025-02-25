FROM nilcons/debian
RUN apt-get update
RUN apt-get install -y nodejs
RUN curl -fsSL https://get.pnpm.io/install.sh | PNPM_HOME=/pnpm bash
WORKDIR /data
COPY web/package.json /data/
RUN /pnpm/pnpm install
COPY web/index.html web/index.ts web/style.css /data/
COPY rubik.py web/mini-coi.js /data/public/
RUN node_modules/.bin/vite build --base=/sexy/rubik/
RUN tar -c -f /output.tar dist
