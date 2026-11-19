#!/bin/sh
# Packages the committed starter/ folder (no venvs, caches or node_modules) into static/starter.zip.
set -e
cd "$(dirname "$0")/.."
git archive --format=zip --prefix=starter/ -o server/static/starter.zip HEAD:starter
