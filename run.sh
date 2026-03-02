#!/usr/bin/env bash
set -euo pipefail

export GEMINI_API_KEY="AIzaSyB4Bw14nL122mNd0oU75gU0RsgQlXoaK6g"

PYTHON="/usr/local/bin/python3.11"
QUERY="${1:-帮我找MIT CS硕士的GPA要求和语言要求}"
OUT="${2:-out}"
MAX_STEPS="${3:-10}"

exec "$PYTHON" -m app.runner "$QUERY" --out "$OUT" --max-steps "$MAX_STEPS"
