#!/usr/bin/env bash
# usage: system/repro.sh <institution folder>   runs the system 5 times and prints each run's SHA-256
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tmp="$(mktemp -d)"
for i in 1 2 3 4 5; do "$here/run" "$1" "$tmp/run_$i.jsonl"; sha256sum "$tmp/run_$i.jsonl" | cut -d' ' -f1; done | sort | uniq -c
rm -rf "$tmp"
