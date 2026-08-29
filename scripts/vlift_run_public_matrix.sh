#!/usr/bin/env bash
# Run public-12 canary then full A-F + Cp/Dp against a local OpenAI-compatible endpoint.
# PUBLIC SET ONLY. Never pass private_eval paths.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="${VLIFT_OUT_DIR:-$ROOT/vertical_lift/results/public_v0.4}"
ENDPOINT="${VLIFT_ENDPOINT:-http://127.0.0.1:8000/v1}"
API_KEY_ENV="${VLIFT_API_KEY_ENV:-VLIFT_API_KEY}"
SET_PATH="$ROOT/vertical_lift/companion/dev_v0.4.jsonl"
TEMPERATURE=0
MAX_TOKENS=800
PHASE="${1:-canary}"  # canary | general | vertical | sensitivity | all

mkdir -p "$OUT_DIR"
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/tmp/vlift-pyc}"

if [[ -n "${!API_KEY_ENV:-}" ]]; then
  KEY_ARGS=(--api-key-env "$API_KEY_ENV")
else
  KEY_ARGS=(--allow-empty-api-key)
fi

run_one() {
  local cfg="$1" model="$2" prompt="$3" subset="$4"
  local out="$OUT_DIR/resp_${cfg}.jsonl"
  echo "[vlift] configuration=$cfg model=$model subset=$subset"
  python3 "$ROOT/scripts/vertical_lift_runner.py" \
    --set "$subset" \
    --model "$model" \
    --configuration "$cfg" \
    --system-prompt-file "$prompt" \
    --provider openai \
    --endpoint "$ENDPOINT" \
    "${KEY_ARGS[@]}" \
    --temperature "$TEMPERATURE" \
    --max-tokens "$MAX_TOKENS" \
    --out "$out"
}

make_canary_set() {
  local src="$1" dst="$2" scenario_id="$3"
  python3 - <<PY
import json
from pathlib import Path
rows=[json.loads(l) for l in Path("$src").read_text(encoding="utf-8").splitlines() if l.strip()]
row=next(r for r in rows if r["scenario_id"]=="$scenario_id")
Path("$dst").write_text(json.dumps(row, ensure_ascii=False)+"\n", encoding="utf-8")
print("canary", row["scenario_id"], "turns", len(row["turns"]))
PY
}

integrity_check() {
  local file="$1"
  python3 - <<PY
import json, sys
from pathlib import Path
rows=[json.loads(l) for l in Path("$file").read_text(encoding="utf-8").splitlines() if l.strip()]
assert rows, "empty response file"
bad=[]
for row in rows:
    if row.get("infra_error"):
        bad.append((row["scenario_id"], "infra", row["infra_error"]))
    for turn in row["transcript"]:
        text=(turn.get("assistant_response") or "").strip()
        if not text:
            bad.append((row["scenario_id"], turn["turn_id"], "empty"))
        if turn.get("finish_reason") not in (None, "stop", "length"):
            bad.append((row["scenario_id"], turn["turn_id"], turn.get("finish_reason")))
        # crude thinking-leak / template markers
        for marker in ("</think>", "<|im_start|>", "INTERNAL PRODUCT STATE"):
            if marker in text:
                bad.append((row["scenario_id"], turn["turn_id"], f"leak:{marker}"))
        if row["controller_enabled"] and "INTERNAL PRODUCT STATE" in text:
            bad.append((row["scenario_id"], turn["turn_id"], "state_leak_in_assistant"))
if bad:
    print("INTEGRITY_FAIL", bad[:10])
    sys.exit(2)
print("INTEGRITY_OK", Path("$file").name, "n", len(rows))
PY
}

MINIMAL="$ROOT/vertical_lift/companion/minimal_role_v0.4.md"
POLICY="$ROOT/prompts/companion_reference_policy_v0.2.md"
REBT="$ROOT/vertical_lift/companion/soulchat_official_rebt_v0.4.md"
POLICY_REBT="$ROOT/vertical_lift/companion/companion_policy_plus_rebt_role_v0.4.md"
GENERAL_MODEL="${VLIFT_GENERAL_MODEL:-qwen2-7b-instruct}"
VERTICAL_MODEL="${VLIFT_VERTICAL_MODEL:-soulchat2-qwen2-7b}"

case "$PHASE" in
  canary)
    CANARY="$OUT_DIR/canary_one.jsonl"
    make_canary_set "$SET_PATH" "$CANARY" "VL-CMP-001"
    run_one A "$GENERAL_MODEL" "$MINIMAL" "$CANARY"
    integrity_check "$OUT_DIR/resp_A.jsonl"
    echo "[vlift] Stop general vLLM, start vertical, then rerun: $0 canary-vertical"
    ;;
  canary-vertical)
    CANARY="$OUT_DIR/canary_one.jsonl"
    [[ -f "$CANARY" ]] || make_canary_set "$SET_PATH" "$CANARY" "VL-CMP-001"
    run_one C "$VERTICAL_MODEL" "$MINIMAL" "$CANARY"
    integrity_check "$OUT_DIR/resp_C.jsonl"
    ;;
  general)
    for cfg in A B E; do
      prompt="$MINIMAL"; [[ "$cfg" != A ]] && prompt="$POLICY"
      run_one "$cfg" "$GENERAL_MODEL" "$prompt" "$SET_PATH"
      integrity_check "$OUT_DIR/resp_${cfg}.jsonl"
    done
    ;;
  vertical)
    for cfg in C D F; do
      prompt="$MINIMAL"; [[ "$cfg" != C ]] && prompt="$POLICY"
      run_one "$cfg" "$VERTICAL_MODEL" "$prompt" "$SET_PATH"
      integrity_check "$OUT_DIR/resp_${cfg}.jsonl"
    done
    ;;
  sensitivity)
    run_one Cp "$VERTICAL_MODEL" "$REBT" "$SET_PATH"
    integrity_check "$OUT_DIR/resp_Cp.jsonl"
    run_one Dp "$VERTICAL_MODEL" "$POLICY_REBT" "$SET_PATH"
    integrity_check "$OUT_DIR/resp_Dp.jsonl"
    ;;
  *)
    echo "usage: $0 {canary|canary-vertical|general|vertical|sensitivity}"
    exit 1
    ;;
esac
