# Finance Fg infra_blocked provenance v0.4

**状态：** `infra_blocked` / `not_scored` / **no training-lift claim**  
**claim_type（记录字段）：** `observed_external_lift_only`  
**日期：** 2026-08-31  
**不重跑、不换第三方权重。**

---

## 对象身份（审计确认）

| 项 | 值 |
|----|-----|
| Adapter | `FinGPT/fingpt-mt_qwen-7b_lora`（官方 HF/AI4Finance；本机经 hf-mirror 下载） |
| adapter_config.base_model_name_or_path | `base_models/Qwen-7B`（**Base**，非 Chat） |
| target_modules | `["c_attn"]` |
| lora_r / alpha | 8 / 32 |
| 审计文档声明基座 | Qwen-7B-Chat（文档 lineage；与 adapter_config 字符串不完全一致） |
| 实际加载基座（失败路径） | ModelScope `Qwen/Qwen-7B-Chat` |

---

## 运行环境

| 项 | 值 |
|----|-----|
| 云 GPU | AutoDL RTX 4090D 24GB（按量；已关机） |
| 受控 A–F 推理 | vLLM 0.6.6 + transformers 4.45.2 |
| Fg 尝试路径 | transformers + peft（`peft==0.13.2`）本地 chat/generate；vLLM 因 Qwen-7B tokenizer/`QWenTokenizer` 与不完整 merge 无法 serve |
| 工作目录 | 云端数据盘（结果已脱敏入库；不保留主机名/SSH） |

---

## 失败阶段与错误类别

| 阶段 | 结果 | 错误类别 |
|------|------|----------|
| 下载 LoRA | 成功（约 8.1MB，`adapter_config.json` + `adapter_model.bin`） | — |
| 基座 Chat 单独推理 | **成功**（`model.chat` 可正常中文回复） | — |
| Peft 挂载 LoRA 后 chat/generate | **失败**：只生成 `<\|im_end\|>`（token 151645）重复；有效文本长度 0 | **adapter_base_mismatch / generation_collapse** |
| merge_and_unload 存盘 | **失败**：磁盘满（`No space left on device`） | **disk_full**（腾盘后未再强行下 Qwen-7B Base） |
| vLLM serve merged | **失败**：目录不完整 / tokenizer 类不兼容 | **serving_incompatible** |

---

## 有效回复与盲评

- **有效助手回复数：** 0/12（`resp_Fg.jsonl` 全部 `infra_error`，`assistant_response` 为空）。  
- **未进入盲评：** 无有效 transcript 可供语义评分；保持 `not_scored`。  
- **未使用第三方替代权重：** 授权要求仅官方 adapter；停机条件含“接口不兼容 / 需第三方权重则停止”。未改用非审计金融 LoRA 或量化包。

---

## 为何不构成金融 training lift

1. 无 Qwen2-7B-Instruct 同基座金融 full-FT 对照。  
2. Fg 计划仅为 **observed external** 敏感性臂，即使跑通也不得写入 causal training lift。  
3. 本轮 **infra_blocked**，连观察性点估计都不可用。

---

## 记录位置

- 响应：`vertical_lift/results/public_v0.4_finance/responses/resp_Fg.jsonl`  
- 生成摘要：`reports/v0.4_fc_generation_summary.md`  
- 暂定报告：`reports/vertical_lift_v0.4_finance_community_provisional.md`
