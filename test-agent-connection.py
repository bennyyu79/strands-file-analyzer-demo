#!/usr/bin/env python3
"""测试 Python Agent 接收的请求格式"""

import requests
import json

# 测试不同的请求格式
url = "http://192.168.214.102:8000/"

# 格式 1: AG-UI 协议标准格式
test_payload_1 = {
    "threadId": "test-thread-123",
    "runId": "test-run-456",
    "state": {
        "uploadedFiles": [
            {
                "name": "test.pdf",
                "base64": "JVBERi0xLjQK",
                "mimeType": "application/pdf",
                "sizeBytes": 100
            }
        ],
        "analysisStatus": "idle",
        "findings": [],
        "redacted": [],
        "tweets": [],
        "summary": None
    },
    "messages": [
        {
            "role": "user",
            "content": "分析文档"
        }
    ],
    "tools": [],
    "forwardedProps": {}
}

print("=" * 60)
print("测试格式 1: 标准 AG-UI 格式")
print("=" * 60)
print(f"URL: {url}")
print(f"Payload keys: {list(test_payload_1.keys())}")
print()

try:
    response = requests.post(url, json=test_payload_1, timeout=10)
    print(f"✅ 状态码: {response.status_code}")
    print(f"响应: {response.text[:500]}")
except Exception as e:
    print(f"❌ 错误: {e}")

print()
print("=" * 60)
