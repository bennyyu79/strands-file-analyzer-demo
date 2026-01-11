# 文件调查员 (File Investigator)

基于 AI 的智能文档分析演示项目,集成了 [CopilotKit](https://copilotkit.ai) 和 LangGraph AI Agent,支持 Amazon Bedrock 和 Anthropic Claude。

## 项目简介

**这是什么:**
- 演示如何将 CopilotKit 前端与 Python AI Agent 后端集成的教育项目
- TypeScript 前端 + Python 后端的开发参考示例
- 展示前后端实时状态同步的完整实现

**这不是什么:**
- 生产级文档处理服务
- 敏感文档的安全分析工具
- 专业法律/合规审查的替代品

**可以用来:**
- 学习 CopilotKit + LangGraph 集成模式
- 了解 React 与 Python 之间的状态同步机制
- 掌握多文件文档处理的智能策略

**核心优势:**
- 支持自定义 Anthropic API 配置,灵活选择 AI 模型
- 智能处理大文件(>4.5MB 自动切换文本提取模式)
- 实时仪表板更新,可视化分析结果
- 支持同时分析多达 10 个 PDF 文件

---

## Quick Start

### 环境要求
- Node.js 20+
- Python 3.12+
- AWS Bedrock 访问权限 或 Anthropic API 密钥

### 1. 安装依赖

```bash
npm install
cd agent && uv sync && cd ..
```

### 2. 配置 AI 模型

项目支持两种 AI 模型配置方式:

#### 方式一: 使用 Anthropic Claude (推荐)

创建 `agent/.env`:

```bash
# Anthropic 自定义 API 配置
ANTHROPIC_BASE_URL=https://your-api-endpoint.com/v1
ANTHROPIC_AUTH_TOKEN=your-api-key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# 可选: 默认模型配置
AWS_REGION=us-west-1
MODEL_ID=claude-3-5-sonnet-20241022
```

#### 方式二: 使用 AWS Bedrock

创建 `agent/.env`:

```bash
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-west-1
MODEL_ID=anthropic.claude-haiku-4-5-20251001-v1:0
```

### 3. 启动开发服务器

```bash
npm run dev
```

这将同时启动:
- **前端**: http://localhost:3000
- **AI Agent**: http://localhost:8000

### 4. 访问应用

打开浏览器访问 http://localhost:3000,即可开始使用文件分析功能。

---

## 核心功能

### 📄 多文件 PDF 支持
- 支持上传最多 10 个 PDF 文件(每个最大 150MB)
- 智能文件处理策略:
  - ≤4.5MB 的文件: 保持原生 PDF 格式,保留完整排版和图片
  - >4.5MB 的文件: 自动切换到文本提取模式,突破大小限制
- 跨文档综合分析,发现文件之间的关联和模式

### 📊 实时仪表板更新
- **关键发现**: 自动提取文档中的重要信息和洞察
- **涂黑内容推测**: 识别文档中的涂黑/删减区域,并进行创意推测
- **推文生成**: 生成适合社交媒体传播的病毒式推文
- **执行摘要**: 提供文档集合的整体总结和故事线

### 💬 对话式界面
- 通过聊天界面与 AI Agent 交互
- 实时查看分析进度和结果
- 工具调用以自定义 UI 组件形式展示在聊天中

### 🤖 AI 模型灵活性
- 支持自定义 Anthropic API 配置
- 兼容 AWS Bedrock 服务
- 可根据需求切换不同 Claude 模型版本
- 智能日志过滤,保护敏感数据不被泄露

---

## 技术架构详解

### CopilotKit 核心功能

#### `useCoAgent` - 状态同步

自动保持前端与 Python Agent 的状态同步:

```typescript
const { state, setState } = useCoAgent({
  name: "file_investigator",
  initialState: INITIAL_STATE
});
```

当您在前端上传文件时,文件会立即同步到 Python Agent。当 Agent 更新分析结果时,UI 会立即更新。

**重要性**: 无需手动 API 调用或状态管理 - CopilotKit 通过 AG-UI 协议自动处理双向同步。

#### `CopilotChat` - 对话界面

提供内置工具调用渲染的聊天界面:

```typescript
<CopilotChat
  labels={{
    title: "文件调查员",
    initial: "上传 PDF 开始分析..."
  }}
/>
```

**重要性**: 开箱即用的生产级聊天 UI,支持流式响应和工具调用可视化。

#### `useDefaultTool` - 自定义工具 UI

当 Agent 调用工具时渲染自定义组件:

```typescript
const defaultTools = [
  useDefaultTool({
    toolKey: "update_findings",
    Component: () => <FindingsCard findings={state.findings} />
  })
];
```

**重要性**: 您可以完全控制工具输出在聊天中的展示方式,而不是通用的 JSON 显示。

---

## LangGraph Agent 实现

### 什么是 LangGraph?

[LangGraph](https://langchain-ai.github.io/langgraph/) 是用于构建复杂 AI Agent 工作流的 Python 框架。它提供了:
- 状态管理
- 工具调用循环
- 与 LLM 的集成

### AG-UI Protocol 集成

本项目使用 `ag_ui_langgraph` 库桥接 LangGraph 与 CopilotKit:
- 将 LangGraph Agent 包装为 FastAPI 端点
- 工具调用时自动发送状态更新
- 处理 AG-UI 协议通信

### Agent 工作流程

```python
# 创建 LangGraph 工作流
graph = create_graph()  # 包含 agent → tools → agent 循环

# 包装为 AG-UI Agent
agent = LangGraphAgent(
    name="file_investigator",
    graph=graph,
    description="AI-powered document analysis agent",
)

# 添加到 FastAPI
add_langgraph_fastapi_endpoint(app, agent, path="/copilotkit")
```

### 状态管理

Agent 使用统一的 `FileInvestigatorState` 管理状态:

```python
class FileInvestigatorState(MessagesState):
    findings: List[Finding]        # 关键发现
    redacted: List[RedactedItem]   # 涂黑内容
    tweets: List[Tweet]           # 推文
    summary: str                   # 执行摘要
    uploaded_files: List[dict]     # 上传的文件
```

**重要性**: 工具调用会自动更新状态,并通过 AG-UI 协议同步到前端,无需手动 API 调用。

---

## 多文件 PDF 处理策略

### 挑战

AWS Bedrock 有严格限制:
- 每个文档最大 4.5MB
- 每次请求最多 5 个文档

但用户需要上传大文件和多个文件。

### 解决方案

基于文件大小的智能处理:

1. **小文件 (≤4.5MB)**: 以原生 PDF 格式发送 → 保留完整排版和图片
2. **大文件 (>4.5MB)**: 使用 pypdf 提取文本 → 支持大文件分析
3. **超过 5 个文件**: 额外文件自动使用文本提取 → 遵守 Bedrock 限制

Agent 统一处理所有文件,无论处理方式如何,都能看到完整内容并进行综合分析。

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Next.js 前端                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  文件上传   │  │   仪表板    │  │   CopilotKit 聊天   │  │
│  │  (多文件)   │  │    面板     │  │                     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                           │                                  │
│                    useCoAgent (状态同步)                     │
└───────────────────────────┬─────────────────────────────────┘
                            │ AG-UI 协议 (HTTP + SSE)
┌───────────────────────────┴─────────────────────────────────┐
│                     Python AI Agent                          │
│                                                              │
│           LangGraph + ag_ui_langgraph + FastAPI              │
│                           │                                  │
│         工具: update_findings, update_redacted,              │
│                update_tweets, update_summary                 │
│                           │                                  │
│              AI 模型 (Claude Haiku / Sonnet)                 │
└─────────────────────────────────────────────────────────────┘
```

### 数据流

1. 用户上传 PDF → 前端通过 `useCoAgent` 更新状态
2. 状态自动同步到 Python Agent
3. 用户发送消息 → "分析这些文档"
4. Agent 从状态读取 PDF,调用 AI 模型
5. Agent 调用工具 → `update_findings`, `update_tweets` 等
6. 工具回调发出状态更新
7. 前端接收更新 → 仪表板面板重新渲染

---

## 项目结构

```
├── src/                          # Next.js 前端源码
│   ├── app/
│   │   ├── page.tsx              # 主页面 (useCoAgent + CopilotChat)
│   │   ├── layout.tsx            # CopilotKit 提供器
│   │   └── api/copilotkit/route.ts # 运行时配置
│   ├── components/
│   │   ├── dashboard-panels.tsx  # 仪表板 UI 组件
│   │   ├── file-upload.tsx       # 多文件上传组件
│   │   └── tool-cards.tsx        # 工具 UI 渲染器
│   └── types/
│       └── investigator.ts       # TypeScript 接口定义
├── agent/                        # Python AI Agent
│   ├── main.py                   # LangGraph Agent + AG-UI 集成
│   ├── pdf_utils.py              # PDF 文本提取工具
│   └── pyproject.toml            # Python 依赖配置
├── scripts/                      # 启动脚本
├── public/                       # 静态资源
└── package.json                  # Node.js 依赖配置
```

---

## 环境变量配置

### AI Agent 配置 (`agent/.env`)

#### Anthropic Claude 配置 (推荐)
| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ANTHROPIC_BASE_URL` | 自定义 API 端点 | - |
| `ANTHROPIC_AUTH_TOKEN` | API 密钥 | - |
| `ANTHROPIC_MODEL` | 模型名称 | `claude-3-5-sonnet-20241022` |

#### AWS Bedrock 配置
| 变量 | 说明 | 默认值 |
|------|------|--------|
| `AWS_ACCESS_KEY_ID` | AWS 访问密钥 | - |
| `AWS_SECRET_ACCESS_KEY` | AWS 密钥 | - |
| `AWS_REGION` | AWS 区域 | `us-west-1` |
| `MODEL_ID` | Bedrock 模型 ID | `anthropic.claude-haiku-4-5-20251001-v1:0` |

### 前端配置 (可选)
| 变量 | 说明 | 默认值 |
|------|------|--------|
| `AGENT_URL` | Agent 服务地址 | `http://localhost:8000` |

---

## 技术栈

**前端技术:**
- Next.js 16 - React 框架
- React 19 - UI 库
- CopilotKit 1.10 - AI 对话界面
- Tailwind CSS 4 - 样式框架

**后端技术:**
- Python 3.12 - 编程语言
- LangGraph 0.2.74+ - AI Agent 框架
- AG-UI Protocol 0.1.5+ - 前后端通信协议
- FastAPI + Uvicorn - Web 服务
- pypdf 4.0+ - PDF 文本提取

**AI 模型:**
- Anthropic Claude (Sonnet/Haiku) - 主力模型
- AWS Bedrock - 备选模型服务

---

## 常用命令

| 命令 | 说明 |
|------|------|
| `npm run dev` | 同时启动前端和 Agent |
| `npm run dev:ui` | 仅启动前端 |
| `npm run dev:agent` | 仅启动 Agent |
| `npm run build` | 构建生产版本 |
| `npm run lint` | 运行 ESLint 代码检查 |
| `cd agent && uv run main.py` | 手动启动 Agent 服务 |

---

## 故障排查

### Agent 连接失败
- 确认 Agent 服务运行在 8000 端口
- 检查 `agent/.env` 中的 API 配置是否正确
- 确认 AWS Bedrock 模型访问已启用或 Anthropic API 有效
- 查看 Agent 日志: `cd agent && uv run main.py`

### PDF 处理失败
- 大文件 (>4.5MB) 会自动切换到文本提取模式
- 检查 Agent 日志中的错误信息
- 确认 PDF 未损坏或加密
- 尝试减小文件大小或转换为标准 PDF 格式

### 状态同步问题
- 确认前后端服务都在运行
- 检查浏览器控制台错误信息
- 验证前后端的 Agent 名称一致 (`file_investigator`)
- 检查 CORS 配置是否包含前端地址

### 模型响应问题
- 如果使用自定义 Anthropic API,确认端点和密钥正确
- 检查网络连接和 API 配额
- 查看 Agent 日志中的模型调用错误
- 尝试切换到不同的模型版本

---

## 学习资源

### CopilotKit
- [官方文档](https://docs.copilotkit.ai)
- [useCoAgent 钩子](https://docs.copilotkit.ai/reference/hooks/useCoAgent)
- [AG-UI 协议](https://docs.copilotkit.ai/coagents/ag-ui-protocol)

### LangGraph
- [官方文档](https://langchain-ai.github.io/langgraph/)
- [快速入门](https://langchain-ai.github.io/langgraph/tutorials/)

### Anthropic Claude
- [Claude 模型介绍](https://www.anthropic.com/claude)
- [API 文档](https://docs.anthropic.com/en/api/getting-started)

### AWS Bedrock
- [服务介绍](https://aws.amazon.com/bedrock/)
- [API 参考](https://docs.aws.amazon.com/bedrock/latest/APIReference/)

---

## License

MIT

Built by Mark Morgan
