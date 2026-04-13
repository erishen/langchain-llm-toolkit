import litellm

# 直接测试 Ollama gemma3 模型
try:
    # 调用 Ollama gemma3 模型（使用 chat 方法）
    response = litellm.chat(
        model="ollama/gemma3",
        messages=[{"role": "user", "content": "Hello, what is your name?"}],
        temperature=0.7,
        max_tokens=1000,
    )

    # 打印完整响应
    print("完整响应:")
    print(response)

    # 尝试不同的方式获取响应内容
    print("\n获取响应内容的不同方式:")

    # 方式 1: 使用 text 属性
    try:
        text = response.choices[0].text
        print(f"方式 1 (text): {text}")
    except Exception as e:
        print(f"方式 1 失败: {e}")

    # 方式 2: 使用 message.content 属性
    try:
        message_content = response.choices[0].message.content
        print(f"方式 2 (message.content): {message_content}")
    except Exception as e:
        print(f"方式 2 失败: {e}")

    # 方式 3: 检查 choices 对象的所有属性
    print("\nchoices[0] 的属性:")
    print(dir(response.choices[0]))

    # 方式 4: 检查响应对象的所有属性
    print("\nresponse 的属性:")
    print(dir(response))

    # 方式 5: 检查响应的字典表示
    print("\nresponse 的字典表示:")
    print(response.__dict__)

except Exception as e:
    print(f"错误: {e}")
