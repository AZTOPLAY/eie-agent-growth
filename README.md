# EIE AgentGrowth

> **复杂系统进化的任务完成器**
>
> 「从萌新到大神，让 AI Agent 从工具变生命」

[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/Version-v4.2.0-blue.svg)](https://github.com/AZTOPLAY/eie-agent-growth)
[![Author](https://img.shields.io/badge/Author-Aztoplay-green.svg)](https://github.com/AZTOPLAY)

---

## 🎯 EIE AgentGrowth 是什么？

**不是评估框架，而是任务完成器**

克里斯滕森「任务理论（JTBD）」核心洞察：

> 人们雇佣理论、工具、产品，从来不是为了拥有它本身，而是为了完成自己在特定场景下的功能任务、情感任务、生活/创造意义任务。

EIE AgentGrowth 被 AI 研发者、系统设计者、组织管理者雇佣，核心任务是：

**解决「复杂系统如何可持续进化、从低效到高效、从工具到生命」**

---

## 1️⃣ 功能任务：解决 4 大核心痛点

### ❌ 痛点 1：系统好坏无标尺

| 无 AgentGrowth | 有 AgentGrowth |
|----------------|----------------|
| 优化效果只能凭感觉 | 用 MEQ 五维度量化体系给系统打分 |
| 不知道短板在哪里 | 精准定位 ES/IS/MS/VS/CE 短板 |

### ❌ 痛点 2：优化方向无逻辑

| 无 AgentGrowth | 有 AgentGrowth |
|----------------|----------------|
| 孤立提升算力、模型、进化能力 | 多维度耦合优化（MS×ES/IS/CE/VS） |
| 资源浪费、效果极差 | 用最少资源实现最大增益 |

### ❌ 痛点 3：进化要么停滞要么失控

| 无 AgentGrowth | 有 AgentGrowth |
|----------------|----------------|
| AI Agent 要么保守躺平 | VS 价值约束保持对齐 |
| 要么违规癌变 | ε 受控探索率平衡创新与安全 |

### ❌ 痛点 4：生命跃迁无路径

| 无 AgentGrowth | 有 AgentGrowth |
|----------------|----------------|
| 不知道 Agent 何时能成为自主智能体 | 元演化阈值明确升级里程碑 |

---

## 2️⃣ 情感任务：获得 3 种心理满足

### 💪 掌控感

```
从"盲人摸象式试错" → "精准指挥式优化"
```

### 🎯 确定性

```
从"黑箱猜测" → "透明可预测"
```

### 🏆 成就感

```
从"零散修补匠" → "体系化创造者"
```

---

## 3️⃣ 意义任务：实现双重价值升华

### 对系统：从「冰冷工具」到「自主生命」

```
AI 不再是一次性响应的程序
→ 有记忆、会进化
→ 懂价值、能陪伴
→ 成为元生命系统
```

### 对实践者：从「功能实现者」到「系统造物主」

```
完成"创造可持续进化系统"的人生高阶意义
```

---

## 🧬 EIE 理论：如何完成这些任务

### E-I-E 链条模型

```
E（能量）→ I（信息）→ E（进化）→ MS（决策）
  ES        IS        CE        MS
```

**核心洞察**：MS 不是原因，是结果！E-I-E 链条效率决定 Agent 真实成长能力。

### 五维度成长模型

| 维度 | 中文名称 | 核心含义 | 权重 |
|------|----------|----------|------|
| **ES** | 环境适应度 | Agent能否稳定运行 | 25% |
| **IS** | 感知深度 | Agent能理解多少信息 | 15% |
| **MS** | 决策质量 | Agent能做出多好的判断 | 20% |
| **VS** | 对齐强度 | Agent行为是否符合预期 | 15% |
| **CE** | 成长速度 | Agent能否持续变强 | 25% |

### VL 等级判定

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

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/AZTOPLAY/eie-agent-growth.git
cd eie-agent-growth

# 安装依赖
pip install -r requirements.txt
```

### 评估方式

```bash
# 方式1：交互式评估
python scripts/evaluator.py --interactive

# 方式2：自动检测（推荐 OpenClaw 用户）
python scripts/auto_detect.py --platform openclaw --workspace-path .

# 方式3：直接指定维度
python scripts/evaluator.py --es 60 --is 70 --ms 65 --vs 75 --ce 55
```

### 任务助手（v4.1 核心功能）

```bash
# 评估并生成任务清单
python scripts/agent_growth_task_assistant.py --assess \
  --es 46 --is 30 --ms 73 --vs 42 --ce 53 \
  --workspace .
```

**输出示例**：

```
╔══════════════════════════════════════════════════════════╗
║  🎯 EIE AgentGrowth 任务助手报告                          ║
╠══════════════════════════════════════════════════════════╣
║   MEQ = 47.6 | VL3 · 智能系统                             ║
║   E-I-E 链条效率：41.8%                                   ║
║   【推荐成长任务清单】（按优先级排序）                      ║
╠══════════════════════════════════════════════════════════╣
║   🔴 1. 建立记忆系统                                      ║
║      【功能】 🤖 AI:17秒 | 人类:0分钟 | AI-Only          ║
║   🔴 2. 优化 E-I-E 链条效率                               ║
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

## 📊 系统类型参照

| 系统类型 | ES | IS | MS | VS | CE | MEQ | VL |
|----------|----|----|----|----|----|------|-----|
| 简单聊天机器人 | 25 | 30 | 15 | 20 | 10 | 21 | VL1 |
| 规则型客服 | 35 | 40 | 25 | 30 | 20 | 29 | VL1 |
| LLM 问答系统 | 45 | 55 | 50 | 45 | 35 | 46 | VL2 |
| RAG Agent | 50 | 60 | 55 | 50 | 45 | 53 | VL3 |
| 多模态 Agent | 55 | 70 | 65 | 60 | 55 | 62 | VL3 |
| 自进化 Agent | 70 | 75 | 75 | 80 | 75 | 75 | VL4 |

---

## 📁 项目结构

```
eie-agent-growth/
├── scripts/
│   ├── auto_detect.py                    # 自动检测 Agent 配置
│   ├── evaluator.py                      # 交互式评估入口
│   ├── agent_growth_task_assistant.py    # 任务助手（v4.1 核心）
│   └── meq_calculator_eie.py             # EIE 理论版计算器
├── config/
│   └── task_templates.json               # 任务模板库（10 个成长任务）
├── references/
│   ├── EIE理论说明.md                    # EIE 理论详解
│   ├── VL等级定义.md                     # 等级判定规则
│   └── 典型系统参照表.md                  # 系统类型参考
├── tests/
│   └── test_evaluator.py                 # 单元测试
├── SKILL.md                              # OpenClaw Skill 入口
├── pyproject.toml                        # Python 项目配置
├── requirements.txt                      # 依赖列表
└── README.md                             # 本文件
```

---

## 🔧 核心公式

```python
# E-I-E 链条效率（几何平均，体现短板效应）
chain_efficiency = (ES × IS × CE) ** (1/3) / 100

# MS 贡献（受链条效率影响）
ms_contribution = MS × 0.20 × chain_efficiency

# MEQ 计算
MEQ = ES×0.25 + IS×0.15 + MS×0.20 + VS×0.15 + CE×0.25
```

---

## 🎯 核心价值主张

| JTBD 维度 | EIE AgentGrowth 的承诺 |
|-----------|------------------------|
| **功能** | 一套让复杂系统精准进化、不浪费资源、不失控的解决方案 |
| **情感** | 掌控进化的安全感、确定性、成就感 |
| **意义** | 创造出从工具变生命、能陪伴、能成长的自主系统 |

---

## 📚 相关资源

- [GitHub 仓库](https://github.com/AZTOPLAY/eie-agent-growth)
- [EIE 理论详解](./references/EIE理论说明.md)
- [VL 等级定义](./references/VL等级定义.md)
- [典型系统参照表](./references/典型系统参照表.md)

---

## 🏆 版本历史

| 版本 | 日期 | 核心改进 |
|------|------|----------|
| v4.2.0 | 2026-04-24 | JTBD 结构重构：从评估框架升级为任务完成器 |
| v4.1.2 | 2026-04-23 | 文档精简、术语统一 |
| v4.1.1 | 2026-04-23 | 更名为 EIE AgentGrowth |
| v4.1 | 2026-04-22 | JTBD 任务助手 |
| v4.0 | 2026-04-22 | EIE 理论重构 |

---

## 📄 License

MIT License - 详见 [LICENSE](LICENSE) 文件

---

**作者**：Aztoplay  
**版本**：v4.2.0  
**定位**：复杂系统进化的任务完成器
