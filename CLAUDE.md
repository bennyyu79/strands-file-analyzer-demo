# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered document analysis demo that integrates **CopilotKit** (TypeScript frontend) with **Strands Agents** (Python backend) using Amazon Bedrock for LLM capabilities. Users upload PDFs which are analyzed by an agent that populates dashboard panels with findings, redacted content speculation, tweets, and summaries.

**Architecture Pattern**: Dual-process application with real-time state synchronization via AG-UI Protocol (HTTP + SSE). Frontend state automatically syncs to Python agent; when agent calls tools, state updates flow back to frontend.

## Development Commands

```bash
# Start both frontend and agent (recommended)
npm run dev

# Start frontend only (Next.js on :3000)
npm run dev:ui

# Start agent only (Python FastAPI on :8000)
npm run dev:agent

# Build for production
npm run build

# Run linter
npm run lint
```

**Agent setup** (first time only):
```bash
cd agent && uv sync && cd ..
```

## Prerequisites & Environment

- Node.js 20+, Python 3.12+
- AWS credentials in `agent/.env`: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`
- Bedrock model access: `us.anthropic.claude-haiku-4-5-20251001-v1:0`

## Key Architecture Concepts

### Dual-Process State Sync

The application uses `useCoAgent` hook to maintain shared state between frontend and agent:

1. Frontend calls `setState()` → state syncs to Python agent via AG-UI Protocol
2. Agent reads state via `context.input_data.state` in `state_context_builder`
3. Agent calls tools → `state_from_args` callbacks extract state updates
4. Updates flow back to frontend → UI re-renders automatically

**Critical for parallel tool calls**: The agent uses `_state_accumulator` (agent/main.py:378) to merge updates when multiple tools execute simultaneously. Without this, each `state_from_args` would overwrite previous updates.

### Tool Behavior Configuration

Each UI-updating tool in agent/main.py has a `ToolBehavior`:
- `skip_messages_snapshot=True`: prevents tool from being added to conversation history
- `state_from_args`: async function that extracts state updates from tool arguments

The `state_from_args` functions must:
- Read from `context.input_data.state` (original state)
- Merge with `_state_accumulator` (previous updates in same batch)
- Return complete merged state object

### PDF Processing Strategy

All PDFs use text extraction (pypdf) rather than Bedrock document blocks. This avoids Bedrock's 5-document limit across conversation history. See `build_investigator_prompt()` (agent/main.py:299) and `pdf_utils.py`.

## Directory Structure

```
src/
├── app/
│   ├── page.tsx                 # Main page with useCoAgent + CopilotChat
│   ├── layout.tsx               # CopilotKit provider setup
│   └── api/copilotkit/route.ts  # CopilotKit runtime configuration
├── components/
│   ├── dashboard-panels.tsx     # FindingsPanel, RedactedPanel, TweetsPanel, SummaryPanel
│   ├── file-upload.tsx          # Multi-file upload (max 10 files, 150MB each)
│   └── tool-cards.tsx           # Custom UI for tool call rendering
└── types/
    └── investigator.ts          # FileInvestigatorState interface

agent/
├── main.py                      # Strands agent + ag_ui_strands integration
├── pdf_utils.py                 # PDF text extraction utilities
└── pyproject.toml               # Python dependencies (uv-managed)
```

## Agent Development

When adding new tools that update UI:

1. Define Pydantic models for tool arguments (agent/main.py:113-162)
2. Create `@tool` function with JSON schema for input validation
3. Create `*_state_from_args` async function to extract state updates
4. Add to `StrandsAgentConfig.tool_behaviors` (agent/main.py:531-548)
5. Add `useDefaultTool` in frontend (src/app/page.tsx:94-103)

**Remember**: State updates from parallel tools must use the accumulator pattern to avoid overwriting each other.

## Frontend Development

State is managed through `useCoAgent` hook. When adding new state properties:
1. Update `FileInvestigatorState` interface (src/types/investigator.ts)
2. Update `INITIAL_STATE` constant
3. Add corresponding panel component in dashboard-panels.tsx
4. Agent automatically receives new state via `context.input_data.state`

## Important Gotchas

- **Tool input is dict, not Pydantic model**: ag_ui_strands passes dict to tools, not the Pydantic models (see agent/main.py:165)
- **State accumulator is request-scoped**: Must be reset via `_reset_state_accumulator()` if needed
- **Binary data redaction**: Logging filters prevent base64 blobs from flooding logs (agent/main.py:11-95)
- **Next.js external packages**: `pino` and `thread-stream` marked as external in next.config.ts
