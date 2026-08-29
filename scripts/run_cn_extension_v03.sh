#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
cd ..

: "${DASHSCOPE_API_KEY:?请先设置 DASHSCOPE_API_KEY；不要把 key 写入仓库}"

new_subjects=(glm_5_2_bailian kimi_k2_5_bailian minimax_m2_5_bailian)
all_subjects=(qwen_local_1_5b qwen_local_7b deepseek_v4_flash stepfun_3_5_flash glm_5_2_bailian kimi_k2_5_bailian minimax_m2_5_bailian)
domains=(finance companion community)
export JUDGE_MAX_OUTPUT_TOKENS=400
export JUDGE_DISABLE_THINKING=1

for domain in "${domains[@]}"; do
  case "$domain" in
    finance)
      setfile="audited_sets/finance_pilot_v0.2.jsonl"
      prompt="prompts/finance_reference_policy_v0.2.md"
      ;;
    companion)
      setfile="audited_sets/companion_pilot_v0.2.jsonl"
      prompt="prompts/companion_reference_policy_v0.2.md"
      ;;
    community)
      setfile="audited_sets/community_pilot_v0.2.jsonl"
      prompt="prompts/community_reference_policy_v0.2.md"
      ;;
  esac

  mkdir -p "responses/$domain" "baselines/$domain"
  for subject in "${new_subjects[@]}"; do
    response_file="responses/$domain/$subject.jsonl"
    if [[ ! -s "$response_file" ]]; then
      python3 scripts/subjects.py \
        --set "$setfile" \
        --subject "$subject" \
        --out "$response_file" \
        --system-prompt-file "$prompt" \
        --temperature 0 \
        --max-output-tokens 512
    else
      echo "复用已有回复 $response_file"
    fi
  done
  python3 scripts/check_response_integrity.py \
    "responses/$domain/glm_5_2_bailian.jsonl" \
    "responses/$domain/kimi_k2_5_bailian.jsonl" \
    "responses/$domain/minimax_m2_5_bailian.jsonl"

  baseline_files=()
  for subject in "${all_subjects[@]}"; do
    response_file="responses/$domain/$subject.jsonl"
    baseline_file="baselines/$domain/$subject.json"
    if [[ ! -s "$baseline_file" ]]; then
      python3 scripts/eval_harness.py \
        --set "$setfile" \
        --responses "$response_file" \
        --out "$baseline_file" \
        --judge-endpoint "https://dashscope.aliyuncs.com/compatible-mode/v1" \
        --judge-key "$DASHSCOPE_API_KEY" \
        --judge-model-name "qwen3.8-max"
    else
      echo "复用已有裁判结果 $baseline_file"
    fi
    python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d.get("valid", 0) > 0, f"裁判零有效结果：{sys.argv[1]}"' "$baseline_file"
    baseline_files+=("$baseline_file")
  done

  python3 scripts/eval_harness.py \
    --compare "${baseline_files[@]}" \
    --out "baselines/$domain/compare.json"
done
