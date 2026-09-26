#!/usr/bin/env bash
# shellcheck shell=bash
set -euo pipefail
if [[ $# -ne 3 ]]; then
  echo "usage: ${0##*/} <name> <signal bit value> <seconds>" >&2
  exit 64
fi
name="$1"
signal="$2"
seconds="$3"
sleep "${seconds}"
touch ".${name}-finished"
code=$((64 | signal))
echo "${name} finished after ${seconds}s, exiting 64 | ${signal} = ${code}" >&2
exit "${code}"
