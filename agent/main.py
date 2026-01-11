"""File Investigator Agent - LangGraph + AG-UI Protocol + CopilotKit Integration."""

import base64
import json
import logging
import os
import re
import uuid
from typing import List, Optional, Annotated

from dotenv import load_dotenv
from pdf_utils import extract_text_from_pdf, format_extracted_files_as_xml
from pydantic import BaseModel, Field

from ag_ui_langgraph import LangGraphAgent, add_langgraph_fastapi_endpoint

#from copilotkit.integrations.fastapi import add_fastapi_endpoint
#from copilotkit import CopilotKitRemoteEndpoint, LangGraphAgent

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

# === LangGraph and AG-UI Imports ===

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langgraph.types import Command
from langchain_core.messages import ToolMessage, HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool
from langchain_aws import ChatBedrock
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from botocore.config import Config as BotocoreConfig
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from ag_ui_langgraph import LangGraphAgent, add_langgraph_fastapi_endpoint  # Disabled - using copilotkit SDK instead

# === Pydantic Models ===

class Finding(BaseModel):
    """A key finding from document analysis."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = Field(description="Short title of the finding")
    description: str = Field(description="Detailed description")
    severity: str = Field(description="low, medium, high, or critical")


class RedactedItem(BaseModel):
    """A detected redaction with speculation."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    location: str = Field(description="Where in the document (page/section)")
    speculation: str = Field(description="What might be hidden")
    confidence: int = Field(description="Confidence 0-100")


class Tweet(BaseModel):
    """A generated tweet."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    content: str = Field(description="Tweet text (max 280 chars)")
    posted: bool = Field(default=False)


# === LangGraph State Definition ===

class FileInvestigatorState(MessagesState):
    """State for the File Investigator agent."""
    findings: List[Finding]
    redactedContent: List[RedactedItem]
    tweets: List[Tweet]
    summary: str
    uploadedFiles: List[dict]


# === Tool Definitions ===

# Global variables to store pending state updates from tools
_pending_findings = []
_pending_redacted = []
_pending_tweets = []
_pending_summary = ""



@tool
def update_findings(findings_list: dict) -> str:
    """Update the Key Findings panel in the dashboard.

    Args:
        findings_list: Dict containing 'findings' array with title, description, severity

    Returns:
        Success message
    """
    logger = logging.getLogger("agent.frontend")
    findings_data = findings_list.get("findings", []) if isinstance(findings_list, dict) else []

    findings = [
        Finding(
            title=f.get("title", "Untitled"),
            description=f.get("description", ""),
            severity=f.get("severity", "low")
        )
        for f in findings_data
    ]

    logger.info(f"update_findings called with {len(findings)} findings")

    # Store findings in a global variable for the router to pick up
    global _pending_findings
    _pending_findings = findings

    return f"Updated {len(findings)} findings"


@tool
def update_redacted(redacted_list: dict) -> str:
    """Update the Redacted Content panel in the dashboard.

    Args:
        redacted_list: Dict containing 'redacted_items' array with location, speculation, confidence

    Returns:
        Success message
    """
    logger = logging.getLogger("agent.frontend")
    items_data = redacted_list.get("redacted_items", []) if isinstance(redacted_list, dict) else []

    items = [
        RedactedItem(
            location=item.get("location", "Unknown"),
            speculation=item.get("speculation", ""),
            confidence=item.get("confidence", 50)
        )
        for item in items_data
    ]

    logger.info(f"update_redacted called with {len(items)} items")

    # Store in state for the router to pick up
    global _pending_redacted
    _pending_redacted = items

    return f"Updated {len(items)} redacted items"


@tool
def update_tweets(tweets_list: dict) -> str:
    """Update the Tweets panel in the dashboard.

    Args:
        tweets_list: Dict containing 'tweets' array with content

    Returns:
        Success message
    """
    logger = logging.getLogger("agent.frontend")
    tweets_data = tweets_list.get("tweets", []) if isinstance(tweets_list, dict) else []

    tweets = [
        Tweet(
            content=t.get("content", ""),
            posted=False
        )
        for t in tweets_data
    ]

    logger.info(f"update_tweets called with {len(tweets)} tweets")

    # Store in state for the router to pick up
    global _pending_tweets
    _pending_tweets = tweets

    return f"Updated {len(tweets)} tweets"


@tool
def update_summary(summary_content: dict) -> str:
    """Update the Summary panel in the dashboard.

    Args:
        summary_content: Dict containing 'summary' string

    Returns:
        Success message
    """
    logger = logging.getLogger("agent.frontend")
    summary = summary_content.get("summary", "") if isinstance(summary_content, dict) else ""

    logger.info(f"update_summary called with {len(summary)} chars")

    # Store in state for the router to pick up
    global _pending_summary
    _pending_summary = summary

    return "Updated summary"


# === Model Configuration ===

def create_model():
    """Create and configure the LLM model for LangGraph.

    优先级顺序:
    1. OpenAI 兼容配置 (OPENAI_BASE_URL, OPENAI_MODEL)
    2. 自定义 Anthropic 配置 (ANTHROPIC_BASE_URL, ANTHROPIC_AUTH_TOKEN, ANTHROPIC_MODEL)
    3. AWS Bedrock 配置 (MODEL_ID, AWS_REGION)
    """
    logger = logging.getLogger("agent.config")

    # 优先检查 OpenAI 兼容配置
    openai_base_url = os.getenv("OPENAI_BASE_URL")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4")
    openai_api_key = os.getenv("OPENAI_API_KEY", "sk-not-needed")  # 某些兼容端点不需要密钥

    if openai_base_url:
        logger.info(f"使用 OpenAI 兼容 API: {openai_base_url}")
        logger.info(f"模型: {openai_model}")

        model = ChatOpenAI(
            model=openai_model,
            base_url=openai_base_url,
            api_key=openai_api_key,
            temperature=0.7,
            max_tokens=4096,
        )
        return model

    # 检查自定义 Anthropic 配置
    custom_base_url = os.getenv("ANTHROPIC_BASE_URL")
    custom_token = os.getenv("ANTHROPIC_AUTH_TOKEN")
    custom_model = os.getenv("ANTHROPIC_MODEL")

    if custom_base_url and custom_token:
        # 使用自定义 Anthropic API 配置
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
        if os.getenv("ANTHROPIC_API_KEY"):
            model = ChatAnthropic(
                model=model_id,
                temperature=0.7,
                max_tokens=4096,
            )
        else:
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
    """Inject files and analysis state into the prompt."""
    logger = logging.getLogger("agent.context")
    context_parts = []
    extracted_texts = []

    # Process uploaded files
    uploadedFiles = state.get("uploadedFiles", [])
    logger.info(f"📁 收到 {len(uploadedFiles)} 个文件")

    for idx, file_info in enumerate(uploadedFiles):
        file_name = file_info.get("name", "document.pdf")
        base64_data = file_info.get("base64", "")
        file_size = len(base64_data) if base64_data else 0

        logger.info(f"📄 [{idx+1}/{len(uploadedFiles)}] 文件名: {file_name}, Base64 大小: {file_size} 字节")

        if not base64_data:
            logger.warning(f"⚠️  文件 {file_name} 没有 base64 数据,跳过")
            continue

        try:
            pdf_bytes = base64.b64decode(base64_data)
            file_size_mb = len(pdf_bytes) / (1024 * 1024)
            logger.info(f"📦 解码后 PDF 大小: {file_size_mb:.2f} MB")

            extracted = extract_text_from_pdf(pdf_bytes, file_name)
            if extracted:
                text_preview = extracted[:100] if len(extracted) > 100 else extracted
                logger.info(f"✅ 文本提取成功, 预览: {text_preview}...")
                logger.info(f"📝 提取的文本长度: {len(extracted)} 字符")
                extracted_texts.append((file_name, extracted))
            else:
                logger.warning(f"⚠️  文件 {file_name} 文本提取失败")

        except Exception as e:
            logger.error(f"❌ 处理文件 {file_name} 失败: {e}", exc_info=True)
            context_parts.append(f"\n**FILE: {file_name}**\n[Error processing file: {str(e)}]\n")

    if extracted_texts:
        logger.info(f"🔍 extracted_texts 内容: {extracted_texts}")
        xml_content = format_extracted_files_as_xml(extracted_texts)
        context_parts.append(f"\n{xml_content}\n")
        logger.info(f"🎨 已将 {len(extracted_texts)} 个文件格式化为 XML")
        logger.info(f"📄 XML 内容长度: {len(xml_content)} 字符")
        logger.info(f"📋 XML 预览: {xml_content[:500]}...")
    else:
        logger.warning("⚠️  没有成功提取任何文件内容")

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
        logger.info(f"🎯 最终 prompt 长度: {len(full_prompt)} 字符")
    else:
        full_prompt = f"{system_prompt}\n\n## USER MESSAGE:\n{user_message}"
        logger.info(f"🎯 最终 prompt 长度: {len(full_prompt)} 字符 (无文件)")

    return full_prompt


# === LangGraph Nodes ===

def call_model(state: FileInvestigatorState, config) -> Command:
    """Node that calls the LLM model."""
    logger = logging.getLogger("agent.model")

    # Get user message from last message
    messages = state.get("messages", [])
    user_message = ""
    if messages and isinstance(messages[-1], HumanMessage):
        user_message = messages[-1].content

    logger.info(f"=" * 60)
    logger.info(f"🤖 开始处理用户消息")
    logger.info(f"📨 用户消息: {user_message[:100]}{'...' if len(user_message) > 100 else ''}")

    # 记录当前状态
    uploadedFiles = state.get("uploadedFiles", [])
    findings = state.get("findings", [])
    redactedContent = state.get("redactedContent", [])
    tweets = state.get("tweets", [])
    summary = state.get("summary", "")

    logger.info(f"📊 当前状态:")
    logger.info(f"  - 文件数: {len(uploadedFiles)}")
    logger.info(f"  - 发现: {len(findings)} 条")
    logger.info(f"  - 涂黑: {len(redactedContent)} 条")
    logger.info(f"  - 推文: {len(tweets)} 条")
    logger.info(f"  - 摘要: {'有' if summary else '无'}")

    # Build prompt with context
    prompt = build_investigator_prompt(state, user_message)

    # Create model with tools
    model = create_model()
    tools = [update_findings, update_redacted, update_tweets, update_summary]
    model_with_tools = model.bind_tools(tools)

    # Call model
    logger.info(f"🔄 调用模型...")
    logger.info(f"📨 当前消息数量: {len(messages)}")

    # 检查最后一条消息
    if messages:
        last_msg = messages[-1]
        msg_type = type(last_msg).__name__
        logger.info(f"📄 最后一条消息类型: {msg_type}")

        if msg_type == "ToolMessage":
            logger.info(f"🔧 检测到工具执行结果")

    logger.info(f"=" * 60)
    response = model_with_tools.invoke([
        SystemMessage(content=prompt),
        *messages
    ])

    logger.info(f"=" * 60)
    logger.info(f"✅ 模型响应完成")

    # 检查是否有工具调用
    if hasattr(response, 'tool_calls') and response.tool_calls:
        logger.info(f"🔧 模型调用了 {len(response.tool_calls)} 个工具:")
        for i, call in enumerate(response.tool_calls, 1):
            logger.info(f"  {i}. {call.get('name', 'unknown')}")
    else:
        logger.info(f"💬 模型直接回复(无工具调用)")

    logger.info(f"=" * 60)

    # Preserve existing state fields to avoid resetting them
    return {
        "messages": [response],
        # Preserve these fields to prevent them from being reset
        "uploadedFiles": state.get("uploadedFiles", []),
        "findings": state.get("findings", []),
        "redactedContent": state.get("redactedContent", []),
        "tweets": state.get("tweets", []),
        "summary": state.get("summary", ""),
    }


def apply_tool_results(state: FileInvestigatorState) -> Command:
    """Apply pending state updates from tool calls."""
    global _pending_findings, _pending_redacted, _pending_tweets, _pending_summary

    logger = logging.getLogger("agent.state")
    updates = {}
    update_keys = []

    # Log current message state
    messages = state.get("messages", [])
    logger.info(f"📨 apply_tool_results: 当前有 {len(messages)} 条消息")

    # Check if there are any pending tool calls
    pending_tool_calls = []
    for i, msg in enumerate(messages):
        msg_type = type(msg).__name__
        if msg_type == "AIMessage" and hasattr(msg, 'tool_calls') and msg.tool_calls:
            logger.info(f"  [{i}] AIMessage with {len(msg.tool_calls)} tool calls")
            # Track tool call IDs
            for call in msg.tool_calls:
                if 'id' in call:
                    pending_tool_calls.append(call['id'])
                    logger.info(f"      - Tool call ID: {call['id']}")
        elif msg_type == "ToolMessage":
            logger.info(f"  [{i}] ToolMessage (tool_call_id: {getattr(msg, 'tool_call_id', 'N/A')})")
        else:
            logger.info(f"  [{i}] {msg_type}")

    if pending_tool_calls:
        logger.info(f"⚠️ 检测到 {len(pending_tool_calls)} 个待处理的工具调用")

    # Apply pending updates
    if _pending_findings:
        updates["findings"] = _pending_findings
        update_keys.append(f"{len(_pending_findings)} findings")
        _pending_findings = []

    if _pending_redacted:
        updates["redactedContent"] = _pending_redacted
        update_keys.append(f"{len(_pending_redacted)} redacted items")
        _pending_redacted = []

    if _pending_tweets:
        updates["tweets"] = _pending_tweets
        update_keys.append(f"{len(_pending_tweets)} tweets")
        _pending_tweets = []

    if _pending_summary:
        updates["summary"] = _pending_summary
        update_keys.append("summary")
        _pending_summary = ""

    if update_keys:
        logger.info(f"🔄 Applied state updates: {', '.join(update_keys)}")

    # Return Command to update state without modifying messages
    # ToolNode already added ToolMessages to the message list
    return Command(update=updates)


def should_continue(state: FileInvestigatorState) -> str:
    """Determine if we should continue to tools or end."""
    messages = state.get("messages", [])
    logger = logging.getLogger("agent.router")

    if messages:
        last_message = messages[-1]
        logger.info(f"📍 should_continue: 检查最后一条消息类型: {type(last_message).__name__}")

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            logger.info(f"🔧 检测到 {len(last_message.tool_calls)} 个工具调用，路由到 tools")
            return "tools"
        else:
            logger.info(f"✅ 无工具调用，可以结束")

    # IMPORTANT: Always end after generating a response without tool calls
    # This ensures that ag-ui-langgraph sees the complete execution
    logger.info(f"🏁 流程结束")
    return END


# === Graph Construction ===

def create_graph():
    """Create the LangGraph agent graph."""
    from langgraph.checkpoint.memory import MemorySaver

    tools = [update_findings, update_redacted, update_tweets, update_summary]
    tool_node = ToolNode(tools)

    # Create a wrapper function that applies state updates after tool execution
    def tools_with_state_updates(state):
        """Execute tools and apply state updates."""
        # First, execute the tools using standard ToolNode logic
        result = tool_node.invoke(state)

        # Then apply any pending state updates
        global _pending_findings, _pending_redacted, _pending_tweets, _pending_summary

        updates = {}
        if _pending_findings:
            updates["findings"] = _pending_findings
            _pending_findings = []
        if _pending_redacted:
            updates["redactedContent"] = _pending_redacted
            _pending_redacted = []
        if _pending_tweets:
            updates["tweets"] = _pending_tweets
            _pending_tweets = []
        if _pending_summary:
            updates["summary"] = _pending_summary
            _pending_summary = ""

        # Merge the tool node result with our state updates
        if updates:
            result = {**result, **updates}

        return result

    builder = StateGraph(FileInvestigatorState)

    builder.add_node("agent", call_model)
    builder.add_node("tools", tools_with_state_updates)

    builder.add_edge(START, "agent")
    builder.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "__end__": END,
        }
    )
    # After tools execute, go back to agent for final response
    builder.add_edge("tools", "agent")

    # Add checkpointer for state persistence
    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)

    return graph


# === AG-UI Integration ===

# Create FastAPI app
app = FastAPI(title="File Investigator Agent")

# === CORS Configuration ===
# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://192.168.214.102:3000",
        "http://47.120.47.251:3002",
        "http://47.120.47.251:3003",  # 后端自己也可能被访问
        # 开发环境:允许所有本地访问
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

# Add exception handler to ag-ui-langgraph errors
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler to catch and log errors without crashing."""
    import traceback
    logger = logging.getLogger("agent.error")
    logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}")
    logger.error(traceback.format_exc())
    # Return a JSON response even for errors
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {type(exc).__name__}: {str(exc)}"}
    )

# Note: AG-UI automatically handles camelCase <-> snake_case conversion
agent = LangGraphAgent(
    name="file_investigator",
    graph=graph,
    description="AI-powered document analysis agent with dry humor",
)

# Initialize messages_in_process to prevent NoneType error
agent.messages_in_process = {}

# Monkey-patch the agent to fix the NoneType error in ag_ui_langgraph
import types

# Get the original unbound method
original_set_message_in_progress = agent.__class__.set_message_in_progress

def patched_set_message_in_progress(self, run_id=None, metadata=None):
    """Patched version that handles None run_id and missing parameters."""
    logger = logging.getLogger("agent.patch")

    # Handle missing metadata parameter
    if metadata is None:
        logger.warning(f"⚠️ metadata is None, skipping message_in_progress update")
        return

    # Handle missing run_id parameter
    if run_id is None:
        logger.warning(f"⚠️ run_id is None, skipping message_in_progress update")
        return

    # If both parameters are present, call the original function
    try:
        original_set_message_in_progress(self, run_id, metadata)
    except Exception as e:
        logger.error(f"❌ Error in set_message_in_progress: {e}")

# Bind the patched method to the instance
agent.set_message_in_progress = types.MethodType(patched_set_message_in_progress, agent)

logger = logging.getLogger("agent.patch")
logger.info("✅ Applied monkey-patch to fix ag-ui-langgraph NoneType error")

# Add AG-UI endpoint to FastAPI app
add_langgraph_fastapi_endpoint(app, agent, path="/copilotkit")



# === Main ===

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
