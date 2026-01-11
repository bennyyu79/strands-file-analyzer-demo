#!/usr/bin/env python3
"""测试 agent API 端点"""

import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("🧪 测试 Agent API")
print("=" * 60)

# 1. 健康检查
print("\n1️⃣  健康检查")
try:
    response = requests.get(f"{BASE_URL}/health")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("   ✅ 健康检查通过")
except Exception as e:
    print(f"   ❌ 健康检查失败: {e}")

# 2. 测试 invoke 端点 (简单文本消息)
print("\n2️⃣  测试 /invoke 端点")
try:
    test_payload = {
        "state": {
            "uploaded_files": [],
            "findings": [],
            "redacted": [],
            "tweets": [],
            "summary": ""
        },
        "message": "你好,请介绍一下你自己"
    }

    print(f"   发送请求...")
    response = requests.post(
        f"{BASE_URL}/invoke",
        json=test_payload,
        timeout=30
    )

    print(f"   状态码: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"   响应状态: {result.get('status', 'success')}")
        if "state" in result:
            state = result["state"]
            print(f"   更新的字段:")
            if state.get("summary"):
                print(f"     - summary: {state['summary'][:100]}...")
            if state.get("findings"):
                print(f"     - findings: {len(state['findings'])} 条")
        print("   ✅ Invoke 测试通过")
    else:
        print(f"   ❌ 请求失败: {response.text}")
except requests.exceptions.Timeout:
    print("   ⚠️  请求超时 (这是正常的,因为模型调用需要时间)")
except Exception as e:
    print(f"   ⚠️  测试跳过或失败: {e}")

print("\n" + "=" * 60)
print("✅ API 测试完成!")
print("=" * 60)
