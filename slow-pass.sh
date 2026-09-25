#!/usr/bin/env bash
# shellcheck shell=bash
set -euo pipefail
sleep 5
touch .slow-pass-finished
echo "slow-pass.sh finished after 5 seconds" >&2
