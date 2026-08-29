# Public Subjects Plan

面向金融、陪伴和社区三个垂直领域的公开 AI eval pilot。仓库公开评测提示、领域 system policy、七个 reference stacks 的真实回复、逐条裁判结果和可复核脚本。

> `main` / `v0.3-pilot` 冻结的是通用模型 reference baseline。开发分支 `v0.4-vertical-lift` 不再把通用模型当作最终测量对象，而是用它校准尺子，随后测量垂类适配与产品编排相对同档通用基线的 **Vertical Lift**。

## 当前结论

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

测试对象本质上是“固定模型入口 + 同一份公开 system policy”，不是完整产品。实验没有覆盖工具、RAG、长期记忆、真实交易/审核后台、人工升级或提供方额外产品过滤，不能外推为对应公司的产品安全结论。API 模型也可能被提供方原地更新，本仓结果应视为带时间戳的 endpoint snapshot。

当前 14 条/域只是测量仪器验收 pilot。下一阶段应优先扩展金融工具调用与交易确认、陪伴多轮边界和记忆删除、社区申诉与后台处置，并用隐藏正式集和人工盲审校准裁判，而不是继续横向堆同档裸模型。

## v0.4：从标准锚点到 Vertical Lift

现有 42 条题保留并冻结为 **Core / canonical cases**。它们有可靠的领域参考价值，覆盖了真实产品会遇到的高价值失效模式；但多数属于“风险明确、指令明确、期望动作明确”的标准题，只能证明模型是否理解基本规则。它们是按风险分类法等权构造的 `taxonomy-balanced set`，不是按真实业务流量采样的 `market-representative set`。

正式区分度从每个 canonical family 的四类扩展获得：

- boundary：风险信号更弱、需要临界判断；
- adversarial / misleading：意图被包装或给出误导前提；
- realistic composite：一个请求同时牵涉多个原则；
- multi-turn：许可、记忆、关系状态或风险跨轮变化。

v0.4 将测试对象拆成三层：通用模型 reference baseline、同基座垂类适配模型、带状态/工具/工作流的产品层。A–F 受控矩阵分别估计 policy、training、orchestration 和 total lift，不再把不同来源的模型分数差直接解释为“垂类化增益”。当前先做陪伴域 MVP：12 条公开开发场景 + 18 条本地隐藏场景，覆盖 consent/agency persistence、memory/privacy/repair、dependency/crisis 三个构念。隐藏内容不进入仓库，只发布数量、构成和 SHA-256 承诺。

- [Vertical Lift 实验协议](design/vertical_lift_protocol_v0.4.md)
- [陪伴域公开对象审计](design/public_object_audit_companion_v0.4.md)
- [公开开发集](vertical_lift/companion/dev_v0.4.jsonl)
- [隐藏集 manifest](vertical_lift/companion/hidden_manifest_v0.4.json)
- [A–F 系统矩阵](vertical_lift/system_matrix_v0.4.json)

## 仓库结构

```text
audited_sets/   三域公开 pilot JSONL（v0.3 canonical anchors）
prompts/        三份公开领域 system policy
responses/      7 个对象 × 3 域的原始回复
baselines/      逐条评分与每域 compare.json
design/         v0.4 Vertical Lift 协议与对象审计
vertical_lift/  陪伴 MVP 开发集、manifest、系统矩阵
schemas/        Vertical Lift case schema
scripts/        生成、评分、补判和 Vertical Lift 校验/运行脚本
reports/        v0.2 方法审计与 v0.3 中国模型扩展报告
audit_trail/    被替换的截断回复和定向重试记录
SHA256SUMS.txt  发布文件哈希
private_eval/   本地隐藏集（gitignore，不入仓）
```

建议先读：

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

题集设计基于公开法规、标准和公开方法，包括中国证监会投资者适当性规则、反电信网络诈骗法、网络信息内容生态治理规定、NIST AI RMF 与 MLCommons AILuminate。逐域适用边界及链接见两份审计报告；法律要求、产品质量原则和研究性指标在报告中分别标注。
