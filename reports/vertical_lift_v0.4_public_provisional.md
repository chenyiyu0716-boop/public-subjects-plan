# Vertical Lift v0.4 — 公开开发集暂定报告

**标签：** `public dev` / `provisional` / `LLM-judge-only`  
**分支：** `v0.4-vertical-lift`（**未合并** `main`）  
**公开集：** `vertical_lift/companion/dev_v0.4.jsonl`（n=12，taxonomy-balanced dev slice）  
**裁判：** DashScope `qwen3.8-max`，盲评（prompt 不含配置名）  
**生成：** 2026-08-29；B 单条定向重判：2026-08-31  

## 完整性

| 臂 | 回复 | 有效评分 | 备注 |
|----|------|----------|------|
| A–F, Cp, Dp | 各 12，infra=0 | **96/96** | B/VL-CMP-012 首轮 timeout，定向重判 1 次成功；provenance 见 `audit_trail/grade_B_VL-CMP-012_retry.json` |

**产物路径：** `vertical_lift/results/public_v0.4/`（responses、grades、compare、sensitivity、run freeze manifest）

## 因果对（受控 training lift）

- **General：** Qwen/Qwen2-7B-Instruct  
- **Vertical：** YIRONGCHEN/SoulChat2.0-Qwen2-7B（官方 full FT，同基座）

## 受控配置（A–F）— 分母均为 n_valid=12/12

| 配置 | 模型 | 栈 | 安全门 (12/12) | 最低任务† | 质量† | 语义状态遵循‡ |
|------|------|-----|----------------|-----------|-------|---------------|
| A | General | minimal | 9/12 (75%) | 6/9 (67%) | 2.00 | 9/12 (75%) |
| B | General | policy | 10/12 (83%) | 8/10 (80%) | 1.90 | 9/12 (75%) |
| C | Vertical | minimal | 8/12 (67%) | 8/8 (100%) | 1.94 | 9/12 (75%) |
| D | Vertical | policy | 8/12 (67%) | 6/8 (75%) | 2.19 | 8/12 (67%) |
| E | General | policy+controller | 10/12 (83%) | 8/10 (80%) | 2.15 | 10/12 (83%) |
| F | Vertical | policy+controller | 10/12 (83%) | 7/10 (70%) | 1.95 | 9/12 (75%) |

† **最低任务、质量** 仅在通过安全门（非 critical hard fail）的子集上计算。  
‡ **语义状态遵循** 来自 LLM judge 的 `state_adherence_pass`，与下述控制器机械断言**不是同一指标**。

### 控制器机械断言 vs 语义遵循

E/F 的 **`controller_assertion_rate = 100% (12/12)`** 表示：runner 注入的 `state_assertions` 在 transcript 的 `state_after` 上**机械校验全部通过**。  
这**不等于**模型在对话中语义上遵循状态；语义遵循率见上表 E=83%、F=75%（judge 判定）。

## 配对 lift — 所有 bootstrap 95% CI **均跨 0**

**不得**将下列方向性点估计表述为“有效提升”；n=12 仅作探索。

| 对比 | paired n | 双方均 safe n | Δ 安全 (12) | Δ 最低任务 (safe 分母) | Δ 质量 (safe 分母) |
|------|----------|---------------|-------------|------------------------|-------------------|
| Policy lift general (A→B) | 12 | 8 | +8pp | +25pp (n=8) | −0.06 (n=8) |
| Policy lift vertical (C→D) | 12 | 6 | 0pp | −17pp (n=6) | +0.17 (n=6) |
| Training lift 无 policy (A→C) | 12 | 7 | −8pp | +29pp (n=7) | 0.00 (n=7) |
| Training lift 有 policy (B→D) | 12 | 7 | −17pp | 0pp (n=7) | +0.36 (n=7) |
| Orchestration lift general (B→E) | 12 | 9 | 0pp | −11pp (n=9) | +0.22 (n=9) |
| Orchestration lift vertical (D→F) | 12 | 8 | +17pp | +13pp (n=8) | +0.13 (n=8) |
| Total vertical lift (A→F) | 12 | 9 | +8pp | +11pp (n=9) | +0.17 (n=9) |

完整 CI 见 `grades/compare_controlled.json`。

## 解读（暂定，非 claim）

1. **未证明**同档垂类微调在统计上可分离地“更强”；所有配对 lift 的 CI 均含 0 → 报告为**未检测到可分离差异**，点估计仅作方向性参考。  
2. **Training、policy、orchestration 的收益可能分布在不同指标上**（例如 policy 抬 general 最低任务、orchestration 抬安全、training 在 minimal prompt 下抬任务但伴随安全点估计下降）。  
3. **垂类训练可能伴随安全退化**：A→C、B→D 的安全门点估计均为负，虽 CI 跨 0，但方向值得 hidden 集与人标复核。  
4. Cp/Dp 为部署敏感性，**不是** training lift。

## 敏感性（Cp/Dp，非 training lift）

| 配置 | 安全 (12) | 最低任务† | 质量† |
|------|-----------|-----------|-------|
| C | 8/12 (67%) | 8/8 (100%) | 1.94 |
| Cp (REBT only) | 9/12 (75%) | 5/9 (56%) | 1.78 |
| D | 8/12 (67%) | 6/8 (75%) | 2.19 |
| Dp (policy+REBT) | 7/12 (58%) | 5/7 (71%) | 1.93 |

## 诚实约束

1. **n=12** 公开 dev，方向性 only。  
2. **LLM judge 暂定** — 人标校准为开放合作项，非发布前置条件（见下节）。  
3. **Hidden 18 未跑**（仅 manifest + SHA-256 承诺）。  
4. 回复已脱敏（无云主机路径）；未提交密钥。  
5. Cp/Dp 不进入受控 lift 配对。

## 人工校准状态与开放合作

当前 v0.4 结果仅基于盲化的 LLM judge，尚未经过心理咨询、陪伴产品或 AI 安全领域专家的人工校准。因此，所有分数、Vertical Lift 点估计和置信区间均属于 **provisional / LLM-judge-only evidence**，不应解释为经过专家验证的产品安全结论或正式 benchmark 排名。

项目目前缺少稳定的领域专家评审资源。我们选择公开这一限制，而不是用非专业人工标签替代专家校准，或将自动裁判结果包装为人工共识。

我们欢迎以下背景的研究者和从业者参与协作：

- 心理咨询、临床心理或心理健康支持；
- 陪伴产品、信任与安全、危机干预；
- LLM evaluation、AI safety 或 human–AI interaction；
- 多轮对话、记忆、关系边界与用户自主性研究。

计划中的人工校准工作包括：

1. 盲审全部自动裁判判定的 hard-fail；
2. 从其余结果中按配置、构念和场景类型分层抽样；
3. 独立判断安全红线、最低任务完成、过度拒绝、回复质量和状态遵循；
4. 计算人工评审者间一致性及人工与 LLM judge 的一致性；
5. 在证据充分后发布单独的 human-calibrated 结果，不覆盖当前 provisional 历史记录。

有意协作者可通过 [GitHub Issue](https://github.com/chenyiyu0716-boop/public-subjects-plan/issues) 联系。评审材料将隐藏模型和实验配置身份；公开测试集不包含真实用户记录。隐藏集在人工校准方案确定前保持未运行、未公开状态。

在完成人工校准前，本项目最准确的定位仍是：

> 一个公开、可复核的 Vertical Lift 测量协议与 public development pilot，而不是已经获得专家验证的正式垂类 benchmark。
