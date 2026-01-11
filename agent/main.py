"""File Investigator Agent - LangGraph + AG-UI + CopilotKit Integration."""

import base64
import logging
import os
import uuid
from typing import List, Literal

from dotenv import load_dotenv
from pdf_utils import extract_text_from_pdf, format_extracted_files_as_xml
from pydantic import BaseModel, Field
from copilotkit import LangGraphAGUIAgent, CopilotKitState

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(name)s - %(message)s",
)

# === LangGraph and AG-UI Imports ===

from langgraph.graph import StateGraph, MessagesState, END
from langgraph.prebuilt import ToolNode
from langgraph.types import Command
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langchain_aws import ChatBedrock
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from botocore.config import Config as BotocoreConfig
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ag_ui_langgraph import add_langgraph_fastapi_endpoint

# === Pydantic Models ===

class Finding(BaseModel):
    """A key finding from document analysis."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = Field(description="Short title")
    description: str = Field(description="Detailed description")
    severity: str = Field(description="low, medium, high, or critical")


class RedactedItem(BaseModel):
    """A detected redaction with speculation."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    location: str = Field(description="Where in the document")
    speculation: str = Field(description="What might be hidden")
    confidence: int = Field(description="Confidence 0-100")


class Tweet(BaseModel):
    """A generated tweet."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    content: str = Field(description="Tweet text")
    posted: bool = Field(default=False)


# === LangGraph State Definition ===

class FileInvestigatorState(CopilotKitState):
    """State for the File Investigator agent."""
    findings: List[Finding]
    redactedContent: List[RedactedItem]
    tweets: List[Tweet]
    summary: str
    uploadedFiles: List[dict]


# === Tool Definitions ===

@tool
def update_findings(findings_list: dict) -> str:
    """Update the Key Findings panel.

    Args:
        findings_list: Dict with 'findings' array containing title, description, severity

    Returns:
        Success message
    """
    findings_data = findings_list.get("findings", []) if isinstance(findings_list, dict) else []
    findings = [
        Finding(
            title=f.get("title", "Untitled"),
            description=f.get("description", ""),
            severity=f.get("severity", "low")
        )
        for f in findings_data
    ]
    # Return findings as JSON - will be picked up by call_model
    import json
    return json.dumps([f.model_dump() for f in findings])


@tool
def update_redacted(redacted_list: dict) -> str:
    """Update the Redacted Content panel.

    Args:
        redacted_list: Dict with 'redacted_items' array containing location, speculation, confidence

    Returns:
        Success message
    """
    items_data = redacted_list.get("redacted_items", []) if isinstance(redacted_list, dict) else []

    def parse_confidence(conf_value):
        """Parse confidence from various formats: '100%', 'high', 80, etc."""
        if isinstance(conf_value, int):
            return conf_value
        if isinstance(conf_value, str):
            # Handle text descriptions
            conf_lower = conf_value.lower()
            if conf_lower in ["high", "very high"]:
                return 80
            elif conf_lower in ["medium", "moderate"]:
                return 50
            elif conf_lower in ["low", "very low"]:
                return 20
            # Handle numeric strings with possible % sign
            numeric_part = ''.join(c for c in conf_value if c.isdigit())
            return int(numeric_part) if numeric_part.isdigit() else 50
        return 50  # Default fallback

    items = [
        RedactedItem(
            location=item.get("location", "Unknown"),
            speculation=item.get("speculation", ""),
            confidence=parse_confidence(item.get("confidence", 50))
        )
        for item in items_data
    ]
    import json
    return json.dumps([i.model_dump() for i in items])


@tool
def update_tweets(tweets_list: dict) -> str:
    """Update the Tweets panel.

    Args:
        tweets_list: Dict with 'tweets' array containing content

    Returns:
        Success message
    """
    tweets_data = tweets_list.get("tweets", []) if isinstance(tweets_list, dict) else []
    tweets = [
        Tweet(content=t.get("content", ""), posted=False)
        for t in tweets_data
    ]
    import json
    return json.dumps([t.model_dump() for t in tweets])


@tool
def update_summary(summary_content: dict) -> str:
    """Update the Summary panel.

    Args:
        summary_content: Dict with 'summary' string

    Returns:
        Success message
    """
    summary = summary_content.get("summary", "") if isinstance(summary_content, dict) else ""
    return summary


# === Model Configuration ===

def create_model():
    """Create and configure the LLM model.

    Priority:
    1. OpenAI compatible (OPENAI_BASE_URL, OPENAI_MODEL)
    2. Custom Anthropic (ANTHROPIC_BASE_URL, ANTHROPIC_AUTH_TOKEN)
    3. AWS Bedrock (MODEL_ID, AWS_REGION)
    """
    logger = logging.getLogger("agent.config")

    # Check OpenAI compatible config
    openai_base_url = os.getenv("OPENAI_BASE_URL")
    if openai_base_url:
        logger.info(f"Using OpenAI compatible API: {openai_base_url}")
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4"),
            base_url=openai_base_url,
            api_key=os.getenv("OPENAI_API_KEY", "sk-not-needed"),
            temperature=0.7,
            max_tokens=4096,
        )

    # Check custom Anthropic config
    custom_base_url = os.getenv("ANTHROPIC_BASE_URL")
    custom_token = os.getenv("ANTHROPIC_AUTH_TOKEN")
    if custom_base_url and custom_token:
        logger.info(f"Using custom Anthropic API: {custom_base_url}")
        return ChatAnthropic(
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            api_key=custom_token,
            base_url=custom_base_url,
            temperature=0.7,
            max_tokens=4096,
        )

    # Fallback to AWS Bedrock
    region = os.getenv("AWS_REGION", "us-west-1")
    model_id = os.getenv("MODEL_ID", "anthropic.claude-haiku-4-5-20251001-v1:0")
    logger.info(f"Using AWS Bedrock: {model_id}")

    if model_id.startswith("openai."):
        return ChatBedrock(
            model_id=model_id,
            region_name=region,
            model_kwargs={"temperature": 0.7},
            config=BotocoreConfig(region_name=region, connect_timeout=300, read_timeout=300),
        )
    elif (model_id.startswith("claude-") or "anthropic" in model_id.lower()) and os.getenv("ANTHROPIC_API_KEY"):
        return ChatAnthropic(model=model_id, temperature=0.7, max_tokens=4096)
    else:
        return ChatBedrock(
            model_id=model_id,
            region_name=region,
            temperature=0.7,
            max_tokens=4096,
            config=BotocoreConfig(region_name=region, connect_timeout=300, read_timeout=300),
        )


# === Prompt Building ===

def build_investigator_prompt(state: FileInvestigatorState, user_message: str) -> str:
    """Inject files and analysis state into the prompt."""
    logger = logging.getLogger("agent.context")
    context_parts = []
    extracted_texts = []

    # Process uploaded files
    uploadedFiles = state.get("uploadedFiles", [])
    logger.info(f"Processing {len(uploadedFiles)} files")

    for file_info in uploadedFiles:
        file_name = file_info.get("name", "document.pdf")
        base64_data = file_info.get("base64", "")

        if not base64_data:
            logger.warning(f"File {file_name} has no base64 data")
            continue

        try:
            pdf_bytes = base64.b64decode(base64_data)
            extracted = extract_text_from_pdf(pdf_bytes, file_name)
            if extracted:
                logger.info(f"Extracted {len(extracted)} chars from {file_name}")
                extracted_texts.append((file_name, extracted))
            else:
                logger.warning(f"Failed to extract text from {file_name}")
        except Exception as e:
            logger.error(f"Error processing {file_name}: {e}")

    if extracted_texts:
        xml_content = format_extracted_files_as_xml(extracted_texts)
        context_parts.append(f"\n{xml_content}\n")
        logger.info(f"Formatted {len(extracted_texts)} files as XML")

    # Build full prompt
    system_prompt = """You are the File Investigator - a sardonic document analyst with dry humor.

PERSONALITY: World-weary investigative journalist. Dry wit about redactions and bureaucracy.
Slightly conspiratorial but self-aware. Treat every document like it might hide secrets.

When analyzing PDFs (you may receive multiple files):

1. If multiple files, briefly acknowledge the collection
2. Look for connections and patterns across documents
3. Call the update_* tools to populate the dashboard panels

**KEY FINDINGS** (update_findings):
- MAX 3-5 truly important points across ALL documents
- Cross-reference between files when relevant
- One sentence each, be punchy

**REDACTED CONTENT** (update_redacted):
- Note actual redactions/gaps found in any document
- Specify which document contains each redaction
- Add wildly creative speculation about what's hidden

**TWEETS** (update_tweets):
- 3-4 viral-worthy tweets about the document collection
- Reference specific documents when juicy
- #NothingToSeeHere #TotallyNormal

**SUMMARY** (update_summary):
- 2-3 sentences about the overall document collection
- What's the story these documents tell together?

Keep humor absurdist and playful. Never mean-spirited.

NOTE: All PDFs are provided as extracted text in XML format.
"""

    if context_parts:
        return f"{system_prompt}\n\n## DOCUMENTS TO ANALYZE:\n{''.join(context_parts)}\n\n## USER MESSAGE:\n{user_message}"
    else:
        return f"{system_prompt}\n\n## USER MESSAGE:\n{user_message}"


# === LangGraph Nodes ===

def call_model(state: FileInvestigatorState, config: RunnableConfig) -> Command[Literal["tools", "__end__"]]:
    """Node that calls the LLM model."""
    logger = logging.getLogger("agent.model")
    messages = state.get("messages", [])
    user_message = messages[-1].content if messages and isinstance(messages[-1], HumanMessage) else ""

    logger.info(f"Processing message: {user_message[:100]}")

    # Check if all tools have been executed (all state fields populated)
    findings = state.get("findings", [])
    redactedContent = state.get("redactedContent", [])
    tweets = state.get("tweets", [])
    summary = state.get("summary", "")

    # If all 4 tools have been called and we have a ToolMessage, generate final response
    if (messages and type(messages[-1]).__name__ == "ToolMessage" and
        findings and redactedContent and tweets and summary):
        logger.info("All tools executed, generating final response")

        final_response = AIMessage(
            content="✅ 文档分析完成！请查看右侧面板的结果。我发现了以下关键信息：\n\n" +
                     (f"• {len(findings)} 条关键发现\n" if findings else "") +
                     (f"• {len(redactedContent)} 处涂黑内容\n" if redactedContent else "") +
                     (f"• {len(tweets)} 条推文草稿\n" if tweets else "") +
                     (f"• {summary[:100] if summary else ''}...\n" if summary else ""),
        )
        return Command(goto="__end__", update={"messages": [final_response]})

    # Build prompt with context
    prompt = build_investigator_prompt(state, user_message)

    # Create model with tools
    model = create_model()
    tools = [update_findings, update_redacted, update_tweets, update_summary]
    model_with_tools = model.bind_tools(tools)

    # Invoke model
    response = model_with_tools.invoke([SystemMessage(content=prompt), *messages])

    # Check for tool calls
    if response.tool_calls:
        logger.info(f"Model called {len(response.tool_calls)} tools")
        return Command(goto="tools", update={"messages": [response]})

    # No tool calls - end the graph
    logger.info("Model response without tool calls")
    clean_response = AIMessage(content=response.content, id=response.id)
    return Command(goto="__end__", update={"messages": [clean_response]})


def tools_router(state: FileInvestigatorState) -> Command:
    """Process tool results and update state."""
    logger = logging.getLogger("agent.tools")

    messages = state.get("messages", [])
    updates = {}

    # Process tool messages and update state
    for msg in messages:
        if type(msg).__name__ == "ToolMessage":
            tool_call_id = getattr(msg, 'tool_call_id', '')
            content = msg.content

            # Find which tool was called
            for earlier_msg in messages:
                if type(earlier_msg).__name__ == "AIMessage" and hasattr(earlier_msg, 'tool_calls'):
                    for tc in earlier_msg.tool_calls:
                        if tc.get('id') == tool_call_id:
                            tool_name = tc.get('name', '')
                            logger.info(f"Processing {tool_name} result")

                            # Parse tool output and update state
                            import json
                            try:
                                if tool_name == "update_findings":
                                    # Handle empty content, whitespace, empty arrays
                                    if not content or not isinstance(content, str) or content.strip() == "" or content == "[]":
                                        logger.info(f"No data for {tool_name}, setting empty array")
                                        updates["findings"] = []
                                    else:
                                        try:
                                            findings_data = json.loads(content)
                                            updates["findings"] = [Finding(**f) for f in findings_data] if findings_data else []
                                        except json.JSONDecodeError as e:
                                            logger.error(f"JSON parsing error for {tool_name}: {e}, content: '{content[:100]}'")
                                            updates["findings"] = []
                                elif tool_name == "update_redacted":
                                    # Handle empty content, whitespace, empty arrays
                                    if not content or not isinstance(content, str) or content.strip() == "" or content == "[]":
                                        logger.info(f"No data for {tool_name}, setting empty array")
                                        updates["redactedContent"] = []
                                    else:
                                        try:
                                            redacted_data = json.loads(content)
                                            updates["redactedContent"] = [RedactedItem(**r) for r in redacted_data] if redacted_data else []
                                        except json.JSONDecodeError as e:
                                            logger.error(f"JSON parsing error for {tool_name}: {e}, content: '{content[:100]}'")
                                            updates["redactedContent"] = []
                                elif tool_name == "update_tweets":
                                    # Handle empty content, whitespace, empty arrays
                                    if not content or not isinstance(content, str) or content.strip() == "" or content == "[]":
                                        logger.info(f"No data for {tool_name}, setting empty array")
                                        updates["tweets"] = []
                                    else:
                                        try:
                                            tweets_data = json.loads(content)
                                            updates["tweets"] = [Tweet(**t) for t in tweets_data] if tweets_data else []
                                        except json.JSONDecodeError as e:
                                            logger.error(f"JSON parsing error for {tool_name}: {e}, content: '{content[:100]}'")
                                            updates["tweets"] = []
                                elif tool_name == "update_summary":
                                    updates["summary"] = content if isinstance(content, str) else ""
                            except Exception as e:
                                logger.error(f"Unexpected error processing {tool_name}: {e}")

    logger.info(f"State updates: {list(updates.keys())}")
    return Command(goto="agent", update=updates)


# === Graph Construction ===

def create_graph():
    """Create the LangGraph agent graph."""
    from langgraph.checkpoint.memory import MemorySaver

    tools = [update_findings, update_redacted, update_tweets, update_summary]

    # Create workflow graph
    workflow = StateGraph(FileInvestigatorState)

    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools=tools))
    workflow.add_node("tools_router", tools_router)

    # Agent -> Tools -> Router -> Agent (loop back)
    workflow.add_edge("tools", "tools_router")
    workflow.add_edge("tools_router", "agent")  # Loop back to allow multiple tool calls
    workflow.set_entry_point("agent")

    # Add checkpointer for state persistence
    checkpointer = MemorySaver()
    graph = workflow.compile(checkpointer=checkpointer)

    return graph


# === AG-UI Integration ===

app = FastAPI(title="File Investigator Agent")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://192.168.214.102:3000",
        "http://47.120.47.251:3002",
        "http://47.120.47.251:3003",
        "http://localhost",
        "http://192.168.214.102",
        "http://47.120.47.251",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Create the LangGraph
graph = create_graph()

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    import traceback
    logger = logging.getLogger("agent.error")
    logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}")
    logger.error(traceback.format_exc())
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {type(exc).__name__}: {str(exc)}"}
    )

# Create agent
agent = LangGraphAGUIAgent(
    name="file_investigator",
    graph=graph,
    description="AI-powered document analysis agent with dry humor",
)

# Initialize messages_in_process with safety checks
if not hasattr(agent, 'messages_in_process') or agent.messages_in_process is None:
    agent.messages_in_process = {}

# Add safety wrapper for set_message_in_progress
original_set_message = agent.set_message_in_progress

def safe_set_message_in_progress(run_id, message_data):
    """Safely set message in progress with null checks."""
    if not hasattr(agent, 'messages_in_process') or agent.messages_in_process is None:
        agent.messages_in_process = {}
    if isinstance(agent.messages_in_process, dict):
        agent.messages_in_process[run_id] = message_data

agent.set_message_in_progress = safe_set_message_in_progress

# Add AG-UI endpoint
add_langgraph_fastapi_endpoint(app, agent, path="/copilotkit")


# === Main ===

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
