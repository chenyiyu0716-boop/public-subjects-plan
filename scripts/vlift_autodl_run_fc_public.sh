#!/usr/bin/env bash
# Full finance+community public generation on cloud (sequential model serve).
# Run after vlift_autodl_bootstrap_fc_v0.4.sh. Stops vLLM between model swaps.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="${VLIFT_REPO_ROOT:-$ROOT}"
WORKDIR="${VLIFT_WORKDIR:-/root/autodl-tmp/vlift-run}"
PORT="${VLIFT_PORT:-8000}"
export VLIFT_API_KEY="${VLIFT_API_KEY:-vlift-local}"
export VLIFT_API_KEY_ENV=VLIFT_API_KEY
LOG="$WORKDIR/logs/fc_public_run.log"
START_TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

exec > >(tee -a "$LOG") 2>&1
echo "[vlift-fc-orchestrator] start=$START_TS"

serve_and_run() {
  local model_dir="$1" served="$2" phase="$3"
  pkill -f "vllm.entrypoints.openai.api_server" 2>/dev/null || true
  sleep 3
  echo "[vlift-fc-orchestrator] serving $served"
  nohup "$WORKDIR/serve_model.sh" "$model_dir" "$served" > "$WORKDIR/logs/serve_${served}.log" 2>&1 &
  for i in $(seq 1 90); do
    if curl -sf -H "Authorization: Bearer $VLIFT_API_KEY" "http://127.0.0.1:${PORT}/v1/models" >/dev/null; then
      break
    fi
    sleep 5
  done
  curl -sf -H "Authorization: Bearer $VLIFT_API_KEY" "http://127.0.0.1:${PORT}/v1/models" | head -c 400
  echo
  bash "$REPO_ROOT/scripts/vlift_run_fc_public_matrix.sh" "$phase"
}

cd "$REPO_ROOT"
git rev-parse HEAD | tee "$WORKDIR/logs/git_head_fc.txt"

serve_and_run "$WORKDIR/models/Qwen2-7B-Instruct" "qwen2-7b-instruct" "finance-qwen2"
serve_and_run "$WORKDIR/models/Qwen2-7B-Instruct" "qwen2-7b-instruct" "community-qwen2"
serve_and_run "$WORKDIR/models/FinGPT-mt-qwen7b-merged" "fingpt-mt-qwen7b" "finance-fg"
serve_and_run "$WORKDIR/models/Qwen3Guard-Gen-0.6B" "qwen3guard-gen-0.6b" "community-gg"

pkill -f "vllm.entrypoints.openai.api_server" 2>/dev/null || true
echo "[vlift-fc-orchestrator] shutdown vllm $(date -u +%Y-%m-%dT%H:%M:%SZ)"

REPO_ROOT="$REPO_ROOT" WORKDIR="$WORKDIR" python3 - <<'PY'
import json
import os
from datetime import datetime, timezone
from pathlib import Path

root = Path(os.environ["REPO_ROOT"])
work = Path(os.environ["WORKDIR"])
manifest = {
    "schema_version": "vertical-lift-run-freeze-v0.4-fc",
    "status": "public_dev_generation_only_no_judge",
    "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    "domains": ["finance", "community"],
    "configs": {
        "finance": ["A","B","C","D","E","F","Fg"],
        "community": ["A","B","C","D","E","F","Gg"],
    },
    "observed_external": {
        "Fg": "FinGPT/fingpt-mt_qwen-7b_lora merged on Qwen/Qwen-7B-Chat",
        "Gg": "Qwen/Qwen3Guard-Gen-0.6B",
    },
    "git_head": (work / "logs/git_head_fc.txt").read_text().strip(),
    "logs": str(work / "logs"),
}
out = root / "vertical_lift/results/public_v0.4_finance/run_freeze_manifest_v0.4.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(root / "vertical_lift/results/public_v0.4_community/run_freeze_manifest_v0.4.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("wrote freeze manifests")
PY

tar czf "$WORKDIR/vlift_fc_public_responses_v0.4.tgz" \
  -C "$REPO_ROOT/vertical_lift/results" \
  public_v0.4_finance/responses public_v0.4_community/responses \
  public_v0.4_finance/run_freeze_manifest_v0.4.json \
  public_v0.4_community/run_freeze_manifest_v0.4.json 2>/dev/null || \
tar czf "$WORKDIR/vlift_fc_public_responses_v0.4.tgz" \
  -C "$REPO_ROOT/vertical_lift/results" public_v0.4_finance public_v0.4_community

ls -lh "$WORKDIR/vlift_fc_public_responses_v0.4.tgz"
echo "[vlift-fc-orchestrator] DONE pack=$WORKDIR/vlift_fc_public_responses_v0.4.tgz"
