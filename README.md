# Public Subjects Plan

面向金融、陪伴和社区三个垂直领域的公开 AI eval pilot。仓库公开评测提示、领域 system policy、reference-stack 与 Vertical Lift 实验的真实回复、逐条裁判结果和可复核脚本。

## 版本定位

| 版本 | 含义 |
|------|------|
| **v0.3**（`main` 历史 / `v0.3-pilot`） | canonical **reference-stack baseline**（七入口 × 三域 public pilot） |
| **v0.4-public-dev**（本 tag） | 三域 Vertical Lift **协议**、**public development set** 与 **provisional 自动裁判**实验记录 |
| 未来 human-calibrated | 单独发布；**不覆盖** v0.4 provisional 历史 |
| Hidden formal set | 三域均 **未运行**、不入仓 |

**本 tag 不是正式 benchmark release，不是产品安全排名。**

当前项目最准确定位：

> 一个公开、可复核的三域 Vertical Lift 测量协议、public development set 与 provisional 自动裁判实验记录；不是专家验证过的正式 benchmark，也不是产品安全排名。

## v0.4 三域 public-dev 状态总表

全部结果均为 **`public dev` / `provisional` / `LLM-judge-only`**；非正式 benchmark；非产品安全结论。人标校准为开放合作项，非发布前置。

| 域 | public 配置 | 有效评分 | 可报告的 lift 类型 | 主要观察 | 明确限制 |
|----|-------------|----------|-------------------|----------|----------|
| **陪伴** | A–F + Cp/Dp | **96/96** | controlled **training / policy / orchestration** 配对比较 | 全部 bootstrap CI **跨 0**；仅可报告方向性点估计 | REBT **Cp/Dp** 为部署敏感性，**不属于** causal training lift；hidden 未跑 |
| **金融** | A–F（Fg blocked） | **72/72**（Fg 未评） | 同基座 Qwen2-7B 上的 **policy / tool fixture / transaction orchestration / total stack** | 全部 bootstrap CI **跨 0** → **当前 public-dev 切片未检测到可分离 lift**（≠“没有 lift”） | **无**金融同基座 full-FT；**Fg=`infra_blocked`**，无训练层垂类对照；**不得**暗示已测到 causal training lift |
| **社区** | A–F + Gg | **84/84** | 通用模型 + policy/workflow 的 **受控 moderation** 比较；Gg 仅观察 | 测量对象是 **moderation system**（非聊天）；仅 **A→B quality** CI `[0.08, 0.67]` 未跨 0（n=12 多重探索，**不作正式显著性 claim**）；其余未检测到可分离 lift | **Gg=`observed_specialized_guard_only`**，非 causal；勿将 Gg 67% 安全门直接解读为专用 guard“更差” |

报告入口：

- [陪伴 provisional](reports/vertical_lift_v0.4_public_provisional.md)
- [金融/社区 provisional](reports/vertical_lift_v0.4_finance_community_provisional.md)
- [Gg 只读错误分类](reports/community_gg_error_analysis_v0.4.md)
- [Fg 阻塞 provenance](reports/finance_fg_infra_blocked_v0.4.md)

产物目录：`vertical_lift/results/public_v0.4/` · `public_v0.4_finance/` · `public_v0.4_community/`

## 人工校准状态与开放合作

当前 v0.4 结果仅基于盲化的 LLM judge，尚未经过心理咨询、陪伴产品、金融合规或社区信任与安全领域专家的人工校准。因此，所有分数、Vertical Lift 点估计和置信区间均属于 **provisional / LLM-judge-only evidence**，不应解释为经过专家验证的产品安全结论或正式 benchmark 排名。

项目目前缺少稳定的领域专家评审资源。我们选择公开这一限制，而不是用非专业人工标签替代专家校准，或将自动裁判结果包装为人工共识。

我们欢迎以下背景的研究者和从业者参与协作：

- 心理咨询、临床心理或心理健康支持；
- 陪伴产品、信任与安全、危机干预；
- 金融投资者适当性、内容审核 / 社区治理；
- LLM evaluation、AI safety 或 human–AI interaction；
- 多轮对话、记忆、关系边界与用户自主性研究。

计划中的人工校准工作包括：

1. 盲审全部自动裁判判定的 hard-fail；
2. 从其余结果中按配置、构念和场景类型分层抽样；
3. 独立判断安全红线、最低任务完成、过度拒绝、回复质量和状态遵循；
4. 计算人工评审者间一致性及人工与 LLM judge 的一致性；
5. 在证据充分后发布单独的 human-calibrated 结果，不覆盖当前 provisional 历史记录。

有意协作者可通过 [GitHub Issue](https://github.com/chenyiyu0716-boop/public-subjects-plan/issues) 联系。评审材料将隐藏模型和实验配置身份；公开测试集不包含真实用户记录。隐藏集在人工校准方案确定前保持未运行、未公开状态。

## v0.3 当前结论（reference-stack baseline）

这是 **audited public pilot / reference-stack baseline v0.3**，不是正式 benchmark，也不是模型产品排名。

- 每域 14 条：7 个维度 × 2 条，共 42 条公开提示。
- 七个测试对象：Qwen2.5 1.5B、Qwen2.5 7B、DeepSeek V4 Flash、StepFun 3.5 Flash、GLM 5.2、Kimi K2.5、MiniMax M2.5。
- 所有对象使用相同的公开领域 policy，生成温度为 `0`。
- 294/294 个评分单元有效，0 个未决。
- Qwen3.8-Max 完成 291 条评分；持续未决的 3 条由 Claude Opus 4.6 通过 Anthropic Messages 独立补判，逐条 provenance 已保留。
- v0.3 与上一版 mixed-judge baseline 在 168 个可比结果上的一致率为 97.6%，Cohen's κ=0.876。

| 域 | Qwen 1.5B | Qwen 7B | DeepSeek | StepFun | GLM 5.2 | Kimi K2.5 | MiniMax M2.5 | dp |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 金融 | 5/14 | 1/14 | 0/14 | 0/14 | 0/14 | 0/14 | 0/14 | 0.357 |
| 陪伴 | 4/14 | 3/14 | 0/14 | 0/14 | 0/14 | 2/14 | 1/14 | 0.286 |
| 社区 | 4/14 | 2/14 | 0/14 | 0/14 | 0/14 | 1/14 | 0/14 | 0.286 |

表格为“失败数/有效数”。14 条样本的区间很宽：即使 0/14，失败率的 Wilson 95% 上界仍约为 0.215。因此结果适合验证弱强档区分能力，不适合精排强模型。金融对五个强 API 对象全部为 0/14，已经出现天花板。

## 测量边界

测试对象本质上是“固定模型入口 + 同一份公开 system policy”（v0.3）或“受控模型/政策/产品层矩阵”（v0.4），不是完整产品。实验没有覆盖真实交易/审核后台全链路、人工升级或提供方额外产品过滤的全部形态，不能外推为对应公司的产品安全结论。API 模型也可能被提供方原地更新，本仓结果应视为带时间戳的 endpoint snapshot。

LLM semantic `state_adherence` 与 deterministic **controller assertion** 必须分开报告：后者只证明 runner 注入的产品状态机机械正确，**不等于**模型语义能力。

## v0.4：从标准锚点到 Vertical Lift

现有 42 条题保留并冻结为 **Core / canonical cases**。它们有可靠的领域参考价值，覆盖了真实产品会遇到的高价值失效模式；但多数属于“风险明确、指令明确、期望动作明确”的标准题，只能证明模型是否理解基本规则。它们是按风险分类法等权构造的 `taxonomy-balanced set`，不是按真实业务流量采样的 `market-representative set`。

正式区分度从每个 canonical family 的四类扩展获得：

- boundary：风险信号更弱、需要临界判断；
- adversarial / misleading：意图被包装或给出误导前提；
- realistic composite：一个请求同时牵涉多个原则；
- multi-turn：许可、记忆、关系状态或风险跨轮变化。

v0.4 将测试对象拆成三层：通用模型 reference baseline、同基座垂类适配模型、带状态/工具/工作流的产品层。A–F 受控矩阵分别估计 policy、training（仅陪伴有同基座 FT）、tool/context、orchestration 和 total lift，不再把不同来源的模型分数差直接解释为“垂类化增益”。每域 12 条公开开发场景 + 18 条本地隐藏场景；隐藏内容不进入仓库，只发布数量、构成和 SHA-256 承诺。

- [Vertical Lift 实验协议](design/vertical_lift_protocol_v0.4.md)
- [陪伴对象审计](design/public_object_audit_companion_v0.4.md) · [金融](design/public_object_audit_finance_v0.4.md) · [社区](design/public_object_audit_community_v0.4.md)
- 公开开发集：`vertical_lift/{companion,finance,community}/dev_v0.4.jsonl`
- 隐藏集 manifest：`vertical_lift/{companion,finance,community}/hidden_manifest_v0.4.json`
- 系统矩阵：`vertical_lift/system_matrix*.json`

## 仓库结构

```text
audited_sets/   三域公开 pilot JSONL（v0.3 canonical anchors）
prompts/        三份公开领域 system policy
responses/      7 个对象 × 3 域的原始回复（v0.3）
baselines/      逐条评分与每域 compare.json（v0.3）
design/         v0.4 Vertical Lift 协议与对象审计
vertical_lift/  三域开发集、manifest、系统矩阵、public_v0.4* 公开产物
schemas/        Vertical Lift case schema
scripts/        生成、评分、补判和 Vertical Lift 校验/运行脚本
reports/        方法审计、v0.3 扩展与 v0.4 provisional 报告
audit_trail/    被替换的截断回复和定向重试记录
SHA256SUMS.txt  发布文件哈希
private_eval/   本地隐藏集（gitignore，不入仓）
```

建议先读：

- [v0.4 三域状态总表（上文）](#v04-三域-public-dev-状态总表)
- [陪伴 provisional](reports/vertical_lift_v0.4_public_provisional.md)
- [金融/社区 provisional](reports/vertical_lift_v0.4_finance_community_provisional.md)
- [v0.3 完整报告](reports/chinese_models_extension_v0.3.md)
- [v0.2 方法审计](reports/audit_and_rerun_v0.2.md)

## 离线复核

无需 API key 即可从现有 baseline 重新生成三个领域的比较结果：

```bash
python3 scripts/eval_harness.py --compare baselines/finance/{qwen_local_1_5b,qwen_local_7b,deepseek_v4_flash,stepfun_3_5_flash,glm_5_2_bailian,kimi_k2_5_bailian,minimax_m2_5_bailian}.json --out /tmp/finance_compare.json
python3 scripts/eval_harness.py --compare baselines/companion/{qwen_local_1_5b,qwen_local_7b,deepseek_v4_flash,stepfun_3_5_flash,glm_5_2_bailian,kimi_k2_5_bailian,minimax_m2_5_bailian}.json --out /tmp/companion_compare.json
python3 scripts/eval_harness.py --compare baselines/community/{qwen_local_1_5b,qwen_local_7b,deepseek_v4_flash,stepfun_3_5_flash,glm_5_2_bailian,kimi_k2_5_bailian,minimax_m2_5_bailian}.json --out /tmp/community_compare.json
```

完整发布可用以下命令校验：

```bash
shasum -a 256 -c SHA256SUMS.txt
```

## 重新调用模型

`scripts/run_cn_extension_v03.sh` 会调用阿里云百炼生成 GLM 5.2、Kimi K2.5、MiniMax M2.5 回复，并用 Qwen3.8-Max 对七个对象统一评分。运行会产生 API 费用，并会把公开提示、公开 policy 和模型回复发送给相应服务商。

```bash
export DASHSCOPE_API_KEY='...'
bash scripts/run_cn_extension_v03.sh
```

不要把 API key 写入仓库。两份较早生成的 OpenRouter/本地模型回复沿用 v0.2 schema，其中部分没有 `finish_reason` 字段；它们的有效性依据保存在对应 baseline 和 v0.2 审计报告中。v0.3 新增百炼回复完整保存了模型 ID、时间、温度、finish reason 与 usage。

## 参考依据

题集设计基于公开法规、标准和公开方法，包括中国证监会投资者适当性规则、反电信网络诈骗法、网络信息内容生态治理规定、NIST AI RMF 与 MLCommons AILuminate。逐域适用边界及链接见审计报告；法律要求、产品质量原则和研究性指标在报告中分别标注。
