#!/usr/bin/env python3
"""调试状态同步问题"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

# 模拟 AG-UI 传入的状态数据
frontend_state = {
    "uploadedFiles": [
        {
            "name": "test.pdf",
            "base64": "JVBERi0xLgo=",  # 最小的 PDF base64
            "mimeType": "application/pdf",
            "sizeBytes": 10
        }
    ],
    "findings": [],
    "redacted": [],
    "tweets": [],
    "summary": None
}

print("=" * 60)
print("🔍 调试状态同步")
print("=" * 60)

print("\n📤 前端状态 (camelCase):")
for key, value in frontend_state.items():
    print(f"  {key}: {type(value).__name__} = {value if not isinstance(value, list) else f'[...{len(value)} items]'}")

# 导入并测试状态处理
from main import FileInvestigatorState, build_investigator_prompt
from langchain_core.messages import HumanMessage

# 模拟状态转换 (AG-UI 会自动转换)
# 前端的 camelCase 会被转换为 snake_case
backend_state = FileInvestigatorState(
    messages=[HumanMessage(content="测试")],
    uploaded_files=frontend_state.get("uploadedFiles", []),
    findings=frontend_state.get("findings", []),
    redacted=frontend_state.get("redacted", []),
    tweets=frontend_state.get("tweets", []),
    summary=frontend_state.get("summary") or ""
)

print("\n📥 后端状态 (snake_case):")
for key in ["uploaded_files", "findings", "redacted", "tweets", "summary"]:
    value = backend_state.get(key, [])
    print(f"  {key}: {type(value).__name__} = {value if not isinstance(value, list) else f'[...{len(value)} items]'}")

# 测试 prompt 构建
print("\n🔨 测试 prompt 构建:")
prompt = build_investigator_prompt(backend_state, "请分析这个文档")

if "test.pdf" in prompt or "PDF" in prompt:
    print("  ✅ 文件信息已包含在 prompt 中")
else:
    print("  ❌ 文件信息未包含在 prompt 中")

if len(prompt) > 100:
    print(f"  ✅ prompt 长度: {len(prompt)} 字符")
else:
    print(f"  ⚠️  prompt 较短: {len(prompt)} 字符")

print("\n" + "=" * 60)
print("✅ 调试完成")
print("=" * 60)
