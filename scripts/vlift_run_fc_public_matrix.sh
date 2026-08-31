#!/usr/bin/env bash
# Run finance + community public-12 (A-F + Fg/Gg). PUBLIC SET ONLY.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENDPOINT="${VLIFT_ENDPOINT:-http://127.0.0.1:8000/v1}"
API_KEY_ENV="${VLIFT_API_KEY_ENV:-VLIFT_API_KEY}"
TEMPERATURE=0
MAX_TOKENS=800
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/tmp/vlift-pyc}"

if [[ -n "${!API_KEY_ENV:-}" ]]; then
  KEY_ARGS=(--api-key-env "$API_KEY_ENV")
else
  KEY_ARGS=(--allow-empty-api-key)
fi

FIN_OUT="${VLIFT_FIN_OUT:-$ROOT/vertical_lift/results/public_v0.4_finance/responses}"
COM_OUT="${VLIFT_COM_OUT:-$ROOT/vertical_lift/results/public_v0.4_community/responses}"
mkdir -p "$FIN_OUT" "$COM_OUT"

FIN_SET="$ROOT/vertical_lift/finance/dev_v0.4.jsonl"
COM_SET="$ROOT/vertical_lift/community/dev_v0.4.jsonl"
FIN_MIN="$ROOT/vertical_lift/finance/minimal_role_v0.4.md"
FIN_POL="$ROOT/prompts/finance_reference_policy_v0.2.md"
COM_MIN="$ROOT/vertical_lift/community/minimal_role_v0.4.md"
COM_POL="$ROOT/prompts/community_reference_policy_v0.2.md"

run_one() {
  local domain="$1" cfg="$2" model="$3" prompt="$4" out="$5" extra=("${@:6}")
  echo "[vlift-fc] domain=$domain cfg=$cfg model=$model"
  python3 "$ROOT/scripts/vertical_lift_runner.py" \
    --set "$([[ $domain == finance ]] && echo "$FIN_SET" || echo "$COM_SET")" \
    --model "$model" \
    --configuration "$cfg" \
    --system-prompt-file "$prompt" \
    --provider openai \
    --endpoint "$ENDPOINT" \
    "${KEY_ARGS[@]}" \
    --temperature "$TEMPERATURE" \
    --max-tokens "$MAX_TOKENS" \
    "${extra[@]}" \
    --out "$out"
}

integrity_check() {
  local file="$1" mode="${2:-chat}"
  python3 - <<PY
import json, sys
from pathlib import Path
mode = "$mode"
rows=[json.loads(l) for l in Path("$file").read_text(encoding="utf-8").splitlines() if l.strip()]
bad=[]
for row in rows:
    if row.get("infra_error"):
        bad.append((row["scenario_id"], "infra", row["infra_error"]))
    ct = row.get("claim_type","")
    if row["configuration"] in ("Fg","Gg") and ct not in (
        "observed_external_lift_only","observed_specialized_guard_only"):
        bad.append((row["scenario_id"], "claim_type", ct))
    for turn in row["transcript"]:
        text=(turn.get("assistant_response") or "").strip()
        if not text:
            bad.append((row["scenario_id"], turn["turn_id"], "empty"))
        if "INTERNAL PRODUCT STATE" in text or "AUTHORITATIVE TOOL FIXTURES" in text:
            bad.append((row["scenario_id"], turn["turn_id"], "state_leak"))
        if mode == "moderation_v1":
            try:
                obj=json.loads(text)
                for k in ("disposition","confidence","reason"):
                    if k not in obj:
                        bad.append((row["scenario_id"], turn["turn_id"], f"missing_{k}"))
            except json.JSONDecodeError:
                bad.append((row["scenario_id"], turn["turn_id"], "invalid_moderation_json"))
if bad:
    print("INTEGRITY_FAIL", bad[:12]); sys.exit(2)
print("INTEGRITY_OK", Path("$file").name, "n", len(rows))
PY
}

PHASE="${1:-all}"

run_finance_qwen2() {
  for cfg in A B C D E F; do
    local prompt="$FIN_MIN"
    [[ "$cfg" != "A" && "$cfg" != "C" ]] && prompt="$FIN_POL"
    run_one finance "$cfg" "qwen2-7b-instruct" "$prompt" "$FIN_OUT/resp_${cfg}.jsonl"
    integrity_check "$FIN_OUT/resp_${cfg}.jsonl" chat
  done
}

run_finance_fg() {
  run_one finance Fg "fingpt-mt-qwen7b" "$FIN_POL" "$FIN_OUT/resp_Fg.jsonl"
  integrity_check "$FIN_OUT/resp_Fg.jsonl" chat
}

run_community_qwen2() {
  for cfg in A B C D E F; do
    local prompt="$COM_MIN"
    [[ "$cfg" != "A" && "$cfg" != "C" ]] && prompt="$COM_POL"
    run_one community "$cfg" "qwen2-7b-instruct" "$prompt" "$COM_OUT/resp_${cfg}.jsonl" \
      --response-mode moderation_v1 --max-tokens 512
    integrity_check "$COM_OUT/resp_${cfg}.jsonl" moderation_v1
  done
}

run_community_gg() {
  run_one community Gg "qwen3guard-gen-0.6b" "$COM_POL" "$COM_OUT/resp_Gg.jsonl" \
    --response-mode moderation_v1 --max-tokens 512
  integrity_check "$COM_OUT/resp_Gg.jsonl" moderation_v1
}

case "$PHASE" in
  finance-qwen2) run_finance_qwen2 ;;
  finance-fg) run_finance_fg ;;
  community-qwen2) run_community_qwen2 ;;
  community-gg) run_community_gg ;;
  all)
    run_finance_qwen2
    run_finance_fg
    run_community_qwen2
    run_community_gg
    ;;
  *)
    echo "usage: $0 {finance-qwen2|finance-fg|community-qwen2|community-gg|all}"
    exit 1
    ;;
esac

echo "[vlift-fc] phase=$PHASE complete"
