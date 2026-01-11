"""Diagnose import issues in main_langgraph_simple.py"""

import sys

print("=== Testing imports step by step ===\n")

# Test 1: Basic imports
print("1. Testing basic imports...")
try:
    from fastapi import FastAPI
    print("   ✅ FastAPI")
except Exception as e:
    print(f"   ❌ FastAPI: {e}")
    sys.exit(1)

# Test 2: LangGraph imports
print("\n2. Testing LangGraph imports...")
try:
    from langgraph.graph import StateGraph, MessagesState, START, END
    print("   ✅ langgraph.graph")
except Exception as e:
    print(f"   ❌ langgraph.graph: {e}")
    sys.exit(1)

try:
    from langgraph.prebuilt import ToolNode
    print("   ✅ langgraph.prebuilt")
except Exception as e:
    print(f"   ❌ langgraph.prebuilt: {e}")

try:
    from langgraph.types import Command
    print("   ✅ langgraph.types")
except Exception as e:
    print(f"   ❌ langgraph.types: {e}")

# Test 3: LangChain imports
print("\n3. Testing LangChain imports...")
try:
    from langchain_core.messages import ToolMessage, HumanMessage, SystemMessage
    print("   ✅ langchain_core.messages")
except Exception as e:
    print(f"   ❌ langchain_core.messages: {e}")

try:
    from langchain_core.tools import tool
    print("   ✅ langchain_core.tools")
except Exception as e:
    print(f"   ❌ langchain_core.tools: {e}")

try:
    from langchain_aws import ChatBedrock
    print("   ✅ langchain_aws")
except Exception as e:
    print(f"   ❌ langchain_aws: {e}")

try:
    from langchain_anthropic import ChatAnthropic
    print("   ✅ langchain_anthropic")
except Exception as e:
    print(f"   ❌ langchain_anthropic: {e}")

# Test 4: Local imports
print("\n4. Testing local imports...")
try:
    from dotenv import load_dotenv
    print("   ✅ dotenv")
except Exception as e:
    print(f"   ❌ dotenv: {e}")

try:
    from pdf_utils import extract_text_from_pdf, format_extracted_files_as_xml
    print("   ✅ pdf_utils")
except Exception as e:
    print(f"   ❌ pdf_utils: {e}")

try:
    from pydantic import BaseModel, Field
    print("   ✅ pydantic")
except Exception as e:
    print(f"   ❌ pydantic: {e}")

# Test 5: State definition
print("\n5. Testing state definition...")
try:
    from typing import List
    from pydantic import BaseModel

    class Finding(BaseModel):
        id: str
        title: str
        description: str
        severity: str

    class FileInvestigatorState(MessagesState):
        findings: List[Finding]
        redacted: list
        tweets: list
        summary: str
        uploaded_files: list

    print("   ✅ State definition")
except Exception as e:
    print(f"   ❌ State definition: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Graph creation
print("\n6. Testing graph creation...")
try:
    def test_node(state: FileInvestigatorState):
        return {"messages": []}

    builder = StateGraph(FileInvestigatorState)
    builder.add_node("test", test_node)
    graph = builder.compile()
    print("   ✅ Graph creation")
except Exception as e:
    print(f"   ❌ Graph creation: {e}")
    import traceback
    traceback.print_exc()

print("\n=== All tests completed ===")
