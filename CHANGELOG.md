# 更新日志

本项目的所有重要更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 新增
- 待添加的新功能

### 变更
- 待变更的内容

### 修复
- 待修复的问题

## [0.1.0] - 2026-04-13

### 新增

#### 核心功能
- ✨ LLM 集成模块 (`llm_integration.py`)
  - 支持多种 AI 模型（OpenAI, Anthropic, Google, Ollama）
  - 统一的文本生成接口
  - 聊天对话功能
  - 流式生成支持（Ollama）
  - 模型和温度参数管理

- ✨ 对话管理模块 (`conversation.py`)
  - 多轮对话历史管理
  - 自动上下文维护
  - 对话历史持久化

- ✨ RAG 系统 (`rag.py`)
  - 文档加载和处理
  - 向量存储管理（FAISS, Qdrant）
  - 文档检索和问答
  - 支持多种文档格式（PDF, TXT, DOCX）

- ✨ 文档加载器 (`document_loader.py`)
  - 多格式文档加载
  - 自动编码检测
  - 元数据提取

- ✨ 文本分割器 (`text_splitter.py`)
  - 智能文本分割
  - 可配置的分割参数
  - 支持多种分割策略

- ✨ 提示模板 (`prompt_templates.py`)
  - 预定义的提示模板
  - 自定义模板支持

#### CLI 工具
- 🛠️ 完整的命令行界面 (`cli.py`)
  - `generate` - 文本生成命令
  - `chat` - 交互式聊天模式
  - `model` - 模型管理命令
  - `temperature` - 温度参数管理

#### Web 和 API 服务
- 🌐 FastAPI 服务 (`api.py`)
  - RESTful API 接口
  - 自动 API 文档（Swagger）
  - 请求验证和错误处理

- 🖥️ Streamlit Web 应用 (`app.py`)
  - 友好的 Web 界面
  - 实时对话
  - 文档上传和问答

#### 开发工具
- 📦 完整的 Makefile
  - 一键安装和设置
  - 测试和覆盖率报告
  - 代码格式化和检查
  - 安全检查

- 🧪 测试套件
  - 259 个单元测试
  - 85% 测试覆盖率
  - 完整的测试文档

- 📝 文档
  - 详细的 README.md
  - OpenClaw 龙虾助理使用指南
  - 快速参考文档
  - API 对比分析文档

#### 配置和安全
- ⚙️ 配置管理
  - 环境变量支持
  - Pydantic 配置验证
  - 多环境配置

- 🔒 安全特性
  - API 密钥环境变量管理
  - 安全检查工具集成
  - 完整的安全审计报告

### 文档

#### 新增文档
- 📚 README.md - 完整的项目文档
- 📚 CONTRIBUTING.md - 贡献指南
- 📚 CODE_OF_CONDUCT.md - 行为准则
- 📚 SECURITY.md - 安全政策
- 📚 LICENSE - MIT 许可证
- 📚 OPENCLAW_GUIDE.md - OpenClaw 使用指南
- 📚 QUICK_REFERENCE.md - 快速参考
- 📚 AI_VS_RAG_COMPARISON.md - AI vs RAG 对比分析
- 📚 OPENCLAW_PROJECT_GUIDE.md - OpenClaw 项目建议
- 📚 SECURITY_AUDIT.md - 安全审计报告
- 📚 RENAME_SUMMARY.md - 项目重命名总结

### 开发工具

#### 代码质量
- 🎨 Black 代码格式化
- 🔍 Flake8 代码检查
- 📝 MyPy 类型检查
- 🛡️ Bandit 安全检查
- 📦 isort 导入排序

#### CI/CD
- 🚀 GitHub Actions 工作流
  - 多 Python 版本测试
  - 自动化测试
  - 安全检查
  - 构建验证

#### Pre-commit Hooks
- 🪝 自动代码格式化
- 🪝 代码检查
- 🪝 类型检查
- 🪝 安全检查

### 变更
- 🔄 项目重命名：`langchain-project` → `langchain-llm-toolkit`
- 🔄 更新项目描述，更准确地反映项目定位

### 优化
- ⚡ 提升测试覆盖率从 71% 到 85%
- ⚡ 添加 51 个新测试用例
- ⚡ 修复所有类型检查错误
- ⚡ 优化代码结构和文档

### 修复
- 🐛 修复 FAISS 向量存储删除集合问题
- 🐛 修复文档加载器文件扩展名处理
- 🐛 修复类型注解问题
- 🐛 修复测试中的断言错误

## 版本说明

### 版本号规则

我们遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范：

- **主版本号（MAJOR）**: 不兼容的 API 变更
- **次版本号（MINOR）**: 向后兼容的功能新增
- **修订号（PATCH）**: 向后兼容的问题修复

### 更新类型

- **新增**: 新功能
- **变更**: 现有功能的变更
- **弃用**: 即将移除的功能
- **移除**: 已移除的功能
- **修复**: Bug 修复
- **安全**: 安全相关的修复

## 路线图

### v0.2.0（计划中）

#### 新增
- [ ] 支持更多 LLM 提供商
- [ ] 改进的 RAG 检索算法
- [ ] Web UI 增强
- [ ] 更多文档格式支持

#### 优化
- [ ] 性能优化
- [ ] 内存使用优化
- [ ] 更好的错误处理

### v0.3.0（计划中）

#### 新增
- [ ] 多语言支持
- [ ] 插件系统
- [ ] 高级分析功能

## 贡献

如果您想为项目做出贡献，请查看 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

**最后更新**: 2026-04-13  
**当前版本**: 0.1.0

[Unreleased]: https://github.com/yourusername/langchain-llm-toolkit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/langchain-llm-toolkit/releases/tag/v0.1.0
