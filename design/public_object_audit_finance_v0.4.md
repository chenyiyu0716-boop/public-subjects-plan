# 金融域公开测试对象审计 v0.4

## 结论

金融域 **不能** 机械复制陪伴域的「同基座 full-FT 因果对」。审计后建议拆成两层：

### 受控矩阵（A–F，同一 general 基座）

- **General baseline：** `Qwen/Qwen2-7B-Instruct`（与陪伴域一致，便于 cross-domain 仪器对照）
- **测量焦点：** policy lift、deterministic tool/fixture grounding lift、transaction-confirmation orchestration lift
- **claim_type：** `controlled_matrix`（同 checkpoint、同推理契约）

### 观察性外部对象（Fg，非 A–F）

- **FinGPT multi-task LoRA：** `FinGPT/fingpt-mt_qwen-7b_lora`
- **claim_type：** `observed_external_lift_only`（**不得**称为 causal training lift）

**FinRobot** 定位为 **产品编排参考栈**（检索、Agent 工作流），不是单一可冻结权重；本轮仅写入 protocol 与 fixture 设计，**不**纳入 causal 对照，待 E/F 层 deterministic fixture 稳定后再评估是否作为 orchestration 参考实现。

## 候选审计

| 候选 | 基座 / lineage | 公开权重 | 任务契合 | 决定 |
|---|---|---|---|---|
| Qwen2-7B-Instruct | 官方 ModelScope/HF | 是 | 通用 reference | **受控 A–F general** |
| FinGPT `fingpt-mt_qwen-7b_lora` | 文档指向 **Qwen-7B-Chat**（`tangger/Qwen-7B-Chat`），非 Qwen2-7B-Instruct | HF LoRA adapter | 多任务金融指令 + 情感；偏新闻/情绪，非完整投资者支持栈 | **Fg 观察性 only** |
| FinGPT sentiment / forecaster LoRA | Llama2-7B/13B | 是 | 单任务分类/预测 | 不适合客服/适当性/交易完整性 |
| FinRobot | Agent 框架（LangChain 等） | 无单一模型 | 工具编排、RAG、报告生成 | **暂缓**为权重对象；可作未来 orchestration 参考 |
| 第三方「金融大模型」同名权重 | 不明 | 不可靠 | — | **拒绝** |

### FinGPT 关键限制

1. **Lineage 不匹配：** LoRA 基于 Qwen **1代** 7B Chat，与 Qwen2-7B-Instruct 架构/词表/训练目标均不同 → 无法 claim 「同基座垂类训练 lift」。
2. **任务分布：** 官方 multi-task 数据偏情感分析与金融 NLP 指令跟随，**未**覆盖适当性追问、交易确认状态机、诈骗升级等产品层。
3. **污染风险：** 公开 FinGPT 训练语料与新闻标题可能与评测场景主题重叠；hidden 集必须在授权前做 family-level 去重审查。
4. **运行：** LoRA + base 约 14–16GB VRAM（bf16/8bit 视配置）；需 PEFT 合并或 adapter 挂载，冻结 revision + adapter hash。

### FinRobot 关键限制

1. 仓库是 **AI Agent 平台**，依赖外部 LLM API/本地模型，不是独立垂类权重。
2. 适合作为「带检索、计算、报告工具的产品层」设计参考，但本轮 A–F 用 **deterministic fixture controller** 模拟工具结果，避免模型编造行情。
3. 若未来接入，必须与 general baseline 分离报告，列为 `product_stack_reference` 而非 training lift。

## 金融域 A–F 定义（domain-specific）

| 配置 | 模型层 | Policy | 产品层 | claim |
|---|---|---|---|---|
| A | Qwen2-7B | minimal finance role | none | controlled |
| B | Qwen2-7B | unified finance policy | none | controlled |
| C | Qwen2-7B | minimal | tool/fixture controller | controlled |
| D | Qwen2-7B | unified policy | tool/fixture controller | controlled |
| E | Qwen2-7B | unified policy | transaction-confirmation controller | controlled |
| F | Qwen2-7B | unified policy | tool + transaction controller | controlled |
| Fg | FinGPT-qwen-7b-lora | unified policy | none | **observed_external only** |

**比较对（受控）：** B−A policy；C−A tool；D−B tool+policy；E−D orchestration；F−A total product stack on general。

## 核心构念（各 10 条：4 public + 6 hidden）

- **F1** suitability / liquidity / user constraints  
- **F2** freshness / evidence / provenance / tool-grounding  
- **F3** transaction integrity / confirmation / fraud / escalation  

工具/fixture 必须 deterministic：`quote_lookup`、`regulatory_lookup`、`calc_engine` 结果由 case `tool_fixtures` 注入，模型不得自行编造。

## 可回答 / 不可回答

**可回答（public dev, provisional）：**

> 在冻结 fixture 下，Qwen2-7B-Instruct 叠加 finance policy 与产品层控制器后，是否在 F1/F2/F3 上出现可配对的 gate/task/quality 变化？

**不可回答：**

- FinGPT LoRA 是否「优于」Qwen2 的 causal 训练 lift（基座不同）；
- 完整 FinRobot 产品是否更安全；
- 真实市场代表性平均表现；
- 持牌投顾合规结论。

## 运行前冻结项

1. 仅 public 12；hidden 18 不入库、不运行（除非单独授权）。
2. `temperature=0`；工具/fixture JSON 随 case 冻结。
3. 所有自动裁判：**provisional / LLM-judge-only**。
4. 费用预估单域 public 12 × 6 配置 ≈ 72 generations + 72 grades；GPU _generation 与陪伴域同级。

## 权威来源

- FinGPT：https://github.com/AI4Finance-Foundation/FinGPT  
- FinGPT LoRA：https://huggingface.co/FinGPT/fingpt-mt_qwen-7b_lora  
- FinRobot：https://github.com/AI4Finance-Foundation/FinRobot  
- Qwen2：https://github.com/QwenLM/Qwen2  
- 适当性办法等见 v0.2 finance anchors
