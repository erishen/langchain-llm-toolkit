#!/usr/bin/env python3
"""LangChain LLM Toolkit 命令行界面"""

import typer

from langchain_llm_toolkit.config.settings import settings
from langchain_llm_toolkit.conversation import ConversationManager
from langchain_llm_toolkit.llm_integration import LLMIntegration

app = typer.Typer(help="LangChain LLM Toolkit 命令行工具")
model_app = typer.Typer(help="模型管理")
temperature_app = typer.Typer(help="温度参数管理")

app.add_typer(model_app, name="model")
app.add_typer(temperature_app, name="temperature")

# 全局配置
current_model = settings.DEFAULT_MODEL
current_temperature = settings.DEFAULT_TEMPERATURE


@app.command()
def generate(
    prompt: str,
    model: str | None = typer.Option(None, "--model", "-m", help="指定模型"),
    temperature: float | None = typer.Option(None, "--temperature", "-t", help="温度参数"),
):
    """生成文本响应"""
    llm = LLMIntegration()

    # 使用指定的模型或默认模型
    use_model = model or current_model
    use_temp = temperature or current_temperature

    llm.set_model(use_model)
    llm.set_temperature(use_temp)

    typer.echo(f"使用模型: {use_model}")
    typer.echo(f"温度参数: {use_temp}")
    typer.echo(f"\n提示: {prompt}")
    typer.echo("-" * 50)

    response = llm.generate(prompt)
    typer.echo(f"回答: {response}")


@app.command()
def chat(
    model: str | None = typer.Option(None, "--model", "-m", help="指定模型"),
    temperature: float | None = typer.Option(None, "--temperature", "-t", help="温度参数"),
):
    """进入聊天模式"""
    conversation_manager = ConversationManager()

    # 使用指定的模型或默认模型
    use_model = model or current_model
    use_temp = temperature or current_temperature

    conversation_manager.set_model(use_model)
    conversation_manager.set_temperature(use_temp)

    typer.echo("=== LangChain 对话系统 ===")
    typer.echo(f"使用模型: {use_model}")
    typer.echo(f"温度参数: {use_temp}")
    typer.echo("输入 'exit' 退出对话")
    typer.echo("输入 'clear' 清空对话历史")
    typer.echo("输入 'history' 查看对话历史")
    typer.echo("========================")

    while True:
        try:
            user_input = typer.prompt("\nUser", type=str)

            if user_input.lower() == "exit":
                typer.echo("再见！")
                break

            elif user_input.lower() == "clear":
                conversation_manager.clear_history()
                typer.echo("对话历史已清空")
                continue

            elif user_input.lower() == "history":
                history = conversation_manager.get_history()
                typer.echo("\n对话历史:")
                for msg in history:
                    typer.echo(f"{msg['role']}: {msg['content'][:100]}...")
                continue

            # 进行对话
            response = conversation_manager.converse(user_input)
            typer.echo(f"Assistant: {response}")

        except KeyboardInterrupt:
            typer.echo("\n再见！")
            break
        except Exception as e:
            typer.echo(f"错误: {e!s}", err=True)


@model_app.command("list")
def list_models():
    """列出支持的模型"""
    typer.echo("支持的模型:")
    typer.echo("\nOpenAI 模型:")
    typer.echo("  - gpt-5.5 (最新)")

    typer.echo("\nAnthropic 模型:")
    typer.echo("  - claude-opus-4-7 (编码+Agent最强)")
    typer.echo("  - claude-sonnet-4-6 (写作最强)")

    typer.echo("\nGoogle 模型:")
    typer.echo("  - gemini-3.1-pro (推理94.3%，性价比最高)")

    typer.echo("\nDeepSeek 模型:")
    typer.echo("  - deepseek-chat (V4 Pro，极致性价比)")
    typer.echo("  - deepseek-reasoner (R2 推理)")

    typer.echo("\nAlibaba 模型:")
    typer.echo("  - qwen-3.6-plus (开源最强编码)")

    typer.echo("\nOllama 本地模型:")
    typer.echo("  - ollama/gemma4 (推荐)")
    typer.echo("  - ollama/llama4-scout (10M上下文)")
    typer.echo("  - ollama/deepseek-v3")
    typer.echo("  - ollama/deepseek-r1")
    typer.echo("  - ollama/qwen3-coder (编码最强)")

    typer.echo("\n当前默认模型: " + typer.style(current_model, fg=typer.colors.GREEN, bold=True))


@model_app.command("set")
def set_model(model: str):
    """设置默认模型"""
    global current_model
    current_model = model
    typer.echo(f"默认模型已设置为: {typer.style(model, fg=typer.colors.GREEN, bold=True)}")


@temperature_app.command("set")
def set_temperature(temperature: float):
    """设置温度参数"""
    global current_temperature
    current_temperature = temperature
    typer.echo(
        f"温度参数已设置为: {typer.style(str(temperature), fg=typer.colors.GREEN, bold=True)}"
    )


@temperature_app.command("get")
def get_temperature():
    """获取当前温度参数"""
    typer.echo(
        f"当前温度参数: {typer.style(str(current_temperature), fg=typer.colors.GREEN, bold=True)}"
    )


if __name__ == "__main__":
    app()
