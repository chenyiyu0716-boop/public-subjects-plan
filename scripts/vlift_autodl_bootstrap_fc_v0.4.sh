#!/usr/bin/env bash
# Bootstrap Qwen2-7B + FinGPT LoRA merge + Qwen3Guard-Gen-0.6B on 24GB cloud GPU.
# Run ON the cloud instance only. PUBLIC artifacts — no hidden set.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORKDIR="${VLIFT_WORKDIR:-/root/autodl-tmp/vlift-run}"
MODELS_DIR="$WORKDIR/models"
LOG_DIR="$WORKDIR/logs"
VLLM_VERSION="${VLLM_VERSION:-0.6.6}"
TRANSFORMERS_VERSION="${TRANSFORMERS_VERSION:-4.45.2}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-8192}"
PORT="${VLIFT_PORT:-8000}"
API_KEY="${VLIFT_API_KEY:-vlift-local}"

mkdir -p "$MODELS_DIR" "$LOG_DIR"
cd "$WORKDIR"

echo "[vlift-fc] workdir=$WORKDIR"
{
  date -u +"%Y-%m-%dT%H:%M:%SZ"
  nvidia-smi || true
  python3 -V
} | tee "$LOG_DIR/env_boot_fc.txt"

python3 -m pip install -U pip
python3 -m pip install "vllm==${VLLM_VERSION}" "transformers==${TRANSFORMERS_VERSION}" modelscope peft accelerate huggingface_hub

download_qwen2() {
  modelscope download --model "Qwen/Qwen2-7B-Instruct" --local_dir "$MODELS_DIR/Qwen2-7B-Instruct"
  python3 "$ROOT/scripts/vlift_verify_weights.py" \
    --expected "$ROOT/vertical_lift/expected_weight_hashes_v0.4.json" \
    --model-id "Qwen/Qwen2-7B-Instruct" \
    --model-dir "$MODELS_DIR/Qwen2-7B-Instruct" \
    | tee "$LOG_DIR/hash_Qwen2-7B-Instruct.json"
}

download_qwen7_chat() {
  modelscope download --model "Qwen/Qwen-7B-Chat" --local_dir "$MODELS_DIR/Qwen-7B-Chat"
}

merge_fingpt_lora() {
  WORKDIR="$WORKDIR" python3 - <<'PY'
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

work = Path(os.environ["WORKDIR"])
base_dir = work / "models/Qwen-7B-Chat"
adapter_id = "FinGPT/fingpt-mt_qwen-7b_lora"
out_dir = work / "models/FinGPT-mt-qwen7b-merged"
log_dir = work / "logs"
out_dir.mkdir(parents=True, exist_ok=True)

tokenizer = AutoTokenizer.from_pretrained(str(base_dir), trust_remote_code=True)
base = AutoModelForCausalLM.from_pretrained(
    str(base_dir), trust_remote_code=True, torch_dtype="auto", device_map="cpu")
model = PeftModel.from_pretrained(base, adapter_id)
merged = model.merge_and_unload()
merged.save_pretrained(out_dir)
tokenizer.save_pretrained(out_dir)

prov = {
    "merged_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    "base_model": "Qwen/Qwen-7B-Chat",
    "adapter": adapter_id,
    "claim_type": "observed_external_lift_only",
    "output_dir": str(out_dir),
}
(log_dir / "fingpt_merge_provenance.json").write_text(
    json.dumps(prov, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(prov, ensure_ascii=False, indent=2))
PY
}

download_guard() {
  modelscope download --model "Qwen/Qwen3Guard-Gen-0.6B" --local_dir "$MODELS_DIR/Qwen3Guard-Gen-0.6B"
}

echo "[vlift-fc] downloading Qwen2-7B-Instruct"
download_qwen2
echo "[vlift-fc] downloading Qwen-7B-Chat base for FinGPT LoRA"
download_qwen7_chat
echo "[vlift-fc] merging FinGPT/fingpt-mt_qwen-7b_lora (observed external Fg)"
merge_fingpt_lora | tee "$LOG_DIR/fingpt_merge.log"
echo "[vlift-fc] downloading Qwen3Guard-Gen-0.6B (observed Gg)"
download_guard

cat > "$WORKDIR/serve_model.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
MODEL_DIR="\$1"
SERVED_NAME="\$2"
TRUST=""
if [[ "\$MODEL_DIR" == *"Qwen3Guard"* ]] || [[ "\$MODEL_DIR" == *"Qwen-7B"* ]]; then
  TRUST="--trust-remote-code"
fi
exec python3 -m vllm.entrypoints.openai.api_server \\
  --model "\$MODEL_DIR" \\
  --served-model-name "\$SERVED_NAME" \\
  --dtype auto \\
  --max-model-len ${MAX_MODEL_LEN} \\
  --gpu-memory-utilization 0.90 \\
  --port ${PORT} \\
  --api-key ${API_KEY} \\
  \$TRUST
EOF
chmod +x "$WORKDIR/serve_model.sh"

cat <<EOF
[vlift-fc] bootstrap complete.

Qwen2 (finance/community A-F):
  $WORKDIR/serve_model.sh $MODELS_DIR/Qwen2-7B-Instruct qwen2-7b-instruct

FinGPT merged (Fg observed external only):
  $WORKDIR/serve_model.sh $MODELS_DIR/FinGPT-mt-qwen7b-merged fingpt-mt-qwen7b

Qwen3Guard (Gg observed specialized only):
  $WORKDIR/serve_model.sh $MODELS_DIR/Qwen3Guard-Gen-0.6B qwen3guard-gen-0.6b

Endpoint: http://127.0.0.1:${PORT}/v1  API key: ${API_KEY}
EOF
