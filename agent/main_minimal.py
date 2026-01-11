"""Minimal working LangGraph server for testing."""

import os
import logging
from typing import List
from fastapi import FastAPI
import uvicorn

# LangGraph imports
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool
from langchain_aws import ChatBedrock

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Simple state
class SimpleState(MessagesState):
    counter: int = 0

# Simple tool
@tool
def test_tool(query: str) -> str:
    """A simple test tool."""
    logger.info(f"test_tool called with: {query}")
    return f"Tool response to: {query}"

# Simple model node
def call_model(state: SimpleState) -> dict:
    """Call the model."""
    logger.info("call_model invoked")

    messages = state.get("messages", [])
    logger.info(f"Messages: {len(messages)}")

    # For testing, just return a simple message
    return {
        "messages": [AIMessage(content="Test response from agent")],
        "counter": state.get("counter", 0) + 1
    }

def should_continue(state: SimpleState) -> str:
    """Determine if we should continue."""
    messages = state.get("messages", [])
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
    return END

# Create graph
def create_graph():
    """Create a simple test graph."""
    builder = StateGraph(SimpleState)

    builder.add_node("agent", call_model)

    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", should_continue, {"end": END})

    return builder.compile()

# Create FastAPI app
app = FastAPI(title="Minimal LangGraph Test")

# Create graph at module level
graph = create_graph()

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "framework": "langgraph", "type": "minimal"}

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Minimal LangGraph Test Server", "endpoints": ["/health", "/invoke"]}

@app.post("/invoke")
async def invoke_agent(request: dict):
    """Invoke the agent."""
    try:
        user_message = request.get("message", "Hello")

        initial_state = SimpleState(
            messages=[HumanMessage(content=user_message)],
            counter=0
        )

        result = graph.invoke(initial_state)

        return {
            "status": "success",
            "result": {
                "messages": [m.content if hasattr(m, "content") else str(m) for m in result.get("messages", [])],
                "counter": result.get("counter", 0)
            }
        }
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    logger.info("Starting minimal LangGraph server on http://localhost:8002")
    uvicorn.run(app, host="0.0.0.0", port=8002)
