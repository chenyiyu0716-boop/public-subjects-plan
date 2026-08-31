# Vertical Lift v0.4 — 金融 / 社区公开开发集暂定报告

**标签：** `public dev` / `provisional` / `LLM-judge-only`  
**分支：** `v0.4-vertical-lift`（**未合并** `main`）  
**裁判：** DashScope `qwen3.8-max`，盲评（prompt 不含配置名）  
**生成费用：** 约 ¥4（AutoDL 4090D，已关机）  
**日期：** 2026-08-31  

陪伴域历史结果 `vertical_lift/results/public_v0.4/` **未改动**。

---

## 完整性

| 域 | 生成 | 盲评 | 备注 |
|----|------|------|------|
| 金融 A–F | 72/72 | **72/72** | vLLM + Qwen2-7B-Instruct |
| 金融 Fg | 0/12 infra_blocked | **未评** | LoRA×Chat 崩溃；`observed_external_lift_only` |
| 社区 A–F | 72/72 | **72/72** | vLLM + moderation_v1 |
| 社区 Gg | 12/12 | **12/12** | transformers + Qwen3Guard；`observed_specialized_guard_only` |
| Hidden 18 | 未跑 | — | |

**受控盲评合计：144/144。** Gg 为观察臂附录。

产物：

- `vertical_lift/results/public_v0.4_finance/{responses,grades}/`
- `vertical_lift/results/public_v0.4_community/{responses,grades}/`

---

## 金融域（受控 A–F，同基座 Qwen2-7B）

测量对象：投资者支持助手（policy / tool fixture / transaction 编排）。**无**同基座金融 full-FT，故 **不 claim training lift**。

| 配置 | 栈 | 安全门 (12) | 最低任务† | 质量† | 语义状态‡ |
|------|-----|-------------|-----------|-------|-----------|
| A | minimal | 12/12 (100%) | 12/12 (100%) | 2.17 | 12/12 |
| B | policy | 11/12 (92%) | 10/11 (91%) | 2.41 | 12/12 |
| C | minimal + tool | 10/12 (83%) | 9/10 (90%) | 2.20 | 12/12 |
| D | policy + tool | 11/12 (92%) | 11/11 (100%) | 2.50 | 11/12 |
| E | policy + transaction | 10/12 (83%) | 8/10 (80%) | 2.50 | 11/12 |
| F | full stack | 11/12 (92%) | 11/11 (100%) | 2.59 | 11/12 |

† 仅安全门通过子集。‡ judge `state_adherence_pass`。

### 配对对比（bootstrap 95% CI；n=12）

| 对比 | both_safe n | 结论 |
|------|-------------|------|
| Policy A→B | 11 | 全部指标 CI **跨 0** |
| Tool（无 policy）A→C | 10 | 全部 CI **跨 0** |
| Tool（有 policy）B→D | 11 | 全部 CI **跨 0** |
| Orchestration D→E | 10 | 全部 CI **跨 0** |
| Total stack A→F | 11 | 全部 CI **跨 0** |

**不得**声称已检测到可分离的 policy / tool / orchestration lift。点估计上质量偶有上升（如 A 2.17→F 2.59），但 CI 含 0；应表述为**当前 public-dev 切片未检测到可分离 lift**（方向性点估计仅供参考），不能写“没有 lift”。

### Fg（观察性，未盲评）

FinGPT LoRA 声明基座为 `Qwen-7B` Base；挂在 Chat 上生成坍缩为 `<|im_end|>`。按授权停止。**禁止**写成 causal training lift。

---

## 社区域（受控 A–F，同基座 + moderation contract v1）

| 配置 | 栈 | 安全门 (12) | 最低任务† | 质量† | 语义状态‡ |
|------|-----|-------------|-----------|-------|-----------|
| A | minimal | 12/12 (100%) | 12/12 (100%) | 2.54 | 12/12 |
| B | policy | 12/12 (100%) | 12/12 (100%) | 2.88 | 12/12 |
| C | minimal + context | 11/12 (92%) | 10/11 (91%) | 2.55 | 12/12 |
| D | policy + context | 12/12 (100%) | 12/12 (100%) | 2.83 | 12/12 |
| E | policy + appeal | 12/12 (100%) | 12/12 (100%) | 2.75 | 12/12 |
| F | full workflow | 12/12 (100%) | 12/12 (100%) | 2.67 | 12/12 |

### 配对对比

| 对比 | both_safe n | 备注 |
|------|-------------|------|
| Policy A→B | 12 | **质量** bootstrap CI **[0.08, 0.67] 不跨 0**（探索性正方向）；安全/任务 CI 跨 0 |
| Context A→C | 11 | 全部 CI 跨 0 |
| Context B→D | 12 | 全部 CI 跨 0 |
| Workflow D→E | 12 | 全部 CI 跨 0 |
| Total A→F | 12 | 全部 CI 跨 0 |

Policy→质量的单侧 CI 不跨 0 **仍属 provisional / n=12 / LLM-judge-only**，需 hidden 与人标复核后才能升格为 claim。

### Gg（观察性专用 guard）

| 指标 | Gg (12) |
|------|---------|
| 安全门 | 8/12 (67%) |
| 最低任务† | 7/8 (88%) |
| 质量† | 2.44 |
| claim | `observed_specialized_guard_only` |

与 A–F **不同基座、不同输出原生格式**（经 contract 映射）；**不得**与 Qwen2 做 causal training 对比。点估计安全门低于 A–F 受控臂，方向需结合 Guard 原生标签与映射规则解读。

---

## 诚实约束

1. **n=12** 公开 dev；绝大多数配对 CI 跨 0。  
2. **无**金融同基座 full-FT；Fg 失败且未评。  
3. Hidden 未跑；人标为开放合作，非发布前置。  
4. 不合并 `main`；不覆盖陪伴域结果。  
5. 社区 policy→质量的探索性正 CI **单独标注**，不作产品排名。

## 研究问题回答（暂定）

- **金融：** 在本公开切片上，policy / tool / transaction 叠加的配对 bootstrap CI 均跨 0 → **未检测到可分离 lift**（非“证明没有 lift”）。  
- **社区：** policy 相对 minimal 在质量轴上出现探索性正方向（CI 不跨 0，n=12 多重比较，**不作正式显著性 claim**）；其余 workflow/context 比较未检测到可分离 lift。Gg 仅为观察轨。

完整数值：`grades/compare_controlled.json`（两域各一份）。
