# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.3.0] - 2026-04-22

### Added
- 🆕 真正零基评分法：移除所有基础分
- 🆕 VS 漏洞惩罚分级机制（P0/P1/P2）
- 🆕 IS 维度加权平均算法
- 🆕 新系统 7 天保护期
- 🆕 RAG 实际使用检测

### Changed
- 🔧 ES 持久化存储评分：从"基础分10分"改为"完全靠实际使用"
- 🔧 IS 维度评分逻辑：从"乘积"改为"加权平均"
- 🔧 VS 漏洞惩罚：从"固定-15分"改为"分级惩罚"
- 🔧 质量调整系数：从 0.3 改为 0.5
- 🔧 降级方案：移除基础分，统一零基评分

### Fixed
- 🐛 【P0-1】零基评分法声明与代码不一致
- 🐛 【P0-2】IS 维度乘积逻辑导致指数级降低得分
- 🐛 【P0-3】VS 维度漏洞惩罚过于严厉
- 🐛 【P0-4】质量调整系数过于严厉，新系统无保护期
- 🐛 【P2-1】降级方案仍有基础分

### Performance
- ⚡ IS 维度评分提升 56%（使用率50%×质量80%场景）
- ⚡ 新系统惩罚降低 33%（从 70% 降至 50%）

### Documentation
- 📝 添加 v3.3.0 优化报告
- 📝 添加自动化测试脚本
- 📝 添加简化验证脚本

## [3.2.0] - 2026-04-22

### Added
- 🆕 零基评分法：无基础分，全部靠实际能力挣分
- 🆕 质量系数：实际效果 / 配置存在
- 🆕 维度分数上限配置

### Changed
- 🔧 ES 评分：移除基础分 30 分
- 🔧 IS 评分：移除基础分 20 分
- 🔧 MS 评分：模型潜力 × 实际调度能力
- 🔧 VS 评分：移除基础分 40 分
- 🔧 CE 评分：移除基础分 20 分

### Fixed
- 🐛 修复基础分设计缺陷
- 🐛 修复"僵尸 Agent" 得分问题

### Performance
- ⚡ 空白系统评分从 30.5 降至 6.2
- ⚡ OpenClaw 评分从 46.3 降至 25.2

## [3.1.0] - 2026-04-22

### Added
- 🆕 质量评估器 `quality_estimator.py`
- 🆕 行为测试器 `behavior_tester.py`
- 🆕 反馈闭环检测
- 🆕 记忆使用率检测
- 🆕 Skills 有效性检测
- 🆕 错误改进率检测
- 🆕 进化产出数量检测

### Changed
- 🔧 IS 评分：从"Memory 存在"改为"Memory 使用率"
- 🔧 MS 评分：从"Skills 数量"改为"有效 Skills"
- 🔧 CE 评分：从"配置存在"改为"成长记录"
- 🔧 VS 评分：从"配置存在"改为"反馈闭环"

### Fixed
- 🐛 修复"配置存在 ≠ 实际能力"问题
- 🐛 修复"数量堆砌 ≠ 能力"问题

### Documentation
- 📝 创建错误记录模板
- 📝 创建进化产出模板
- 📝 创建情报记录模板

## [3.0.0] - 2026-04-22

### Added
- 🎉 初始版本发布
- 📊 MEQ 评分系统
- 📊 五维度模型（ES/IS/MS/VS/CE）
- 📊 VL 等级判定（VL0-VL5）
- 🔍 自动检测功能（OpenClaw/Hermes）
- 🧮 交互式评估
- 🧮 批量评估
- 🧮 系统类型估算

### Documentation
- 📝 SKILL.md 定义
- 📝 核心公式说明
- 📝 VL 等级定义
- 📝 典型系统参照表

---

## [Unreleased]

### Planned
- [ ] 实现 RAG 实际效果检测（召回率/准确率）
- [ ] 改进 VS 访问控制判断逻辑
- [ ] 增加单元测试覆盖率
- [ ] 支持更多平台（LangChain, AutoGen）
- [ ] Web UI 界面
- [ ] 可视化报告生成

---

## 维护策略

### 版本号规则
- **主版本号（Major）**：不兼容的 API 变更
- **次版本号（Minor）**：向下兼容的功能新增
- **修订号（Patch）**：向下兼容的问题修复

### 发布周期
- 每月发布一个次版本号（Minor）
- 随时发布修订号（Patch）修复紧急问题
- 主版本号（Major）根据重大变更发布

### 支持策略
- 当前版本 + 前 2 个次版本号：完全支持
- 更早版本：安全补丁支持
- 不再支持的版本：建议升级
