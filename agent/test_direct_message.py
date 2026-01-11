#!/usr/bin/env python3
"""直接测试模型响应"""

import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

print("=" * 60)
print("🧪 直接测试模型响应")
print("=" * 60)

# 创建模型
model = ChatAnthropic(
    model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
    api_key=os.getenv("ANTHROPIC_AUTH_TOKEN"),
    base_url=os.getenv("ANTHROPIC_BASE_URL"),
    temperature=0.7,
    max_tokens=4096,
)

system_prompt = """你是 File Investigator - 一个带有讽刺幽默的文档分析师。

当用户向你打招呼或提问时,你应该:
1. 用幽默、讽刺的语气回应
2. 介绍你是一个文档分析专家
3. 如果有上传的文件,可以调用工具来分析文档

你现在可以使用的工具:
- update_findings: 更新关键发现
- update_redacted: 更新涂黑内容猜测
- update_tweets: 更新推文
- update_summary: 更新摘要

如果用户只是打招呼,你可以直接回复,不需要调用工具。
"""

# 测试 1: Hello World
print("\n📝 测试 1: Hello World")
print("-" * 60)

messages = [
    SystemMessage(content=system_prompt),
    HumanMessage(content="hello world")
]

response = model.invoke(messages)
print(f"响应类型: {type(response).__name__}")
print(f"响应内容:\n{response.content}\n")

if hasattr(response, 'tool_calls') and response.tool_calls:
    print(f"工具调用: {len(response.tool_calls)} 个")
    for i, call in enumerate(response.tool_calls, 1):
        print(f"  {i}. {call['name']}")
else:
    print("工具调用: 无")

# 测试 2: 中文问候
print("\n📝 测试 2: 中文问候")
print("-" * 60)

messages = [
    SystemMessage(content=system_prompt),
    HumanMessage(content="你好,你是谁?请介绍一下自己。")
]

response = model.invoke(messages)
print(f"响应内容:\n{response.content}\n")

if hasattr(response, 'tool_calls') and response.tool_calls:
    print(f"工具调用: {len(response.tool_calls)} 个")
else:
    print("工具调用: 无")

# 测试 3: 要求分析文档(但没有文档)
print("\n📝 测试 3: 要求分析")
print("-" * 60)

messages = [
    SystemMessage(content=system_prompt),
    HumanMessage(content="请帮我分析一下这份文档。")
]

response = model.invoke(messages)
print(f"响应内容:\n{response.content}\n")

if hasattr(response, 'tool_calls') and response.tool_calls:
    print(f"工具调用: {len(response.tool_calls)} 个")
    for i, call in enumerate(response.tool_calls, 1):
        print(f"  {i}. {call['name']}")
else:
    print("工具调用: 无")

print("\n" + "=" * 60)
print("✅ 测试完成!")
print("=" * 60)
