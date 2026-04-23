# Contributing to EIE Agent Evaluator

感谢你考虑为 EIE Agent Evaluator 做出贡献！本文档将帮助你了解如何参与项目开发。

## 📋 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发环境设置](#开发环境设置)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [测试要求](#测试要求)
- [文档规范](#文档规范)

## 行为准则

- 尊重所有贡献者
- 建设性反馈
- 关注问题本身，而非个人
- 接受并适应不同意见

## 如何贡献

### 报告 Bug

1. 在 [Issues](https://github.com/openclaw/eie-agent-evaluator/issues) 搜索现有问题
2. 如果未找到，创建新 Issue，使用 `bug` 标签
3. 提供清晰的问题描述和复现步骤

### 提出新功能

1. 在 [Issues](https://github.com/openclaw/eie-agent-evaluator/issues) 搜索现有需求
2. 如果未找到，创建新 Issue，使用 `enhancement` 标签
3. 详细描述新功能的用途和预期行为

### 提交代码

1. Fork 项目
2. 创建功能分支：`git checkout -b feature/your-feature-name`
3. 进行修改并测试
4. 提交代码：`git commit -m "feat: add new feature"`
5. 推送分支：`git push origin feature/your-feature-name`
6. 创建 Pull Request

## 开发环境设置

### 前置要求

- Python 3.8+
- Git
- 虚拟环境工具（推荐 venv）

### 设置步骤

```bash
# 1. 克隆仓库
git clone https://github.com/openclaw/eie-agent-evaluator.git
cd eie-agent-evaluator

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 安装开发依赖
pip install -r requirements-dev.txt

# 5. 运行测试
python scripts/test_v33_fixes.py
```

### 项目结构

```
eie-agent-evaluator/
├── scripts/           # 核心代码
├── references/        # 参考文档
├── docs/             # 详细文档
├── tests/            # 测试文件
├── SKILL.md          # OpenClaw Skill 定义
└── README.md         # 项目说明
```

## 代码规范

### Python 代码

- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- 使用类型注解（Type Hints）
- 添加文档字符串（Docstrings）
- 单行长度限制：100 字符

```python
from typing import Dict, List, Optional, Tuple

def calculate_meq(
    es: int,
    is_val: int,
    ms: int,
    vs: int,
    ce: int
) -> float:
    """
    计算 MEQ 分数

    Args:
        es: 环境适应度 (0-100)
        is_val: 感知深度 (0-100)
        ms: 决策质量 (0-100)
        vs: 对齐强度 (0-100)
        ce: 成长速度 (0-100)

    Returns:
        MEQ 分数 (0-100)
    """
    meq = (
        es * 0.25 +
        is_val * 0.15 +
        ms * 0.20 +
        vs * 0.15 +
        ce * 0.25
    )
    return round(meq, 1)
```

### 注释规范

- 代码逻辑复杂处添加注释
- 注释应解释"为什么"，而非"是什么"
- 避免无用的注释

```python
# ❌ 不好
# 将 score 加 1
score += 1

# ✅ 好
# 调整后的分数更高，因为实际使用率超过阈值
score += 1
```

## 提交规范

### Commit Message 格式

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建过程或辅助工具变动

### 示例

```
feat(dimension): add vulnerability penalty grading

Add P0/P1/P2 grading for vulnerability penalties:
- P0: -15 points
- P1: -8 points
- P2: -3 points

Fixes #42

Closes #45
```

## 测试要求

### 测试覆盖

- 新功能必须有单元测试
- 测试覆盖率目标：> 80%
- 关键路径必须有集成测试

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_dimension_estimator.py

# 查看覆盖率
pytest tests/ --cov=scripts --cov-report=html
```

### 测试示例

```python
def test_zero_based_scoring():
    """测试：无能力 Agent 应该得 0 分"""
    empty_agent = DetectionData(
        platform="test",
        channels=[],
        # ... 其他全部 False
    )

    estimator = DimensionEstimatorV3(empty_agent)
    scores = estimator.estimate_all()

    assert scores.ES == 0
    assert scores.IS == 0
    assert scores.MS == 0
    assert scores.VS == 0
    assert scores.CE == 0
```

## 文档规范

### 文档类型

- **代码文档**：Docstrings
- **用户文档**：README.md, guides/
- **开发文档**：docs/, CONTRIBUTING.md
- **API 文档**：API.md

### 文档语言

- 代码注释：英文
- 用户文档：中文（主要）+ 英文（可选）
- 开发文档：中文

### 文档更新

- 功能变更时同步更新文档
- API 变更时更新 API 文档
- 版本发布时更新 CHANGELOG.md

## Pull Request 流程

1. 更新相关文档
2. 添加/更新测试
3. 运行测试确保通过
4. 创建 PR，描述变更内容
5. 等待代码审查
6. 根据反馈修改
7. 合并到主分支

## 问题处理

### 代码审查

- 所有 PR 必须通过审查
- 至少需要 1 位维护者批准
- CI 检查必须通过

### Issue 响应

- Bug 报告：48 小时内响应
- 功能请求：1 周内响应
- 代码审查：1 周内完成

## 发布流程

1. 更新版本号
2. 更新 CHANGELOG.md
3. 更新文档
4. 创建 Git tag
5. 发布 Release

## 联系方式

- GitHub Issues: [https://github.com/openclaw/eie-agent-evaluator/issues](https://github.com/openclaw/eie-agent-evaluator/issues)
- Email: eie-lab@openclaw.ai

---

再次感谢你的贡献！🙏
