#!/usr/bin/env bash
set -euo pipefail

# ── Config ──────────────────────────────────────────────
export GEMINI_API_KEY="${GEMINI_API_KEY:-AIzaSyD3CmScILLkHoH1Le_pgCyYamqf6CO4ExQ}"
PYTHON="/usr/local/bin/python3.11"
MAX_STEPS="${MAX_STEPS:-20}"
OUT="${OUT:-out}"
# ────────────────────────────────────────────────────────

if [ $# -eq 0 ]; then
  echo "Usage: ./run.sh \"<query>\" [output_dir] [max_steps]"
  echo ""
  echo "Examples:"
  echo "  ./run.sh \"帮我找MIT CS硕士的GPA要求和语言要求\""
  echo "  ./run.sh \"帮我找香港城市大学商科相关专业的申请截止时间\" out/ 15"
  echo "  ./run.sh \"Stanford CS Master deadlines\""
  echo ""
  echo "Env vars:"
  echo "  GEMINI_API_KEY  — Gemini API key (required)"
  echo "  MAX_STEPS       — max agent steps (default: 20)"
  echo "  OUT             — output directory (default: out)"
  exit 1
fi

QUERY="$1"
OUT="${2:-$OUT}"
MAX_STEPS="${3:-$MAX_STEPS}"

exec "$PYTHON" -m app.runner "$QUERY" --out "$OUT" --max-steps "$MAX_STEPS"
