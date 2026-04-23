# Security Policy

## Supported Versions

| Version | Supported |
|---------|------------|
| 3.3.x | :white_check_mark: Yes |
| 3.2.x | :white_check_mark: Yes |
| 3.1.x | :white_check_mark: Yes |
| < 3.1.0 | :x: No |

## Reporting a Vulnerability

如果你发现了安全漏洞，请遵循以下步骤报告：

### 📧 私密报告

1. **不要公开 Issue** - 安全问题应该在修复前保密
2. **发送邮件到**：security@openclaw.ai
3. **邮件内容应包括**：
   - 漏洞描述
   - 影响范围
   - 复现步骤
   - 建议的修复方案（可选）

### 📋 报告流程

1. 收到报告后，我们会在 **48 小时内**确认收到
2. 我们会在 **7 天内** 评估漏洞并确定修复计划
3. 修复完成后，我们会协调发布时间
4. 发布安全补丁时，会同时在 Security Advisories 中发布通知

### 🏆 致谢

安全漏洞的发现者会在 CHANGELOG 中被致谢（如果你愿意公开的话）。

## 安全最佳实践

### 使用本项目时

1. **定期更新**：保持使用最新版本
2. **审查依赖**：定期检查依赖项的安全性
3. **限制权限**：不要以 root 权限运行
4. **隔离环境**：使用虚拟环境或容器

### 开发本项目时

1. **代码审查**：所有代码必须经过审查
2. **自动化测试**：确保测试覆盖率 > 80%
3. **依赖扫描**：使用工具扫描依赖漏洞
4. **安全测试**：定期进行安全审计

## 安全配置

### OpenClaw 安全建议

在使用 EIE Agent Evaluator 评估 OpenClaw 时：

1. **配置访问控制**：
   ```yaml
   safety:
     allowlist:
       - user@example.com
   ```

2. **启用审计日志**：
   ```yaml
   safety:
     audit: true
   ```

3. **配置内容过滤**：
   ```yaml
   safety:
     content_filter:
       enabled: true
   ```

## 已知安全问题

### v3.2.0 及以下版本

- **问题**：零基评分法未完全实现，存在基础分
- **影响**：评估结果可能虚高
- **修复**：升级到 v3.3.0

详见 [CHANGELOG.md](CHANGELOG.md#330---2026-04-22)

## 联系方式

- 安全邮件：security@openclaw.ai
- GitHub Issues：[https://github.com/openclaw/eie-agent-evaluator/security](https://github.com/openclaw/eie-agent-evaluator/security)

---

**我们致力于维护一个安全的开源项目。感谢你的帮助！**
