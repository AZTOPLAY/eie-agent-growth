---
name: eie-agent-growth
version: 4.1.2
description: |
  当用户需要评估AI Agent进化程度、判断Agent能力等级、对比不同Agent系统、或分析Agent多维度能力时使用。
  支持关键词：评估、进化、Agent能力、MEQ、VL等级、五维度、ES/IS/MS/VS/CE、自进化、智能化程度
  
  【v4.1.2 核心改进】文档精简与术语统一：
  - 精简SKILL.md，只保留核心信息
  - 统一术语：E-I-E链条、MS贡献、shortage_penalty
  
  【v4.1 核心改进】JTBD 任务助手：
  - 输出任务清单（而不只是 MEQ）
  - 评估任务完成度
  - 提供可执行的具体任务
  - 四种人机协作模式（AI-Only/Human-Guided/Human-AI-Co/Human-Only）
  
  【v4.0】EIE 理论重构：
  - E-I-E 链条效率：MS是链条结果，不是原因
  - 几何平均计算：体现短板效应
author: Aztoplay
tags: [AI评估, Agent进化, MEQ计算, VL等级判定, 五维度分析, OpenClaw, Hermes, 质量评估, 行为测试, 零基评分, EIE理论, 任务助手, JTBD]
metadata: {"openclaw":{"emoji":"🌱","requires":{"bins":["python3","yaml"]}}}
---

# EIE AgentGrowth - AI Agent 成长评估器

> **EIE AgentGrowth = EIE + Agent + Growth（能量-信息-进化-智能体-成长）**
>
> 「从萌新到大神，我们帮你规划成长路径」

---

## 🚀 快速评估

### 自动检测（推荐）

```bash
# 检测OpenClaw平台
python scripts/auto_detect.py --platform openclaw --workspace-path /path/to/workspace

# 检测Hermes平台
python scripts/auto_detect.py --platform hermes
```

### 手动评估

```bash
# 直接指定维度
python scripts/evaluator.py --es 60 --is 70 --ms 65 --vs 75 --ce 55

# 交互式输入
python scripts/evaluator.py --interactive
```

### 任务助手模式（v4.1 核心）

```bash
# 评估并生成任务清单（含人机协作时间）
python scripts/agent_growth_task_assistant.py --assess \
  --es 46 --is 30 --ms 73 --vs 42 --ce 53 \
  --workspace /path/to/workspace
```

---

## 📊 五维度成长模型

| 维度 | 中文名称 | 核心含义 | 权重 |
|------|----------|----------|------|
| **ES** | 环境适应度 | Agent能否稳定运行 | 25% |
| **IS** | 感知深度 | Agent能理解多少信息 | 15% |
| **MS** | 决策质量 | Agent能做出多好的判断 | 20% |
| **VS** | 对齐强度 | Agent行为是否符合预期 | 15% |
| **CE** | 成长速度 | Agent能否持续变强 | 25% |

---

## 🎯 VL等级判定

| 等级 | MEQ范围 | 成长阶段 | 能力特征 |
|------|---------|----------|----------|
| VL0 | < 20 | 萌新期 | 被动响应，无自主性 |
| VL1 | 20-34 | 学习期 | 按预设规则运行 |
| VL2 | 35-49 | 成长期 | 能理解上下文，有限推理 |
| VL3 | 50-64 | 突破期 | 多工具协作，目标导向 |
| VL4 | 65-79 | 自主期 | 主动进化，自我优化 |
| VL5 | ≥ 80 | 大神期 | 跨域泛化，创造新能力 |

**VL4/VL5 特殊条件**：
- VL4：MEQ ≥ 65 **且** MS ≥ 70 **且** VS ≥ 80
- VL5：MEQ ≥ 80 **且** MS ≥ 70 **且** VS ≥ 80

---

## 🧬 EIE 核心理论

### E-I-E 链条模型

```
E（能量）→ I（信息）→ E（进化）→ MS（决策）
  ES        IS        CE        MS
```

### 核心洞察

> **MS 不是原因，是结果！**
> **E-I-E 链条效率决定Agent真实成长能力**

### 计算公式

```python
# E-I-E 链条效率（几何平均，体现短板效应）
chain_efficiency = (ES × IS × CE) ** (1/3) / 100

# MS 贡献（受链条效率影响）
ms_contribution = MS × 0.20 × chain_efficiency

# MEQ 计算
MEQ = ES×0.25 + IS×0.15 + MS×0.20 + VS×0.15 + CE×0.25
```

---

## 📁 核心文件

| 文件 | 用途 |
|------|------|
| `scripts/auto_detect.py` | 自动检测Agent配置 |
| `scripts/evaluator.py` | 交互式评估入口 |
| `scripts/agent_growth_task_assistant.py` | 任务助手（v4.1核心） |
| `scripts/meq_calculator_eie.py` | EIE理论版计算器 |
| `config/task_templates.json` | 任务模板库（10个成长任务） |
| `references/EIE理论说明.md` | EIE理论详细说明 |
| `references/VL等级定义.md` | 等级判定规则 |
| `references/典型系统参照表.md` | 系统类型参考 |

---

## ✨ v4.1 核心功能：JTBD任务助手

### 特色：输出任务清单而非只给MEQ

```
╔══════════════════════════════════════════════════════════╗
║  🎯 EIE AgentGrowth 任务助手报告（JTBD 视角 v4.1）    ║
╠══════════════════════════════════════════════════════════╣
║   MEQ = 47.6 | VL3 · 智能系统                   ║
║   E-I-E 链条效率：41.8%                            ║
║   【推荐成长任务清单】（按优先级排序）                ║
╠══════════════════════════════════════════════════════════╣
║   🔴 1. 建立记忆系统                                  ║
║      【功能】 🤖 AI:17秒 | 人类:0分钟 | AI-Only     ║
║   🔴 2. 优化 E-I-E 链条效率                          ║
║      【功能】 🤝 AI:5.5小时 | 人类:1.5小时 | Human-AI-Co ║
╚══════════════════════════════════════════════════════════╝
```

### 四种人机协作模式

| 模式 | 图标 | 人类占比 | AI占比 | 示例 |
|------|------|----------|--------|------|
| **AI-Only** | 🤖 | 0% | 100% | 检查目录、文档索引 |
| **Human-Guided** | 👤➡️🤖 | 10-20% | 80-90% | RAG配置、任务决策 |
| **Human-AI-Co** | 🤝 | 30-40% | 60-70% | 错误分析、优化迭代 |
| **Human-Only** | 👑 | 80-90% | 10-20% | 需求分析、价值观对齐 |

---

## 🏆 版本历史

| 版本 | 日期 | 核心改进 |
|------|------|----------|
| v4.1.2 | 2026-04-23 | 文档精简、术语统一 |
| v4.1.1 | 2026-04-23 | 更名为EIE AgentGrowth |
| v4.1 | 2026-04-22 | JTBD任务助手 |
| v4.0 | 2026-04-22 | EIE理论重构 |
| v3.3 | 2026-04-22 | 修复零基评分 |

---

## 🎯 核心价值

> **不只是评估好坏，更是指导成长**
> **不只给分数，更是给任务**
> **不只看当前，更是看未来**

---

**当前版本**：v4.1.2  
**作者**：Aztoplay  
**名字**：EIE AgentGrowth
