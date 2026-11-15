#!/usr/bin/env bash
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "=========================================================="
echo "      Starting PrivateDrive (WebDAV Virtual Drive)        "
echo "=========================================================="

python3 "$DIR/app.py" "$@"
