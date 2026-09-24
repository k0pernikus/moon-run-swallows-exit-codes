#!/usr/bin/env bash
# shellcheck shell=bash
set -euo pipefail
if [[ $# -lt 2 ]]; then
  echo "usage: ${0##*/} <expected exit code> <command> [args...]" >&2
  exit 64
fi
expected="$1"
shift
code=0
"$@" || code=$?
echo "observed exit code ${code}, expected ${expected}" >&2
if [[ "${code}" -ne "${expected}" ]]; then
  exit 1
fi
