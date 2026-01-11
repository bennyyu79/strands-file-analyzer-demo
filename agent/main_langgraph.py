"""File Investigator Agent - LangGraph + AG-UI + CopilotKit Integration."""

import base64
import json
import logging
import os
import re
import uuid
from typing import List, Optional, TypedDict, Annotated
from langchain_core.runnables import RunnableConfig

# LangGraph and LangChain imports
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langgraph.types import Command
from langchain_core.messages import ToolMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_aws import ChatBedrock
from langchain_anthropic import ChatAnthropic
from botocore.config import Config as BotocoreConfig

# FastAPI and Pydantic
from fastapi import FastAPI
from pydantic import BaseModel


class StateUpdate(BaseModel):
    """Simple state update response for API."""
    state: dict

# PDF processing
from dotenv import load_dotenv
from pdf_utils import extract_text_from_pdf, format_extracted_files_as_xml
from pydantic import BaseModel, Field

load_dotenv()

# === Logging Configuration ===

class BinaryDataRedactingFilter(logging.Filter):
    """Redact binary/base64 data from log messages to keep logs readable."""

    BASE64_PATTERN = re.compile(r'[A-Za-z0-9+/=]{100,}')
    BYTES_LITERAL_PATTERN = re.compile(r"b'[^']{50,}'")
    HEX_ESCAPE_PATTERN = re.compile(r'(\\x[0-9a-fA-F]{2}){20,}')
    PDF_STREAM_PATTERN = re.compile(r'stream\s*[\s\S]{100,}?\s*endstream', re.IGNORECASE)

    def _redact(self, text: str) -> str:
        """Redact binary blobs from text."""
        if not isinstance(text, str):
            text = str(text)
        text = self.BASE64_PATTERN.sub('[BASE64_DATA]', text)
        text = self.BYTES_LITERAL_PATTERN.sub("[BYTES_DATA]", text)
        text = self.HEX_ESCAPE_PATTERN.sub('[HEX_DATA]', text)
        text = self.PDF_STREAM_PATTERN.sub('[PDF_STREAM]', text)
        return text

    def filter(self, record):
        try:
            if hasattr(record, 'msg') and isinstance(record.msg, str):
                record.msg = self._redact(record.msg)
            if hasattr(record, 'args') and record.args:
                if isinstance(record.args, dict):
                    record.args = {k: self._redact(v) if isinstance(v, str) else v
                                  for k, v in record.args.items()}
                elif isinstance(record.args, tuple):
                    record.args = tuple(self._redact(a) if isinstance(a, str) else a
                                       for a in record.args)
        except Exception:
            pass
        return True


class RedactingFormatter(logging.Formatter):
    """Formatter that redacts binary data from final formatted message."""

    REDACT_PATTERNS = [
        (re.compile(r'[A-Za-z0-9+/=]{100,}'), '[BASE64_DATA]'),
        (re.compile(r"b'[^']{50,}'"), '[BYTES_DATA]'),
        (re.compile(r'(\\x[0-9a-fA-F]{2}){20,}'), '[HEX_DATA]'),
    ]

    def format(self, record):
        result = super().format(record)
        for pattern, replacement in self.REDACT_PATTERNS:
            result = pattern.sub(replacement, result)
        return result


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(name)s - %(message)s",
)

redact_filter = BinaryDataRedactingFilter()
redact_formatter = RedactingFormatter("%(levelname)s - %(name)s - %(message)s")
for handler in logging.root.handlers:
    handler.addFilter(redact_filter)
    handler.setFormatter(redact_formatter)

logging.getLogger("langgraph").setLevel(logging.INFO)
logging.getLogger("langchain").setLevel(logging.INFO)
logging.getLogger("agent").setLevel(logging.DEBUG)

# === Pydantic Models for Tool Arguments ===

class Finding(BaseModel):
    """A key finding from document analysis."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = Field(description="Short title of the finding")
    description: str = Field(description="Detailed description")
    severity: str = Field(description="low, medium, high, or critical")


class FindingsList(BaseModel):
    """List of findings to update in UI."""
    findings: List[Finding] = Field(description="List of key findings")


class RedactedItem(BaseModel):
    """A detected redaction with speculation."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    location: str = Field(description="Where in the document (page/section)")
    speculation: str = Field(description="What might be hidden")
    confidence: int = Field(description="Confidence 0-100")


class RedactedList(BaseModel):
    """List of redacted content."""
    redacted_items: List[RedactedItem] = Field(description="Found redactions")


class Tweet(BaseModel):
    """A generated tweet."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    content: str = Field(description="Tweet text (max 280 chars)")
    posted: bool = Field(default=False)


class TweetsList(BaseModel):
    """List of tweets."""
    tweets: List[Tweet] = Field(description="Generated tweets")


class SummaryContent(BaseModel):
    """Summary content."""
    summary: str = Field(description="Executive summary text")


# === LangGraph State Definition ===

class FileInvestigatorState(MessagesState):
    """State for the File Investigator agent."""
    # Findings panel data
    findings: List[Finding]
    # Redacted content panel data
    redacted: List[RedactedItem]
    # Tweets panel data
    tweets: List[Tweet]
    # Summary panel data
    summary: str
    # Uploaded files from frontend
    uploaded_files: List[dict]


# === Tool Definitions for LangGraph ===

def update_state_from_result(field_name: str, data):
    """Helper function to create Command that updates state."""
    return Command(update={
        field_name: data,
        "messages": [
            ToolMessage(
                content=f"Successfully updated {field_name}",
                tool_call_id="",  # Will be filled by ToolNode
            )
        ]
    })


@tool
def update_findings(findings_list: dict) -> Command:
    """Update the Key Findings panel in the dashboard.

    Args:
        findings_list: Dict containing 'findings' array with title, description, severity

    Returns:
        Command to update the findings state
    """
    logger = logging.getLogger("agent.frontend")
    findings_data = findings_list.get("findings", []) if isinstance(findings_list, dict) else []

    # Convert to Finding objects
    findings = [
        Finding(
            title=f.get("title", "Untitled"),
            description=f.get("description", ""),
            severity=f.get("severity", "low")
        )
        for f in findings_data
    ]

    logger.info(f"update_findings called with {len(findings)} findings")

    # Return Command to update state
    return Command(update={
        "findings": findings,
        "messages": [
            ToolMessage(
                content=f"Updated {len(findings)} findings",
                tool_call_id="",  # Will be filled by ToolNode
            )
        ]
    })


@tool
def update_redacted(redacted_list: dict) -> Command:
    """Update the Redacted Content panel in the dashboard.

    Args:
        redacted_list: Dict containing 'redacted_items' array with location, speculation, confidence

    Returns:
        Command to update the redacted state
    """
    logger = logging.getLogger("agent.frontend")
    items_data = redacted_list.get("redacted_items", []) if isinstance(redacted_list, dict) else []

    # Convert to RedactedItem objects
    items = [
        RedactedItem(
            location=item.get("location", "Unknown"),
            speculation=item.get("speculation", ""),
            confidence=item.get("confidence", 50)
        )
        for item in items_data
    ]

    logger.info(f"update_redacted called with {len(items)} items")

    return Command(update={
        "redacted": items,
        "messages": [
            ToolMessage(
                content=f"Updated {len(items)} redacted items",
                tool_call_id="",
            )
        ]
    })


@tool
def update_tweets(tweets_list: dict) -> Command:
    """Update the Tweets panel in the dashboard.

    Args:
        tweets_list: Dict containing 'tweets' array with content

    Returns:
        Command to update the tweets state
    """
    logger = logging.getLogger("agent.frontend")
    tweets_data = tweets_list.get("tweets", []) if isinstance(tweets_list, dict) else []

    # Convert to Tweet objects
    tweets = [
        Tweet(
            content=t.get("content", ""),
            posted=False
        )
        for t in tweets_data
    ]

    logger.info(f"update_tweets called with {len(tweets)} tweets")

    return Command(update={
        "tweets": tweets,
        "messages": [
            ToolMessage(
                content=f"Updated {len(tweets)} tweets",
                tool_call_id="",
            )
        ]
    })


@tool
def update_summary(summary_content: dict) -> Command:
    """Update the Summary panel in the dashboard.

    Args:
        summary_content: Dict containing 'summary' string

    Returns:
        Command to update the summary state
    """
    logger = logging.getLogger("agent.frontend")
    summary = summary_content.get("summary", "") if isinstance(summary_content, dict) else ""

    logger.info(f"update_summary called with {len(summary)} chars")

    return Command(update={
        "summary": summary,
        "messages": [
            ToolMessage(
                content="Updated summary",
                tool_call_id="",
            )
        ]
    })


# === Model Configuration ===

def create_model():
    """Create and configure the LLM model for LangGraph.

    优先使用 .env 中的自定义 Anthropic 配置:
    - ANTHROPIC_BASE_URL: 自定义 API 端点
    - ANTHROPIC_AUTH_TOKEN: API 密钥
    - ANTHROPIC_MODEL: 模型名称
    """
    # 优先检查自定义 Anthropic 配置
    custom_base_url = os.getenv("ANTHROPIC_BASE_URL")
    custom_token = os.getenv("ANTHROPIC_AUTH_TOKEN")
    custom_model = os.getenv("ANTHROPIC_MODEL")

    if custom_base_url and custom_token:
        # 使用自定义 Anthropic API 配置
        logger = logging.getLogger("agent.config")
        logger.info(f"使用自定义 Anthropic API: {custom_base_url}")

        model = ChatAnthropic(
            model=custom_model or "claude-3-5-sonnet-20241022",
            api_key=custom_token,
            base_url=custom_base_url,
            temperature=0.7,
            max_tokens=4096,
        )
        return model

    # 回退到原有配置逻辑
    region = os.getenv("AWS_REGION", "us-west-1")
    model_id = os.getenv("MODEL_ID", "anthropic.claude-haiku-4-5-20251001-v1:0")

    if model_id.startswith("openai."):
        # Using OpenAI compatible model via Bedrock
        boto_config = BotocoreConfig(
            region_name=region,
            connect_timeout=300,
            read_timeout=300,
        )
        model = ChatBedrock(
            model_id=model_id,
            region_name=region,
            model_kwargs={"temperature": 0.7},
            boto_config=boto_config,
        )
    elif model_id.startswith("claude-") or "anthropic" in model_id.lower():
        # Using Anthropic Claude via Bedrock or directly
        if os.getenv("ANTHROPIC_API_KEY"):
            # Direct Anthropic API
            model = ChatAnthropic(
                model=model_id,
                temperature=0.7,
                max_tokens=4096,
            )
        else:
            # Via Bedrock
            boto_config = BotocoreConfig(
                region_name=region,
                connect_timeout=300,
                read_timeout=300,
            )
            model = ChatBedrock(
                model_id=model_id,
                region_name=region,
                temperature=0.7,
                max_tokens=4096,
                boto_config=boto_config,
            )
    else:
        # Default to Bedrock
        boto_config = BotocoreConfig(
            region_name=region,
            connect_timeout=300,
            read_timeout=300,
        )
        model = ChatBedrock(
            model_id=model_id,
            region_name=region,
            temperature=0.7,
            max_tokens=4096,
            boto_config=boto_config,
        )

    return model


# === Prompt Building ===

def build_investigator_prompt(state: FileInvestigatorState, user_message: str) -> str:
    """Inject files and analysis state into the prompt.

    Always extracts text from PDFs - never uses Bedrock document blocks.
    This avoids Bedrock's 5-document limit which applies across conversation history.
    """
    logger = logging.getLogger("agent.context")
    context_parts = []
    extracted_texts = []

    # Process uploaded files
    uploaded_files = state.get("uploaded_files", [])

    for file_info in uploaded_files:
        file_name = file_info.get("name", "document.pdf")
        base64_data = file_info.get("base64", "")

        if not base64_data:
            continue

        try:
            pdf_bytes = base64.b64decode(base64_data)
            file_size_mb = len(pdf_bytes) / (1024 * 1024)
            logger.debug(f"Processing {file_name} ({file_size_mb:.2f} MB)")

            extracted = extract_text_from_pdf(pdf_bytes)
            extracted_texts.append((file_name, extracted))

        except Exception as e:
            logger.error(f"Failed to process {file_name}: {e}", exc_info=True)
            context_parts.append(f"\n**FILE: {file_name}**\n[Error processing file: {str(e)}]\n")

    if extracted_texts:
        xml_content = format_extracted_files_as_xml(extracted_texts)
        context_parts.append(f"\n{xml_content}\n")

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
        full_prompt = f"{system_prompt}\n\n## DOCUMENTS TO ANALYZE:\n{''.join(context_parts)}\n\n## USER MESSAGE:\n{user_message}"
    else:
        full_prompt = f"{system_prompt}\n\n## USER MESSAGE:\n{user_message}"

    return full_prompt


# === LangGraph Nodes ===

def call_model(state: FileInvestigatorState, config: RunnableConfig) -> Command:
    """Node that calls the LLM model.

    Args:
        state: Current agent state
        config: Runtime configuration

    Returns:
        Command with model response
    """
    logger = logging.getLogger("agent.model")

    # Get user message from last message
    messages = state.get("messages", [])
    user_message = ""
    if messages and isinstance(messages[-1], HumanMessage):
        user_message = messages[-1].content

    # Build prompt with context
    prompt = build_investigator_prompt(state, user_message)

    # Create model with tools
    model = create_model()
    tools = [update_findings, update_redacted, update_tweets, update_summary]
    model_with_tools = model.bind_tools(tools)

    # Call model
    logger.info(f"Calling model with {len(messages)} messages")
    response = model_with_tools.invoke([
        SystemMessage(content=prompt),
        *messages
    ])

    return {"messages": [response]}


def should_continue(state: FileInvestigatorState) -> str:
    """Determine if we should continue to tools or end.

    Args:
        state: Current agent state

    Returns:
        "tools" if last message has tool calls, "end" otherwise
    """
    messages = state.get("messages", [])
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
    return END


# === Graph Construction ===

def create_graph():
    """Create the LangGraph agent graph.

    Returns:
        Compiled LangGraph
    """
    # Create tool node
    tools = [update_findings, update_redacted, update_tweets, update_summary]
    tool_node = ToolNode(tools)

    # Create state graph
    builder = StateGraph(FileInvestigatorState)

    # Add nodes
    builder.add_node("agent", call_model)
    builder.add_node("tools", tool_node)

    # Add edges
    builder.add_edge(START, "agent")
    builder.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "__end__": END,
        }
    )
    builder.add_edge("tools", "agent")

    # Compile graph
    graph = builder.compile()

    return graph


# === FastAPI Integration ===

app = FastAPI(title="File Investigator Agent (LangGraph)")

# Create the graph
graph = create_graph()


@app.post("/invoke")
async def invoke_agent(request: dict):
    """Invoke the agent with state and message.

    Expected request format:
    {
        "state": {
            "uploaded_files": [...],
            "findings": [...],
            "redacted": [...],
            "tweets": [...],
            "summary": "..."
        },
        "message": "User message to the agent"
    }
    """
    logger = logging.getLogger("agent.api")

    # Extract state and message from request
    state_data = request.get("state", {})
    user_message = request.get("message", "")

    # Build initial state
    initial_state = FileInvestigatorState(
        messages=[HumanMessage(content=user_message)],
        findings=state_data.get("findings", []),
        redacted=state_data.get("redacted", []),
        tweets=state_data.get("tweets", []),
        summary=state_data.get("summary", ""),
        uploaded_files=state_data.get("uploaded_files", []),
    )

    logger.info(f"Invoking agent with {len(initial_state['uploaded_files'])} files")

    # Invoke graph
    try:
        result = graph.invoke(initial_state)

        # Extract updated state
        updated_state = {
            "findings": [f.model_dump() for f in result.get("findings", [])],
            "redacted": [r.model_dump() for r in result.get("redacted", [])],
            "tweets": [t.model_dump() for t in result.get("tweets", [])],
            "summary": result.get("summary", ""),
        }

        logger.info("Agent invocation successful")

        return StateUpdate(state=updated_state)

    except Exception as e:
        logger.error(f"Agent invocation failed: {e}", exc_info=True)
        return {"error": str(e)}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "framework": "langgraph"}


# === Main ===

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main_langgraph:app", host="0.0.0.0", port=8000, reload=True)
