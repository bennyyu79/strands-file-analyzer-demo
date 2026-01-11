#!/usr/bin/env python3
"""测试模型配置是否正确加载"""

import os
from dotenv import load_dotenv
from main_langgraph import create_model

# 加载环境变量
load_dotenv()

print("=" * 60)
print("🔍 测试模型配置")
print("=" * 60)

# 显示当前配置
print("\n📋 环境变量配置:")
print(f"  ANTHROPIC_BASE_URL: {os.getenv('ANTHROPIC_BASE_URL')}")
print(f"  ANTHROPIC_AUTH_TOKEN: {os.getenv('ANTHROPIC_AUTH_TOKEN')[:20]}...")
print(f"  ANTHROPIC_MODEL: {os.getenv('ANTHROPIC_MODEL')}")

# 创建模型
print("\n🔧 创建模型实例...")
model = create_model()

# 显示模型信息
print("\n✅ 模型信息:")
print(f"  类型: {type(model).__name__}")
print(f"  模型名称: {model.model}")

if hasattr(model, 'base_url'):
    print(f"  Base URL: {model.base_url}")

if hasattr(model, 'api_key'):
    print(f"  API Key: {model.api_key[:20]}...")

if hasattr(model, 'temperature'):
    print(f"  Temperature: {model.temperature}")

if hasattr(model, 'max_tokens'):
    print(f"  Max Tokens: {model.max_tokens}")

print("\n" + "=" * 60)
print("✅ 配置测试完成!")
print("=" * 60)
