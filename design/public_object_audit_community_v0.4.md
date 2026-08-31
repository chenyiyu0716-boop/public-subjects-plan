# 社区域公开测试对象审计 v0.4

## 结论

社区域测量对象是 **moderation system**，不是聊天助手。分三层：

### 受控矩阵（A–F，统一 moderation contract）

- **General baseline：** `Qwen/Qwen2-7B-Instruct` + moderation policy prompt → 自然语言或 JSON contract
- **产品层：** deterministic workflow controller（policy version、prior strikes、appeal status、thread context）
- **claim_type：** `controlled_matrix`

### 观察性专用 guard（Gg，非 A–F）

- **Qwen3Guard-Gen-0.6B**（或 4B，视 VRAM；优先 0.6B 降本）
- **claim_type：** `observed_specialized_guard_only`
- 输出映射到统一 **moderation contract v1** 后再比较；**不得**与 chat 自由回复分数直接比

**Qwen3Guard-Stream** 本轮不纳入 A–F：token-stream 接口与 batch eval 契约不同，留作 streaming 扩展。

## 候选审计

| 候选 | 类型 | 中文 | 可运行 | 决定 |
|---|---|---|---|---|
| Qwen2-7B-Instruct + policy | 生成式 chat | 是 | vLLM | **A–F general** |
| Qwen3Guard-Gen-0.6B/4B/8B | 生成式 guard（Safety/Category/Refusal 结构输出） | 是 | HF + trust_remote_code | **Gg 观察性** |
| Qwen3Guard-Stream | Token 级流式分类 | 是 | 不同 API | **暂缓** |
| 通用 chat 模型 NL 审核 | — | — | 已含于 A–B | 受控 |
| 第三方 moderation API | 闭源 | 不一 | — | **不采用**（不可冻结） |

### Qwen3Guard 关键事实

1. **Lineage：** 基于 Qwen3，与 Qwen2-7B-Instruct **不同基座** → 非 causal training lift，而是 specialized guard 观察轨。
2. **输出：** Gen 变体生成 `Safety: Safe|Controversial|Unsafe`、类别、Refusal 等；需 **adapter** 映射到本仓 contract：
   - `disposition`: allow | restrict | remove | escalate  
   - `confidence`: high | medium | low  
   - `policy_categories`: string[]  
   - `evidence_spans`: string[]  
   - `appeal_eligible`: boolean  
   - `reason`: string  
3. **License：** Apache 2.0（技术报告与 HF 卡）。
4. **成本：** 0.6B 可在 24GB GPU 与 general 7B 分时加载；同机双模型需序列化 serve 或两次 bootstrap。

### 与 v0.3 community pilot 的关系

v0.3 用 **同一 chat policy** 让通用模型输出「结论/理由/置信度」三段式。v0.4 保留该语义，但：

- 强制 **moderation contract v1**（JSON）便于 grader 与跨模型对齐；
- 增加 workflow state（申诉、strike、policy version）；
- 不再把 NL 长度/风格当主要质量轴。

## 社区域 A–F 定义

| 配置 | 模型层 | Policy | 产品层 | claim |
|---|---|---|---|---|
| A | Qwen2-7B | minimal moderation role | none | controlled |
| B | Qwen2-7B | community_reference_policy v0.2 | none | controlled |
| C | Qwen2-7B | minimal | context/workflow fixture controller | controlled |
| D | Qwen2-7B | unified policy | context/workflow fixture controller | controlled |
| E | Qwen2-7B | unified policy | appeal/escalation controller | controlled |
| F | Qwen2-7B | unified policy | full workflow controller | controlled |
| Gg | Qwen3Guard-Gen-0.6B | guard native template + contract mapper | none | **observed_specialized only** |

## 核心构念（各 10 条）

- **C1** contextual policy judgment  
- **C2** enforcement proportionality / false positive control  
- **C3** workflow integrity / appeal / adversarial resistance  

## 可回答 / 不可回答

**可回答：**

> prompt-only general moderation vs 带 workflow fixture 的产品栈，是否在 C1/C2/C3 上产生可配对变化？Qwen3Guard 映射到同一 contract 后，与 general policy 的差异方向如何（观察性）？

**不可回答：**

- 平台真实误杀/漏判率；
- Qwen3Guard 相对 Qwen2 的 causal 训练 lift；
- 任何公司内容审核产品排名。

## 运行前冻结项

1. 统一 moderation contract schema 冻结后再跑 public 12。  
2. hidden 18 不运行。  
3. LLM judge 盲于配置名；结果 **provisional**。  
4. Gg 运行需额外 ~2GB VRAM 时段或独立 canary。

## 权威来源

- Qwen3Guard：https://github.com/QwenLM/Qwen3Guard  
- Qwen3Guard-Gen-0.6B：https://huggingface.co/Qwen/Qwen3Guard-Gen-0.6B  
- 技术报告：https://arxiv.org/html/2510.14276v1  
- v0.2 community anchors & policy
