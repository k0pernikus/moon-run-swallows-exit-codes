#!/usr/bin/env bash
# shellcheck shell=bash
set -euo pipefail
if [[ $# -eq 0 ]]; then
  echo "usage: ${0##*/} <task name> [task name...]" >&2
  exit 64
fi
missing=0
for name in "$@"; do
  if [[ ! -f ".${name}-finished" ]]; then
    echo "${name} did not run to completion" >&2
    missing=1
  fi
done
exit "${missing}"
