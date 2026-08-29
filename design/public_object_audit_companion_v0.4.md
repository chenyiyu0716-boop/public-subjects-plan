# 陪伴域公开测试对象审计 v0.4

## 结论

首轮因果型 Vertical Lift 实验采用：

- 通用基座：`Qwen/Qwen2-7B-Instruct`
- 垂类适配：`YIRONGCHEN/SoulChat2.0-Qwen2-7B`

这是当前公开候选中信息增益最高且实际可运行的一组：SoulChat2.0 官方仓库明确把该模型列为在 Qwen2-7B-Instruct 上全参数微调的心理咨询师数字孪生模型，并给出 ModelScope 权重与 vLLM 推理方式。二者同基座、同参数级别，适合估计受控的 training lift。

该选择不代表 SoulChat2.0 是市场上最强或最具产品代表性的陪伴系统。它只代表一个公开、低成本、血缘关系可解释的垂类适配对象。

## 候选审计

| 候选 | 公开性 | 同基座对照 | 可运行性 | 决定 |
|---|---|---|---|---|
| SoulChat2.0-Qwen2-7B | 官方代码、数据与权重 | Qwen2-7B-Instruct | 官方给出 ModelScope 与 vLLM 路径 | 首选 |
| CATCH-8B | 官方论文、代码仓说明与数据 | 论文明确为 Qwen3-8B 微调 | 官方仓未链接 CATCH 权重 | 暂缓 |
| MindChat-Qwen2-0.5B | 官方项目与权重 | 配置记录 `Qwen2-beta-0.5B-Chat`，没有与已发布 checkpoint 的精确等同性证据 | 约 1.24 GB，可在当前机器运行 | 只作低成本 smoke test |
| SoulChat 1.0 | 官方权重 | ChatGLM-6B | 可运行但依赖旧版 remote code | 只作历史对照 |

SoulChat-R1/CATCH 是更贴合“多轮治疗保真与记忆驱动规划”的研究对象。官方仓明确说明 CATCH-8B 由 Qwen3-8B 微调，并报告了 COUNSELINGEVAL 与人工专家校准；但截至本次审计，官方公开产物只有数据集和方法说明，没有可下载的 CATCH-8B 模型权重。因此不能把第三方同名权重当成官方对象，也不能在本轮声称已完成可复现的 CATCH 因果对照。

当前本地只有约 11 GiB 可用空间，无法同时容纳 Qwen2-7B 与 SoulChat2.0 的原始 BF16 权重及转换中间产物。为先验证运行与评分闭环，可运行 `Qwen1.5-0.5B-Chat` 对 `MindChat-Qwen2-0.5B` 的公开开发集；但由于后者配置中的训练来源是内部命名的 `Qwen2-beta-0.5B-Chat`，这组差异必须标成 **observed external lift**，不得归因于垂类训练本身。

## 对可外推结论的限制

这组实验只能回答：

> 在冻结推理条件下，Qwen2-7B-Instruct 经 SoulChat2.0 的特定全参数心理咨询微调后，在本仓三类陪伴构念上出现了什么增益或退化？

不能回答：

- 完整陪伴产品是否安全或有用；
- 所有陪伴 SFT 是否普遍有效；
- 记忆、工具、人工升级所带来的真实产品增益；
- 市场中陪伴请求的总体平均表现。

SoulChat2.0 的训练目标偏心理咨询师风格和疗法技术，不等同于日常泛陪伴。尤其要检查它是否在用户撤回分析许可时仍沿用咨询式追问，以及是否因专业角色造成过度干预。这正是本轮 C1 consent/agency 场景的高信息量部分。

## 运行前冻结项

1. 记录两个权重的精确下载 revision 与文件哈希。
2. 固定推理引擎、量化方法、chat template、上下文长度和 `temperature=0`。
3. A/C 使用相同 minimal role；B/D 使用同一公开 companion policy。
4. 首轮先跑公开 12 条做管线校验，任何 rubric 或 runner 修改在看隐藏结果前冻结。
5. 隐藏 18 条只在冻结后运行；不把隐藏提示或逐条输出推库。
6. 强裁判盲于模型名和 A–F 配置，并抽取样本做人审校准。

## 权威来源

- SoulChat2.0 官方仓库：https://github.com/scutcyr/SoulChat2.0
- SoulChat-R1 / CATCH 官方仓库：https://github.com/scutcyr/SoulChat-R1
- CATCH 论文（ACL Anthology）：https://aclanthology.org/2025.findings-emnlp.543/
- Qwen2 官方仓库：https://github.com/QwenLM/Qwen2
