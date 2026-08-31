#!/usr/bin/env bash
# Blind-grade finance A-F + community A-F + Gg. Excludes Fg.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export JUDGE_API_KEY="${JUDGE_API_KEY:-${DASHSCOPE_API_KEY:-}}"
: "${JUDGE_API_KEY:?set DASHSCOPE_API_KEY or JUDGE_API_KEY}"
ENDPOINT="${JUDGE_ENDPOINT:-https://dashscope.aliyuncs.com/compatible-mode/v1}"
MODEL="${JUDGE_MODEL:-qwen3.8-max}"
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/tmp/vlift-pyc}"

grade_one() {
  local domain="$1" cfg="$2" set_path="$3" resp_dir="$4" grade_dir="$5"
  local resp="$resp_dir/resp_${cfg}.jsonl"
  local out="$grade_dir/grade_${cfg}.jsonl"
  echo "[grade] $domain $cfg"
  python3 "$ROOT/scripts/vertical_lift_grader.py" \
    --set "$set_path" \
    --responses "$resp" \
    --judge-model "$MODEL" \
    --judge-endpoint "$ENDPOINT" \
    --judge-key-env JUDGE_API_KEY \
    --out "$out"
  python3 - <<PY
import json
from pathlib import Path
rows=[json.loads(l) for l in Path("$out").read_text().splitlines() if l.strip()]
ok=sum(1 for r in rows if r.get("judge_valid"))
print(f"GRADE_OK {Path('$out').name} valid {ok}/{len(rows)}")
if ok < len(rows):
    bad=[(r['scenario_id'], r.get('judge_error','')[:120]) for r in rows if not r.get('judge_valid')]
    print("UNRESOLVED", bad[:5])
PY
}

FIN_SET="$ROOT/vertical_lift/finance/dev_v0.4.jsonl"
COM_SET="$ROOT/vertical_lift/community/dev_v0.4.jsonl"
FIN_RESP="$ROOT/vertical_lift/results/public_v0.4_finance/responses"
COM_RESP="$ROOT/vertical_lift/results/public_v0.4_community/responses"
FIN_GRADE="$ROOT/vertical_lift/results/public_v0.4_finance/grades"
COM_GRADE="$ROOT/vertical_lift/results/public_v0.4_community/grades"
mkdir -p "$FIN_GRADE" "$COM_GRADE"

PHASE="${1:-all}"
case "$PHASE" in
  finance)
    for cfg in A B C D E F; do grade_one finance "$cfg" "$FIN_SET" "$FIN_RESP" "$FIN_GRADE"; done
    ;;
  community)
    for cfg in A B C D E F Gg; do grade_one community "$cfg" "$COM_SET" "$COM_RESP" "$COM_GRADE"; done
    ;;
  all)
    for cfg in A B C D E F; do grade_one finance "$cfg" "$FIN_SET" "$FIN_RESP" "$FIN_GRADE"; done
    for cfg in A B C D E F Gg; do grade_one community "$cfg" "$COM_SET" "$COM_RESP" "$COM_GRADE"; done
    ;;
  *)
    echo "usage: $0 {finance|community|all}"; exit 1
    ;;
esac
echo "[grade] phase=$PHASE done"
