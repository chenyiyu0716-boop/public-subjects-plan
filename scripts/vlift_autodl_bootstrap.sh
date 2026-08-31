#!/usr/bin/env bash
# Bootstrap official Qwen2 / SoulChat2.0 weights + vLLM on a 24GB cloud GPU.
# Run ON the cloud instance. Do not download these weights to the local Mac.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORKDIR="${VLIFT_WORKDIR:-$HOME/vlift-run}"
MODELS_DIR="$WORKDIR/models"
LOG_DIR="$WORKDIR/logs"
VLLM_VERSION="${VLLM_VERSION:-0.6.6}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-8192}"
PORT="${VLIFT_PORT:-8000}"
API_KEY="${VLIFT_API_KEY:-vlift-local}"

mkdir -p "$MODELS_DIR" "$LOG_DIR"
cd "$WORKDIR"

echo "[vlift] workdir=$WORKDIR"
echo "[vlift] recording environment"
{
  date -u +"%Y-%m-%dT%H:%M:%SZ"
  nvidia-smi || true
  python3 -V
  pip3 -V
} | tee "$LOG_DIR/env_boot.txt"

python3 -m pip install -U pip
python3 -m pip install "vllm==${VLLM_VERSION}" modelscope

python3 - <<'PY' | tee "$LOG_DIR/package_versions.json"
import json, importlib.metadata as md
pkgs = ["vllm", "torch", "transformers", "modelscope"]
out = {}
for name in pkgs:
    try:
        out[name] = md.version(name)
    except md.PackageNotFoundError:
        out[name] = None
print(json.dumps(out, indent=2))
PY

download_and_verify() {
  local model_id="$1"
  local target="$2"
  mkdir -p "$target"
  echo "[vlift] downloading $model_id -> $target"
  modelscope download --model "$model_id" --local_dir "$target"
  python3 "$ROOT/scripts/vlift_verify_weights.py" \
    --expected "$ROOT/vertical_lift/expected_weight_hashes_v0.4.json" \
    --model-id "$model_id" \
    --model-dir "$target" | tee "$LOG_DIR/hash_$(echo "$model_id" | tr '/' '_').json"
}

download_and_verify "Qwen/Qwen2-7B-Instruct" "$MODELS_DIR/Qwen2-7B-Instruct"
download_and_verify "YIRONGCHEN/SoulChat2.0-Qwen2-7B" "$MODELS_DIR/SoulChat2.0-Qwen2-7B"

# Capture chat templates for freeze record
python3 - <<PY
import json
from pathlib import Path
out = {}
for name, path in {
    "Qwen2-7B-Instruct": Path("$MODELS_DIR/Qwen2-7B-Instruct/tokenizer_config.json"),
    "SoulChat2.0-Qwen2-7B": Path("$MODELS_DIR/SoulChat2.0-Qwen2-7B/tokenizer_config.json"),
}.items():
    cfg = json.loads(path.read_text(encoding="utf-8"))
    out[name] = {
        "chat_template": cfg.get("chat_template"),
        "model_max_length": cfg.get("model_max_length"),
        "tokenizer_class": cfg.get("tokenizer_class"),
    }
Path("$LOG_DIR/chat_templates.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("wrote chat_templates.json")
PY

cat > "$WORKDIR/serve_model.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
MODEL_DIR="\$1"
SERVED_NAME="\$2"
exec python3 -m vllm.entrypoints.openai.api_server \\
  --model "\$MODEL_DIR" \\
  --served-model-name "\$SERVED_NAME" \\
  --dtype auto \\
  --max-model-len ${MAX_MODEL_LEN} \\
  --gpu-memory-utilization 0.90 \\
  --port ${PORT} \\
  --api-key ${API_KEY}
EOF
chmod +x "$WORKDIR/serve_model.sh"

cat <<EOF
[vlift] bootstrap complete.

Serve general model:
  $WORKDIR/serve_model.sh $MODELS_DIR/Qwen2-7B-Instruct qwen2-7b-instruct

Serve vertical model (stop general first on 24GB):
  $WORKDIR/serve_model.sh $MODELS_DIR/SoulChat2.0-Qwen2-7B soulchat2-qwen2-7b

Endpoint:
  http://127.0.0.1:${PORT}/v1
  API key env: VLIFT_API_KEY=${API_KEY}
EOF
