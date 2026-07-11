#!/usr/bin/env bash
set -euo pipefail
codes=(70 80 90)
code="${codes[$((RANDOM % ${#codes[@]}))]}"
echo "fail.sh exiting with code ${code}" >&2
exit "${code}"
