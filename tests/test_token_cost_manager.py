"""
Tests for Token Cost Manager.
Token 成本管理器测试
"""

from datetime import datetime

from langchain_llm_toolkit.token_cost_manager import (
    CostEstimator,
    CostReport,
    ModelPricing,
    TokenCostManager,
    TokenCounter,
    TokenUsage,
)


class TestModelPricing:
    """测试模型定价"""

    def test_default_pricing(self):
        """测试默认定价"""
        pricing = ModelPricing(input_price=1.0, output_price=2.0)
        assert pricing.input_price == 1.0
        assert pricing.output_price == 2.0
        assert pricing.currency == "USD"


class TestTokenUsage:
    """测试 Token 使用"""

    def test_create_usage(self):
        """测试创建使用记录"""
        usage = TokenUsage(
            model="gpt-4o",
            input_tokens=100,
            output_tokens=50,
            cost=0.01,
            timestamp=datetime.now(),
        )
        assert usage.model == "gpt-4o"
        assert usage.input_tokens == 100
        assert usage.output_tokens == 50
        assert usage.request_type == "chat"


class TestCostReport:
    """测试成本报告"""

    def test_empty_report(self):
        """测试空报告"""
        report = CostReport()
        assert report.total_requests == 0
        assert report.total_input_tokens == 0
        assert report.total_output_tokens == 0
        assert report.total_cost == 0


class TestTokenCounter:
    """测试 Token 计数器"""

    def test_count_tokens_default(self):
        """测试默认计数"""
        counter = TokenCounter()
        text = "Hello, world!"
        count = counter.count_tokens(text)
        assert count > 0

    def test_count_tokens_empty(self):
        """测试空文本"""
        counter = TokenCounter()
        count = counter.count_tokens("")
        assert count == 0

    def test_count_tokens_chinese(self):
        """测试中文文本"""
        counter = TokenCounter()
        text = "你好，世界！"
        count = counter.count_tokens(text)
        assert count > 0

    def test_count_tokens_with_model(self):
        """测试指定模型"""
        counter = TokenCounter()
        text = "Hello, world!"
        count = counter.count_tokens(text, model="gpt-4o")
        assert count > 0


class TestCostEstimator:
    """测试成本估算器"""

    def test_estimate_cost(self):
        """测试估算成本"""
        estimator = CostEstimator()
        cost = estimator.estimate_cost(
            input_tokens=1000,
            output_tokens=500,
            model="gpt-4o",
        )
        assert cost > 0

    def test_estimate_cost_deepseek(self):
        """测试 DeepSeek 模型"""
        estimator = CostEstimator()
        cost = estimator.estimate_cost(
            input_tokens=1000,
            output_tokens=500,
            model="deepseek-chat",
        )
        assert cost > 0


class TestTokenCostManager:
    """测试 Token 成本管理器"""

    def test_init(self):
        """测试初始化"""
        manager = TokenCostManager()
        assert manager is not None

    def test_record_usage(self):
        """测试记录使用"""
        manager = TokenCostManager()
        manager.record_usage(
            model="gpt-4o",
            input_tokens=100,
            output_tokens=50,
        )
        report = manager.get_report()
        assert report.total_requests == 1

    def test_get_report(self):
        """测试获取报告"""
        manager = TokenCostManager()
        manager.record_usage(
            model="gpt-4o",
            input_tokens=100,
            output_tokens=50,
        )
        report = manager.get_report()
        assert report.total_cost > 0
