#!/usr/bin/env python3
"""测试 hello world 消息"""

import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("🧪 测试 Hello World")
print("=" * 60)

# 测试简单的 hello world
test_payload = {
    "state": {
        "uploaded_files": [],
        "findings": [],
        "redacted": [],
        "tweets": [],
        "summary": ""
    },
    "message": "hello world"
}

print("\n📤 发送消息:")
print(f"   {test_payload['message']}")

print("\n⏳ 等待响应...")
response = requests.post(
    f"{BASE_URL}/invoke",
    json=test_payload,
    timeout=30
)

print(f"\n📥 状态码: {response.status_code}")

if response.status_code == 200:
    result = response.json()

    print("\n" + "=" * 60)
    print("📊 Agent 响应:")
    print("=" * 60)

    if "state" in result:
        state = result["state"]

        # 显示各个面板的更新
        if state.get("summary"):
            print(f"\n📝 Summary:")
            print(f"   {state['summary']}")

        if state.get("findings"):
            print(f"\n🔍 Findings ({len(state['findings'])} 条):")
            for i, finding in enumerate(state['findings'], 1):
                print(f"   {i}. {finding.get('title', 'N/A')}")
                print(f"      {finding.get('description', 'N/A')}")

        if state.get("tweets"):
            print(f"\n🐦 Tweets ({len(state['tweets'])} 条):")
            for i, tweet in enumerate(state['tweets'], 1):
                print(f"   {i}. {tweet.get('content', 'N/A')}")

        if state.get("redacted"):
            print(f"\n🕵️  Redacted ({len(state['redacted'])} 条):")
            for i, item in enumerate(state['redacted'], 1):
                print(f"   {i}. {item.get('location', 'N/A')}")
                print(f"      猜测: {item.get('speculation', 'N/A')}")

    print("\n" + "=" * 60)
    print("✅ 测试完成!")
    print("=" * 60)
else:
    print(f"❌ 请求失败: {response.text}")
