# 安全政策

## 支持的版本

目前我们正在为以下版本提供安全更新：

| 版本 | 支持状态 |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## 报告漏洞

如果您发现了安全漏洞，请**不要**通过公开的 GitHub Issues 报告。

### 如何报告

请通过以下方式私下报告安全漏洞：

1. **发送邮件至**: [在此处填写安全邮箱]
2. **使用 GitHub Security Advisories**: 
   - 访问项目的 [Security Advisories](https://github.com/yourusername/langchain-llm-toolkit/security/advisories)
   - 点击 "Report a vulnerability"

### 报告内容

请在报告中包含以下信息：

- **漏洞类型**: 例如 SQL 注入、XSS、认证绕过等
- **影响范围**: 受影响的功能和版本
- **复现步骤**: 详细描述如何复现漏洞
- **概念验证**: 如果可能，提供 PoC 代码
- **影响评估**: 漏洞可能造成的影响
- **建议修复**: 如果有修复建议，请提供

### 响应时间

我们承诺：

- **确认收到**: 24 小时内确认收到您的报告
- **初步评估**: 3 个工作日内提供初步评估
- **修复时间**: 根据严重程度，我们将在以下时间内修复：
  - 严重漏洞: 7 天内
  - 高危漏洞: 14 天内
  - 中危漏洞: 30 天内
  - 低危漏洞: 下一个版本发布时

### 披露政策

我们遵循**负责任的披露**原则：

1. **私下修复**: 我们会私下修复漏洞并准备发布
2. **协调披露**: 在发布修复版本后，我们会：
   - 发布安全公告
   - 在 CHANGELOG 中记录修复
   - 感谢报告者（如果他们愿意）
3. **公开披露**: 修复版本发布后，漏洞详情将被公开

## 安全最佳实践

### API 密钥管理

**重要**: 请勿在代码中硬编码 API 密钥或其他敏感信息。

#### 正确做法

```python
# ✅ 从环境变量读取
import os
api_key = os.getenv("OPENAI_API_KEY")

# ✅ 使用配置文件
from config import settings
api_key = settings.OPENAI_API_KEY
```

#### 错误做法

```python
# ❌ 不要硬编码
api_key = "sk-xxxxx"  # 危险！

# ❌ 不要提交到版本控制
# config.py
API_KEY = "sk-xxxxx"  # 危险！
```

### 环境变量配置

1. 复制 `.env.example` 为 `.env`
2. 填入您的 API 密钥
3. 确保 `.env` 已加入 `.gitignore`

```bash
# .env.example
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
```

### 依赖安全

我们使用以下工具确保依赖安全：

- **pip-audit**: 检查依赖漏洞
- **safety**: 检查已知安全漏洞
- **dependabot**: 自动更新依赖

定期运行：

```bash
# 检查依赖漏洞
make security-check

# 或手动运行
uv run pip-audit
uv run safety check
```

### 代码安全

我们使用以下工具进行代码安全检查：

- **bandit**: Python 代码安全检查
- **semgrep**: 高级代码分析
- **CodeQL**: GitHub 代码扫描

定期运行：

```bash
# 运行安全检查
make security-check

# 或手动运行
uv run bandit -r . -ll
```

## 安全配置建议

### 生产环境

在生产环境中，请确保：

1. **API 密钥安全**
   - 使用密钥管理服务（AWS Secrets Manager, Azure Key Vault 等）
   - 定期轮换密钥
   - 使用最小权限原则

2. **网络安全**
   - 使用 HTTPS
   - 配置防火墙规则
   - 启用速率限制

3. **日志和监控**
   - 不要记录敏感信息
   - 监控异常访问
   - 设置告警

4. **访问控制**
   - 实施身份验证
   - 使用授权机制
   - 定期审查访问权限

### 开发环境

在开发环境中：

1. **不要使用生产密钥**
   - 使用开发/测试环境的密钥
   - 或使用模拟服务

2. **本地配置**
   - 使用 `.env` 文件
   - 确保 `.env` 不被提交

3. **代码审查**
   - 提交前检查是否有敏感信息
   - 使用 pre-commit hooks

## 已知安全问题

目前没有已知的未修复安全问题。

## 安全更新历史

### 2026-04-13
- 初始安全政策发布
- 添加安全最佳实践文档

## 联系方式

如果您有任何安全问题或疑问，请联系：

- **安全邮箱**: [在此处填写安全邮箱]
- **GitHub Security**: [Security Advisories](https://github.com/yourusername/langchain-llm-toolkit/security/advisories)

## 致谢

我们感谢所有负责任地报告安全漏洞的研究人员和用户。您的帮助使我们的项目更加安全。

---

**最后更新**: 2026-04-13  
**安全政策版本**: 1.0
