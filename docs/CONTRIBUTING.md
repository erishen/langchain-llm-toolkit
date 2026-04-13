# 贡献指南

感谢您有兴趣为 LangChain LLM Toolkit 做出贡献！我们欢迎所有形式的贡献。

## 📋 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发流程](#开发流程)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [测试要求](#测试要求)
- [文档规范](#文档规范)

## 行为准则

本项目采用贡献者公约作为行为准则。参与此项目即表示您同意遵守其条款。请阅读 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) 了解详情。

## 如何贡献

### 报告 Bug

如果您发现了 bug，请通过 [GitHub Issues](https://github.com/yourusername/langchain-llm-toolkit/issues) 提交报告。

提交 Bug 报告时，请包含：

1. **清晰的标题**：简明扼要地描述问题
2. **详细描述**：包括您期望发生的情况和实际发生的情况
3. **复现步骤**：提供详细的步骤让我们能够复现问题
4. **环境信息**：
   - 操作系统和版本
   - Python 版本
   - 相关依赖版本
5. **日志输出**：如果有错误日志，请提供完整输出
6. **截图**：如果适用，添加截图帮助解释问题

### 建议新功能

我们欢迎新功能建议！请通过 [GitHub Issues](https://github.com/yourusername/langchain-llm-toolkit/issues) 提交。

建议新功能时，请包含：

1. **功能描述**：清晰详细地描述您希望添加的功能
2. **使用场景**：说明这个功能如何使用，解决什么问题
3. **示例代码**：如果可能，提供示例代码展示如何使用
4. **替代方案**：描述您考虑过的其他解决方案

### 提交代码

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 开发流程

### 环境设置

```bash
# 克隆仓库
git clone https://github.com/yourusername/langchain-llm-toolkit.git
cd langchain-llm-toolkit

# 安装依赖
make install

# 设置环境变量
cp .env.example .env
# 编辑 .env 文件，填入必要的配置

# 运行测试
make test
```

### 开发工作流

1. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

2. **编写代码**
   - 遵循代码规范
   - 添加必要的测试
   - 更新相关文档

3. **运行测试**
   ```bash
   make test
   make test-coverage
   ```

4. **代码检查**
   ```bash
   make check
   ```

5. **提交更改**
   ```bash
   git add .
   git commit -m "type: description"
   ```

6. **推送并创建 PR**
   ```bash
   git push origin your-branch-name
   ```

## 代码规范

### Python 代码规范

我们遵循以下规范：

- **PEP 8**: Python 代码风格指南
- **Black**: 代码格式化工具（行长度 100）
- **isort**: 导入排序
- **MyPy**: 类型检查

### 格式化代码

```bash
# 格式化代码
make format

# 检查代码风格
make lint

# 类型检查
make type-check
```

### 代码质量要求

- ✅ 所有代码必须通过 `make check` 检查
- ✅ 测试覆盖率不低于 80%
- ✅ 没有类型检查错误
- ✅ 没有安全漏洞警告

### 文档字符串

使用 Google 风格的文档字符串：

```python
def function_name(param1: str, param2: int) -> bool:
    """函数简短描述。

    更详细的描述，说明函数的作用。

    Args:
        param1: 第一个参数的说明
        param2: 第二个参数的说明

    Returns:
        返回值的说明

    Raises:
        ValueError: 何时会抛出此异常

    Example:
        >>> function_name("test", 42)
        True
    """
    pass
```

## 提交规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

### 提交消息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型（type）

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响代码运行的变动）
- `refactor`: 重构（既不是新增功能，也不是修改 bug）
- `perf`: 性能优化
- `test`: 增加测试
- `chore`: 构建过程或辅助工具的变动
- `revert`: 回退
- `ci`: CI/CD 相关

### 示例

```bash
# 新功能
git commit -m "feat: 添加流式生成功能"

# Bug 修复
git commit -m "fix: 修复空输入导致的崩溃问题"

# 文档更新
git commit -m "docs: 更新 API 使用文档"

# 重构
git commit -m "refactor: 重构 LLM 集成模块"
```

## 测试要求

### 运行测试

```bash
# 运行所有测试
make test

# 运行特定测试
uv run pytest test_llm_integration.py -v

# 运行测试并生成覆盖率报告
make test-coverage
```

### 测试规范

1. **测试文件命名**: `test_*.py`
2. **测试类命名**: `Test*`
3. **测试方法命名**: `test_*`
4. **测试覆盖率**: 新代码覆盖率不低于 80%

### 测试示例

```python
import unittest
from llm_integration import LLMIntegration


class TestLLMIntegration(unittest.TestCase):
    def setUp(self):
        """测试前准备"""
        self.llm = LLMIntegration()

    def test_generate_success(self):
        """测试成功生成文本"""
        response = self.llm.generate("Hello")
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)

    def tearDown(self):
        """测试后清理"""
        pass
```

## 文档规范

### README.md

- 保持简洁明了
- 包含安装、使用、配置说明
- 提供示例代码
- 包含常见问题

### API 文档

- 使用 Google 风格文档字符串
- 包含参数、返回值、异常说明
- 提供使用示例

### 更新日志

在 `CHANGELOG.md` 中记录所有重要更改：

```markdown
## [Unreleased]

### Added
- 新增功能描述

### Changed
- 变更描述

### Fixed
- 修复描述
```

## Pull Request 指南

### PR 标题

使用与提交消息相同的格式：

```
type: description
```

### PR 描述模板

```markdown
## 变更类型
- [ ] Bug 修复
- [ ] 新功能
- [ ] 重构
- [ ] 文档更新
- [ ] 其他

## 描述
清晰描述您的更改

## 相关 Issue
关闭 #issue_number

## 测试
描述您如何测试这些更改

## 检查清单
- [ ] 代码遵循项目规范
- [ ] 已添加测试
- [ ] 所有测试通过
- [ ] 文档已更新
- [ ] 提交消息符合规范
```

### 代码审查

所有 PR 都需要至少一位维护者审查。我们会尽快处理您的 PR。

## 获取帮助

- **GitHub Issues**: 提交问题或建议
- **文档**: 查看 [README.md](../README.md) 和其他文档
- **讨论**: 在 GitHub Discussions 中参与讨论

## 许可证

通过贡献代码，您同意您的贡献将按照 MIT 许可证授权。

---

再次感谢您的贡献！🎉
