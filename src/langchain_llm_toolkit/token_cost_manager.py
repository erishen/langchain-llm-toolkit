"""
Token Cost Manager - Token 成本管理器
优化 LLM API 调用成本
"""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ModelPricing:
    """模型定价信息"""

    input_price: float  # 每百万 token 输入价格 (USD)
    output_price: float  # 每百万 token 输出价格 (USD)
    currency: str = "USD"


@dataclass
class TokenUsage:
    """Token 使用记录"""

    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    timestamp: datetime
    request_type: str = "chat"


@dataclass
class CostReport:
    """成本报告"""

    total_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    by_model: dict[str, dict] = field(default_factory=dict)
    by_day: dict[str, dict] = field(default_factory=dict)
    optimization_tips: list[str] = field(default_factory=list)


MODEL_PRICING: dict[str, ModelPricing] = {
    "gpt-5.3": ModelPricing(input_price=5.0, output_price=15.0),
    "gpt-4o": ModelPricing(input_price=2.5, output_price=10.0),
    "gpt-4": ModelPricing(input_price=30.0, output_price=60.0),
    "gpt-3.5-turbo": ModelPricing(input_price=0.5, output_price=1.5),
    "deepseek-chat": ModelPricing(input_price=0.14, output_price=0.28),
    "deepseek-reasoner": ModelPricing(input_price=0.55, output_price=2.19),
    "claude-3-opus": ModelPricing(input_price=15.0, output_price=75.0),
    "claude-3-sonnet": ModelPricing(input_price=3.0, output_price=15.0),
    "gemini-pro": ModelPricing(input_price=0.5, output_price=1.5),
    "ollama/gemma4": ModelPricing(input_price=0.0, output_price=0.0),
    "ollama/gemma3": ModelPricing(input_price=0.0, output_price=0.0),
    "ollama/llama3.1:8b": ModelPricing(input_price=0.0, output_price=0.0),
    "ollama/deepseek-r1:7b": ModelPricing(input_price=0.0, output_price=0.0),
    "ollama/deepseek-v3": ModelPricing(input_price=0.0, output_price=0.0),
}


class TokenCounter:
    """Token 计数器"""

    def __init__(self):
        self._tiktoken = None

    def _get_tiktoken(self):
        if self._tiktoken is None:
            try:
                import tiktoken

                self._tiktoken = tiktoken
            except ImportError:
                logger.warning("tiktoken not installed, using approximate counting")
        return self._tiktoken

    def count_tokens(self, text: str, model: str = "gpt-4") -> int:
        """计算文本的 token 数量"""
        if not text:
            return 0

        tiktoken = self._get_tiktoken()
        if tiktoken:
            try:
                if "gpt" in model.lower() or "deepseek" in model.lower():
                    encoding = tiktoken.encoding_for_model("gpt-4")
                else:
                    encoding = tiktoken.get_encoding("cl100k_base")
                return len(encoding.encode(text))
            except Exception as e:
                logger.debug(f"tiktoken error: {e}")

        return len(text) // 4

    def count_messages_tokens(self, messages: list[dict], model: str = "gpt-4") -> int:
        """计算消息列表的 token 数量"""
        total = 0
        for msg in messages:
            total += 4
            for value in msg.values():
                if isinstance(value, str):
                    total += self.count_tokens(value, model)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict) and "text" in item:
                            total += self.count_tokens(item["text"], model)
            total += 2
        return total


class CostEstimator:
    """成本估算器"""

    def __init__(self, pricing: dict[str, ModelPricing] | None = None):
        self.pricing = pricing or MODEL_PRICING

    def estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """估算成本"""
        model_key = model.replace("ollama/", "") if model.startswith("ollama/") else model

        for key, pricing in self.pricing.items():
            if model_key in key or key in model_key:
                input_cost = (input_tokens / 1_000_000) * pricing.input_price
                output_cost = (output_tokens / 1_000_000) * pricing.output_price
                return round(input_cost + output_cost, 6)

        return 0.0

    def get_model_pricing(self, model: str) -> ModelPricing | None:
        """获取模型定价"""
        model_key = model.replace("ollama/", "") if model.startswith("ollama/") else model

        for key, pricing in self.pricing.items():
            if model_key in key or key in model_key:
                return pricing
        return None


class TokenCostManager:
    """Token 成本管理器"""

    def __init__(self, storage_path: Path | None = None):
        self.token_counter = TokenCounter()
        self.cost_estimator = CostEstimator()
        self.usage_history: list[TokenUsage] = []
        self.storage_path = storage_path
        self._daily_stats: dict[str, dict] = defaultdict(
            lambda: {"requests": 0, "tokens": 0, "cost": 0.0}
        )

        if storage_path and storage_path.exists():
            self._load_history()

    def record_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        request_type: str = "chat",
    ) -> TokenUsage:
        """记录使用情况"""
        cost = self.cost_estimator.estimate_cost(model, input_tokens, output_tokens)

        usage = TokenUsage(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            timestamp=datetime.now(),
            request_type=request_type,
        )

        self.usage_history.append(usage)

        day_key = usage.timestamp.strftime("%Y-%m-%d")
        self._daily_stats[day_key]["requests"] += 1
        self._daily_stats[day_key]["tokens"] += input_tokens + output_tokens
        self._daily_stats[day_key]["cost"] += cost

        if self.storage_path:
            self._save_usage(usage)

        logger.debug(
            f"Recorded usage: model={model}, input={input_tokens}, "
            f"output={output_tokens}, cost=${cost:.6f}"
        )

        return usage

    def get_report(self, days: int = 7) -> CostReport:
        """生成成本报告"""
        report = CostReport()

        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        recent_usage = [u for u in self.usage_history if u.timestamp.timestamp() > cutoff]

        report.total_requests = len(recent_usage)

        for usage in recent_usage:
            report.total_input_tokens += usage.input_tokens
            report.total_output_tokens += usage.output_tokens
            report.total_cost += usage.cost

            if usage.model not in report.by_model:
                report.by_model[usage.model] = {
                    "requests": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost": 0.0,
                }

            report.by_model[usage.model]["requests"] += 1
            report.by_model[usage.model]["input_tokens"] += usage.input_tokens
            report.by_model[usage.model]["output_tokens"] += usage.output_tokens
            report.by_model[usage.model]["cost"] += usage.cost

            day_key = usage.timestamp.strftime("%Y-%m-%d")
            if day_key not in report.by_day:
                report.by_day[day_key] = {"requests": 0, "tokens": 0, "cost": 0.0}
            report.by_day[day_key]["requests"] += 1
            report.by_day[day_key]["tokens"] += usage.input_tokens + usage.output_tokens
            report.by_day[day_key]["cost"] += usage.cost

        report.optimization_tips = self._generate_optimization_tips(report)

        return report

    def _generate_optimization_tips(self, report: CostReport) -> list[str]:
        """生成优化建议"""
        tips = []

        if report.total_cost > 10:
            tips.append("💰 成本较高，建议使用本地模型 (Ollama) 或 DeepSeek")

        for model in report.by_model:
            pricing = self.cost_estimator.get_model_pricing(model)
            if pricing and pricing.input_price > 5:
                tips.append(f"🔄 {model} 成本较高，可考虑切换到 DeepSeek-V4 (节省 ~95%)")

        if report.total_input_tokens > 100000:
            tips.append("📝 输入 token 较多，建议优化 prompt 长度")

        avg_tokens_per_request = (report.total_input_tokens + report.total_output_tokens) / max(
            report.total_requests, 1
        )
        if avg_tokens_per_request > 2000:
            tips.append("⚡ 平均每请求 token 较多，建议启用缓存减少重复请求")

        if not tips:
            tips.append("✅ 当前成本控制良好")

        return tips

    def estimate_request_cost(
        self,
        model: str,
        messages: list[dict],
        estimated_output_tokens: int = 500,
    ) -> dict:
        """估算请求成本"""
        input_tokens = self.token_counter.count_messages_tokens(messages, model)
        estimated_cost = self.cost_estimator.estimate_cost(
            model, input_tokens, estimated_output_tokens
        )

        return {
            "model": model,
            "input_tokens": input_tokens,
            "estimated_output_tokens": estimated_output_tokens,
            "estimated_cost": estimated_cost,
            "pricing": self.cost_estimator.get_model_pricing(model).__dict__
            if self.cost_estimator.get_model_pricing(model)
            else None,
        }

    def _save_usage(self, usage: TokenUsage):
        """保存使用记录"""
        if not self.storage_path:
            return

        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "model": usage.model,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "cost": usage.cost,
                "timestamp": usage.timestamp.isoformat(),
                "request_type": usage.request_type,
            }

            with open(self.storage_path, "a") as f:
                f.write(json.dumps(data) + "\n")
        except Exception as e:
            logger.error(f"Failed to save usage: {e}")

    def _load_history(self):
        """加载历史记录"""
        if not self.storage_path or not self.storage_path.exists():
            return

        try:
            with open(self.storage_path) as f:
                for line in f:
                    data = json.loads(line.strip())
                    usage = TokenUsage(
                        model=data["model"],
                        input_tokens=data["input_tokens"],
                        output_tokens=data["output_tokens"],
                        cost=data["cost"],
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        request_type=data.get("request_type", "chat"),
                    )
                    self.usage_history.append(usage)
        except Exception as e:
            logger.error(f"Failed to load history: {e}")

    def clear_history(self):
        """清除历史记录"""
        self.usage_history.clear()
        self._daily_stats.clear()
        if self.storage_path and self.storage_path.exists():
            self.storage_path.unlink()


token_cost_manager = TokenCostManager()
