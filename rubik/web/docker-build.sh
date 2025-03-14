#!/bin/bash

set -euo pipefail

# Build the 2D Rubik's Cube
rm -rf dist .iid
docker build --iidfile .iid -f Dockerfile ..
mkdir -p dist/rubik

# Put it in dist/rubik (https://errge.github.io/sexy/rubik)
docker run --rm $(cat .iid) cat /output.tar | tar -xv --strip-components=1 -C dist/rubik

# Put the sexy color puzzle game in dist/ (https://errge.github.io/sexy)
cp ../../index.html dist

# Local sexy symlink hack for people who want to test on local webserver
( cd dist ; ln -s . sexy )
