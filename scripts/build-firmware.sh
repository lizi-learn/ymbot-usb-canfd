#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root/firmware/upstream"
make -j2 GIT_VERSION=b158aa7 GIT_REMOTE=github.com/normaldotcom/canable2-fw
sha256sum build/canable2-b158aa7.bin
# Compiler versions can change the binary. The flash CLI intentionally accepts
# only the distributed GCC 10.3.1 image, never an unreviewed rebuilt image.
