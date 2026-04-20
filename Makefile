.PHONY: help install test clean run chat generate format lint all sync \
        info python-list python-install python-pin \
        update upgrade outdated \
        dev-tools check type-check security-check \
        clean-all clean-cache clean-build \
        docs serve \
        git-status git-hooks \
        benchmark profile

# 默认目标
.DEFAULT_GOAL := help

# 颜色定义
BLUE := \033[34m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

help:
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(RESET)"
	@echo "$(GREEN)  LangChain LLM Toolkit Makefile (使用 uv)$(RESET)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(RESET)"
	@echo ""
	@echo "$(YELLOW)使用方法:$(RESET) make [target]"
	@echo ""
	@echo "$(BLUE)📦 项目设置$(RESET)"
	@echo "  install         安装项目依赖（使用 uv）"
	@echo "  sync            同步依赖到虚拟环境"
	@echo "  env             创建 .env 文件（从 .env.example）"
	@echo "  lock            锁定依赖版本"
	@echo "  all             一键设置项目（清理 + 安装 + 配置）"
	@echo "  setup           同 all，一键设置项目"
	@echo ""
	@echo "$(BLUE)🐍 Python 管理$(RESET)"
	@echo "  python-list     查看可用的 Python 版本"
	@echo "  python-install  安装指定的 Python 版本（需要 VERSION 变量）"
	@echo "  python-pin      固定项目的 Python 版本（需要 VERSION 变量）"
	@echo "  python-info     显示当前 Python 环境信息"
	@echo ""
	@echo "$(BLUE)📦 依赖管理$(RESET)"
	@echo "  update          更新所有依赖到最新版本"
	@echo "  upgrade         同 update，更新所有依赖"
	@echo "  outdated        查看过时的依赖包"
	@echo "  list-deps       列出所有已安装的依赖"
	@echo "  tree            显示依赖树"
	@echo ""
	@echo "$(BLUE)🧪 测试$(RESET)"
	@echo "  test            运行所有测试"
	@echo "  test-llm        测试 LLM 集成"
	@echo "  test-rag        测试 RAG 系统"
	@echo "  test-doc        测试文档处理"
	@echo "  test-conversation 测试对话管理"
	@echo "  test-coverage   运行测试并生成覆盖率报告"
	@echo "  test-quick      快速测试（跳过慢速测试）"
	@echo ""
	@echo "$(BLUE)🚀 运行$(RESET)"
	@echo "  run             运行 CLI 工具（显示帮助）"
	@echo "  chat            进入聊天模式"
	@echo "  generate        生成文本（需要 PROMPT 变量）"
	@echo "  model-list      列出支持的模型"
	@echo ""
	@echo "$(BLUE)🌐 Web 界面$(RESET)"
	@echo "  web             启动 Web 界面（Streamlit）"
	@echo "  web-port        指定端口启动 Web 界面（需要 PORT 变量）"
	@echo "  web-external    允许外部访问启动 Web 界面"
	@echo ""
	@echo "$(BLUE)🚀 API 服务$(RESET)"
	@echo "  api             启动 FastAPI 服务"
	@echo "  api-port        指定端口启动 API 服务（需要 PORT 变量）"
	@echo "  api-external    允许外部访问启动 API 服务"
	@echo "  api-docs        打开 API 文档（Swagger UI）"
	@echo ""
	@echo "$(BLUE)🔧 代码质量$(RESET)"
	@echo "  format          格式化代码（使用 black）"
	@echo "  lint            代码检查（使用 flake8）"
	@echo "  type-check      类型检查（使用 mypy）"
	@echo "  security-check  安全检查（使用 bandit）"
	@echo "  check           运行所有检查（格式 + lint + 类型检查）"
	@echo "  dev-tools       安装开发工具（black, flake8, mypy, bandit）"
	@echo ""
	@echo "$(BLUE)🧹 清理$(RESET)"
	@echo "  clean           清理缓存和临时文件"
	@echo "  clean-all       深度清理（包括虚拟环境）"
	@echo "  clean-cache     仅清理缓存文件"
	@echo "  clean-build     清理构建文件"
	@echo ""
	@echo "$(BLUE)📊 信息和工具$(RESET)"
	@echo "  info            显示项目信息"
	@echo "  serve           启动开发服务器（如果有）"
	@echo "  docs            生成文档"
	@echo "  benchmark       运行性能基准测试"
	@echo "  profile         性能分析"
	@echo ""
	@echo "$(BLUE)🔧 Git 工具$(RESET)"
	@echo "  git-status      显示 Git 状态"
	@echo "  git-hooks       设置 Git hooks"
	@echo ""
	@echo "$(BLUE)示例:$(RESET)"
	@echo "  make install                    # 安装依赖"
	@echo "  make generate PROMPT='你好'     # 生成文本"
	@echo "  make python-install VERSION=3.12 # 安装 Python 3.12"
	@echo "  make test-coverage              # 运行测试并生成覆盖率报告"
	@echo ""

# ═══════════════════════════════════════════════════════════
# 项目设置
# ═══════════════════════════════════════════════════════════

install:
	@echo "$(GREEN)使用 uv 安装项目依赖...$(RESET)"
	uv sync
	@echo "$(GREEN)✓ 依赖安装完成！$(RESET)"

sync:
	@echo "$(GREEN)同步依赖到虚拟环境...$(RESET)"
	uv sync
	@echo "$(GREEN)✓ 同步完成！$(RESET)"

lock:
	@echo "$(GREEN)锁定依赖版本...$(RESET)"
	uv lock
	@echo "$(GREEN)✓ 依赖已锁定到 uv.lock！$(RESET)"

env:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)✓ 已创建 .env 文件，请编辑并设置你的 API 密钥$(RESET)"; \
	else \
		echo "$(YELLOW).env 文件已存在$(RESET)"; \
	fi

all: clean install env
	@echo "$(GREEN)✓ 项目设置完成！$(RESET)"
	@echo "$(YELLOW)请编辑 .env 文件并设置你的 API 密钥$(RESET)"

setup: all

# ═══════════════════════════════════════════════════════════
# Python 管理
# ═══════════════════════════════════════════════════════════

python-list:
	@echo "$(GREEN)可用的 Python 版本:$(RESET)"
	uv python list

python-install:
	@if [ -z "$(VERSION)" ]; then \
		echo "$(RED)错误: 请提供 VERSION 变量$(RESET)"; \
		echo "使用方法: make python-install VERSION=3.12"; \
		exit 1; \
	fi
	@echo "$(GREEN)安装 Python $(VERSION)...$(RESET)"
	uv python install $(VERSION)
	@echo "$(GREEN)✓ Python $(VERSION) 安装完成！$(RESET)"

python-pin:
	@if [ -z "$(VERSION)" ]; then \
		echo "$(RED)错误: 请提供 VERSION 变量$(RESET)"; \
		echo "使用方法: make python-pin VERSION=3.12"; \
		exit 1; \
	fi
	@echo "$(GREEN)固定项目 Python 版本为 $(VERSION)...$(RESET)"
	uv python pin $(VERSION)
	@echo "$(GREEN)✓ Python 版本已固定！$(RESET)"

python-info:
	@echo "$(GREEN)Python 环境信息:$(RESET)"
	@uv run python -c "import sys; print(f'Python 版本: {sys.version}'); print(f'虚拟环境: {sys.prefix}'); print(f'可执行文件: {sys.executable}')"

# ═══════════════════════════════════════════════════════════
# 依赖管理
# ═══════════════════════════════════════════════════════════

update:
	@echo "$(GREEN)更新所有依赖到最新版本...$(RESET)"
	uv sync --upgrade
	@echo "$(GREEN)✓ 依赖已更新！$(RESET)"

upgrade: update

outdated:
	@echo "$(GREEN)检查过时的依赖包...$(RESET)"
	uv pip list --outdated

list-deps:
	@echo "$(GREEN)已安装的依赖:$(RESET)"
	@uv run pip list

tree:
	@echo "$(GREEN)依赖树:$(RESET)"
	@uv run pip list --format=freeze | head -30

# ═══════════════════════════════════════════════════════════
# 测试
# ═══════════════════════════════════════════════════════════

test:
	@echo "$(GREEN)运行所有测试...$(RESET)"
	PYTHONWARNINGS="ignore::DeprecationWarning" uv run pytest -v
	@echo "$(GREEN)✓ 所有测试完成！$(RESET)"

test-llm:
	@echo "$(GREEN)测试 LLM 集成...$(RESET)"
	uv run python -c "from langchain_llm_toolkit.llm_integration import main; main()"

test-rag:
	@echo "$(GREEN)测试 RAG 系统...$(RESET)"
	uv run python -c "from langchain_llm_toolkit.rag import main; main()"

test-doc:
	@echo "$(GREEN)测试文档处理...$(RESET)"
	uv run python -m pytest tests/test_document_processing.py -v

test-conversation:
	@echo "$(GREEN)测试对话管理...$(RESET)"
	uv run python -c "from langchain_llm_toolkit.conversation import main; main()"

test-coverage:
	@echo "$(GREEN)运行测试并生成覆盖率报告...$(RESET)"
	uv run pytest --cov=. --cov-report=html --cov-report=term
	@echo "$(GREEN)✓ 覆盖率报告已生成到 htmlcov/$(RESET)"

test-quick:
	@echo "$(GREEN)快速测试（跳过慢速测试）...$(RESET)"
	uv run pytest -v -m "not slow"

# ═══════════════════════════════════════════════════════════
# 运行
# ═══════════════════════════════════════════════════════════

run:
	@echo "$(GREEN)运行 CLI 工具...$(RESET)"
	uv run langchain-cli --help

chat:
	@echo "$(GREEN)进入聊天模式...$(RESET)"
	uv run langchain-cli chat

generate:
	@if [ -z "$(PROMPT)" ]; then \
		echo "$(RED)错误: 请提供 PROMPT 变量$(RESET)"; \
		echo "使用方法: make generate PROMPT='你的提示'"; \
		exit 1; \
	fi
	@echo "$(GREEN)生成文本...$(RESET)"
	uv run langchain-cli generate "$(PROMPT)"

model-list:
	@echo "$(GREEN)支持的模型列表:$(RESET)"
	uv run langchain-cli model list

# ═══════════════════════════════════════════════════════════
# 代码质量
# ═══════════════════════════════════════════════════════════

dev-tools:
	@echo "$(GREEN)安装开发工具...$(RESET)"
	uv add --dev black flake8 mypy bandit pytest pytest-cov
	@echo "$(GREEN)✓ 开发工具安装完成！$(RESET)"

format:
	@echo "$(GREEN)格式化代码...$(RESET)"
	uv run black . --line-length 100
	@echo "$(GREEN)✓ 代码格式化完成！$(RESET)"

lint:
	@echo "$(GREEN)代码检查...$(RESET)"
	uv run flake8 . --max-line-length 100 --exclude=.venv,.git,__pycache__,venv
	@echo "$(GREEN)✓ 代码检查完成！$(RESET)"

type-check:
	@echo "$(GREEN)类型检查...$(RESET)"
	uv run mypy . --ignore-missing-imports
	@echo "$(GREEN)✓ 类型检查完成！$(RESET)"

security-check:
	@echo "$(GREEN)安全检查...$(RESET)"
	@uv run bandit *.py models/*.py config/*.py -ll || true
	@echo "$(GREEN)✓ 安全检查完成！$(RESET)"

check: format lint type-check
	@echo "$(GREEN)✓ 所有检查完成！$(RESET)"

# ═══════════════════════════════════════════════════════════
# 清理
# ═══════════════════════════════════════════════════════════

clean:
	@echo "$(GREEN)清理缓存和临时文件...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	rm -rf .pytest_cache 2>/dev/null || true
	rm -rf .mypy_cache 2>/dev/null || true
	rm -rf .coverage 2>/dev/null || true
	rm -rf htmlcov 2>/dev/null || true
	@echo "$(GREEN)✓ 清理完成！$(RESET)"

clean-all: clean
	@echo "$(GREEN)深度清理（包括虚拟环境）...$(RESET)"
	rm -rf .venv 2>/dev/null || true
	rm -rf venv 2>/dev/null || true
	@echo "$(GREEN)✓ 深度清理完成！$(RESET)"

clean-cache:
	@echo "$(GREEN)清理缓存文件...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache 2>/dev/null || true
	rm -rf .mypy_cache 2>/dev/null || true
	@echo "$(GREEN)✓ 缓存清理完成！$(RESET)"

clean-build:
	@echo "$(GREEN)清理构建文件...$(RESET)"
	rm -rf build 2>/dev/null || true
	rm -rf dist 2>/dev/null || true
	rm -rf *.egg-info 2>/dev/null || true
	@echo "$(GREEN)✓ 构建文件清理完成！$(RESET)"

# ═══════════════════════════════════════════════════════════
# 信息和工具
# ═══════════════════════════════════════════════════════════

info:
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(RESET)"
	@echo "$(GREEN)  项目信息$(RESET)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(RESET)"
	@echo ""
	@echo "$(YELLOW)项目名称:$(RESET) LangChain LLM Toolkit"
	@echo "$(YELLOW)描述:$(RESET) 基于 LangChain 和 LiteLLM 的 LLM 应用框架"
	@echo "$(YELLOW)Python 版本:$(RESET) $(shell uv run python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')"
	@echo "$(YELLOW)虚拟环境:$(RESET) .venv/"
	@echo "$(YELLOW)包管理器:$(RESET) uv"
	@echo ""
	@echo "$(YELLOW)已安装的包:$(RESET) $(shell uv pip list 2>/dev/null | wc -l | tr -d ' ')"
	@echo ""
	@echo "$(YELLOW)项目结构:$(RESET)"
	@ls -1 | head -10
	@echo ""
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(RESET)"

serve:
	@echo "$(GREEN)启动开发服务器...$(RESET)"
	@echo "$(YELLOW)注意: 此项目暂无 Web 服务器$(RESET)"

docs:
	@echo "$(GREEN)生成文档...$(RESET)"
	@echo "$(YELLOW)注意: 需要配置文档生成工具$(RESET)"

benchmark:
	@echo "$(GREEN)运行性能基准测试...$(RESET)"
	@echo "$(YELLOW)注意: 需要创建基准测试脚本$(RESET)"

profile:
	@echo "$(GREEN)性能分析...$(RESET)"
	@echo "$(YELLOW)注意: 需要配置性能分析工具$(RESET)"

# ═══════════════════════════════════════════════════════════
# Git 工具
# ═══════════════════════════════════════════════════════════

git-status:
	@echo "$(GREEN)Git 状态:$(RESET)"
	@git status -s

git-hooks:
	@echo "$(GREEN)设置 Git hooks...$(RESET)"
	@echo "$(YELLOW)注意: 需要创建 .git/hooks/ 目录和 hook 脚本$(RESET)"

# ═══════════════════════════════════════════════════════════
# 快捷命令
# ═══════════════════════════════════════════════════════════

# 快速开发流程
dev: install test
	@echo "$(GREEN)✓ 开发环境准备完成！$(RESET)"

# 快速检查和提交
ci: check test
	@echo "$(GREEN)✓ CI 检查完成！$(RESET)"

# 快速重置
reset: clean-all install
	@echo "$(GREEN)✓ 项目已重置！$(RESET)"

# ═══════════════════════════════════════════════════════════
# Web 界面
# ═══════════════════════════════════════════════════════════

web:
	@echo "$(GREEN)启动 Web 界面...$(RESET)"
	@echo "$(YELLOW)访问地址: http://localhost:8501$(RESET)"
	uv run streamlit run src/langchain_llm_toolkit/app.py

web-port:
	@if [ -z "$(PORT)" ]; then \
		echo "$(RED)错误: 请提供 PORT 变量$(RESET)"; \
		echo "使用方法: make web-port PORT=8080"; \
		exit 1; \
	fi
	@echo "$(GREEN)启动 Web 界面（端口: $(PORT)）...$(RESET)"
	@echo "$(YELLOW)访问地址: http://localhost:$(PORT)$(RESET)"
	uv run streamlit run src/langchain_llm_toolkit/app.py --server.port $(PORT)

web-external:
	@echo "$(GREEN)启动 Web 界面（允许外部访问）...$(RESET)"
	@echo "$(YELLOW)访问地址: http://0.0.0.0:8501$(RESET)"
	uv run streamlit run src/langchain_llm_toolkit/app.py --server.address 0.0.0.0

# ═══════════════════════════════════════════════════════════
# API 服务
# ═══════════════════════════════════════════════════════════

api:
	@echo "$(GREEN)启动 FastAPI 服务...$(RESET)"
	@echo "$(YELLOW)API 地址: http://localhost:8000$(RESET)"
	@echo "$(YELLOW)API 文档: http://localhost:8000/docs$(RESET)"
	@echo "$(YELLOW)ReDoc 文档: http://localhost:8000/redoc$(RESET)"
	uv run langchain-api

api-port:
	@if [ -z "$(PORT)" ]; then \
		echo "$(RED)错误: 请提供 PORT 变量$(RESET)"; \
		echo "使用方法: make api-port PORT=8080"; \
		exit 1; \
	fi
	@echo "$(GREEN)启动 FastAPI 服务（端口: $(PORT)）...$(RESET)"
	@echo "$(YELLOW)API 地址: http://localhost:$(PORT)$(RESET)"
	@echo "$(YELLOW)API 文档: http://localhost:$(PORT)/docs$(RESET)"
	uv run langchain-api --port $(PORT)

api-external:
	@echo "$(GREEN)启动 FastAPI 服务（允许外部访问）...$(RESET)"
	@echo "$(YELLOW)API 地址: http://0.0.0.0:8000$(RESET)"
	@echo "$(YELLOW)API 文档: http://0.0.0.0:8000/docs$(RESET)"
	uv run langchain-api --host 0.0.0.0

api-docs:
	@echo "$(GREEN)打开 API 文档...$(RESET)"
	@if command -v open >/dev/null 2>&1; then \
		open http://localhost:8000/docs; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open http://localhost:8000/docs; \
	else \
		echo "$(YELLOW)请手动打开: http://localhost:8000/docs$(RESET)"; \
	fi

