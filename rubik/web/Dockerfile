FROM nilcons/debian
RUN apt-get update
RUN apt-get install -y nodejs
RUN curl -fsSL https://get.pnpm.io/install.sh | PNPM_HOME=/pnpm bash
WORKDIR /data
COPY package.json pnpm-lock.yaml vite.config.js /data/
RUN /pnpm/pnpm install
COPY index.html index.ts mini-coi.js style.css rubik.py /data/
RUN node_modules/.bin/vite build --base=/sexy/rubik/
RUN tar -c -f /output.tar dist
