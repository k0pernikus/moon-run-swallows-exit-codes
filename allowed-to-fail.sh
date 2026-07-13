#!/usr/bin/env bash
# shellcheck shell=bash
set -euo pipefail
if [[ $# -eq 0 ]]; then
  echo "usage: ${0##*/} <command> [args...]" >&2
  exit 64
fi
code=0
"$@" || code=$?
echo "observed exit code ${code}" >&2
case "${code}" in
  70 | 80 | 90)
    echo "exit code ${code} is allowed to fail" >&2
    exit 0
    ;;
esac
exit "${code}"
