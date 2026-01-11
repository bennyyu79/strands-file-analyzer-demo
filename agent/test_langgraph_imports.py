"""Test LangGraph imports and basic setup."""

import sys

def test_imports():
    """Test if all required packages can be imported."""
    print("Testing LangGraph imports...")

    try:
        from langgraph.graph import StateGraph, MessagesState, START, END
        print("✅ langgraph.graph imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import langgraph.graph: {e}")
        return False

    try:
        from langgraph.prebuilt import ToolNode
        print("✅ langgraph.prebuilt imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import langgraph.prebuilt: {e}")
        return False

    try:
        from langgraph.types import Command
        print("✅ langgraph.types imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import langgraph.types: {e}")
        return False

    try:
        from langchain_core.messages import ToolMessage, HumanMessage, SystemMessage
        print("✅ langchain_core.messages imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import langchain_core.messages: {e}")
        return False

    try:
        from langchain_core.tools import tool
        print("✅ langchain_core.tools imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import langchain_core.tools: {e}")
        return False

    try:
        from langchain_aws import ChatBedrock
        print("✅ langchain_aws imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import langchain_aws: {e}")
        return False

    try:
        from langchain_anthropic import ChatAnthropic
        print("✅ langchain_anthropic imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import langchain_anthropic: {e}")
        return False

    try:
        from fastapi import FastAPI
        print("✅ fastapi imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import fastapi: {e}")
        return False

    try:
        from ag_ui_langgraph import StateUpdate
        print("✅ ag_ui_langgraph imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import ag_ui_langgraph: {e}")
        return False

    print("\n✅ All imports successful!")
    return True

def test_basic_functionality():
    """Test basic LangGraph functionality."""
    print("\nTesting basic LangGraph functionality...")

    try:
        from langgraph.graph import StateGraph, MessagesState

        # Create a simple state graph
        class TestState(MessagesState):
            test_value: str = "test"

        def test_node(state: TestState):
            return {"messages": ["test"]}

        builder = StateGraph(TestState)
        builder.add_node("test", test_node)
        print("✅ Basic StateGraph creation successful")
        return True

    except Exception as e:
        print(f"❌ Failed to create StateGraph: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    if success:
        test_basic_functionality()
    else:
        print("\n❌ Import tests failed. Please check your installation.")
        sys.exit(1)
