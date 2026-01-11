# File Investigator - AI 文档分析演示系统

<div align="center">

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Next.js](https://img.shields.io/badge/Next.js-16.0.7-black)
![Python](https://img.shields.io/badge/Python-3.12+-blue)
![React](https://img.shields.io/badge/React-19.2.0-cyan)

**一个集成 CopilotKit 前端与 Strands Agents 后端的 AI 文档分析系统**

[功能特性](#功能特性) • [快速开始](#快速开始) • [架构设计](#架构设计) • [开发指南](#开发指南)

</div>

---

## 📖 项目简介

File Investigator 是一个创新的双进程 AI 文档分析演示系统，它将 **TypeScript 前端**（基于 CopilotKit）与 **Python 后端**（基于 Strands Agents）完美结合，利用 Amazon Bedrock 提供的 LLM 能力，实现智能 PDF 文档分析。

### 🎯 核心特性

- **🤖 AI 驱动的智能分析**：利用 Claude Haiku 模型进行深度文档分析
- **📊 实时状态同步**：前端与 Agent 之间通过 AG-UI 协议实现双向状态同步
- **📄 多文档并行处理**：支持同时上传最多 10 个 PDF 文件（每个最大 150MB）
- **🎨 现代化 UI 设计**：基于 Next.js 16 和 React 19 构建的响应式界面
- **🔍 智能内容提取**：自动提取 PDF 文本、发现关键信息、推测审查内容
- **🐦 社交媒体集成**：自动生成可分享的推文内容

### 💡 应用场景

- **文档调查**：快速分析大量 PDF 文档，提取关键信息
- **内容审查**：识别文档中的敏感信息和审查内容
- **摘要生成**：自动生成文档执行摘要
- **内容营销**：基于文档内容生成社交媒体内容

---

## ✨ 功能特性

### 📁 文件上传与管理

- **拖拽上传**：直观的拖放界面，支持批量上传
- **智能验证**：自动验证文件类型（仅支持 PDF）和大小限制
- **实时预览**：显示已上传文件列表，支持单独删除
- **大文件处理**：超过 4.5MB 的文件自动使用文本提取模式

### 🎛️ 仪表板面板

系统提供四个智能分析面板：

#### 1. 🔍 关键发现（Key Findings）
- 自动识别文档中的重要信息点
- 按严重程度分级（低、中、高、严重）
- 支持跨文档关联分析

#### 2. 🚫 审查内容（Redacted Content）
- 检测文档中的黑色审查条
- AI 推测被隐藏的内容
- 显示推测置信度百分比

#### 3. 🐦 生成推文（Generated Tweets）
- 基于文档内容自动生成推文
- 支持在线编辑（280 字符限制）
- 一键复制和模拟发布功能

#### 4. 📝 执行摘要（Executive Summary）
- 生成 2-3 句话的文档集合摘要
- Markdown 格式支持
- 多文档综合分析

### 💬 智能对话助手

- 集成 CopilotChat 聊天界面
- 自然语言交互方式
- 上下文感知的智能回复

---

## 🚀 快速开始

### 📋 前置要求

在开始之前，请确保您的系统已安装以下软件：

- **Node.js** 20.0 或更高版本
- **Python** 3.12 或更高版本
- **AWS 账户**并启用 Bedrock 服务
- **uv**（Python 包管理器）

### 🔑 AWS 配置

您需要在 `agent/.env` 文件中配置 AWS 凭证：

```bash
# agent/.env
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-west-1
```

**重要提示**：确保您的 AWS 账户已访问以下 Bedrock 模型：
- `us.anthropic.claude-haiku-4-5-20251001-v1:0`

### 📦 安装与运行

#### 1. 克隆项目

```bash
git clone <repository-url>
cd strands-file-analyzer-demo
```

#### 2. 安装依赖

```bash
# 安装前端依赖
npm install

# 安装后端依赖（首次运行）
cd agent && uv sync && cd ..
```

#### 3. 配置环境变量

```bash
# 在 agent 目录下创建 .env 文件
cat > agent/.env << EOF
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-west-1
EOF
```

#### 4. 启动应用

```bash
# 同时启动前端和后端（推荐）
npm run dev

# 或者分别启动
npm run dev:ui    # 前端：http://localhost:3000
npm run dev:agent # 后端：http://localhost:8000
```

#### 5. 访问应用

打开浏览器访问：**http://localhost:3000**

---

## 🏗️ 架构设计

### 🔄 双进程状态同步

本应用采用创新的 **双进程架构**，通过 AG-UI 协议（HTTP + SSE）实现前后端状态同步：

```
┌─────────────────┐         AG-UI Protocol          ┌─────────────────┐
│   Next.js 前端   │ ◄─────────────────────────────► │  Python Agent   │
│  (React 19)     │                                 │  (Strands)      │
└─────────────────┘                                 └─────────────────┘
       │                                                   │
       │                                                   │
   useCoAgent                                         Agent Tools
       │                                                   │
       └─────────────── 状态自动同步────────────────────────┘
```

#### 状态同步流程

1. **前端 → Agent**：前端调用 `setState()` → 状态通过 AG-UI 协议同步到 Python Agent
2. **Agent 读取**：Agent 在 `state_context_builder` 中通过 `context.input_data.state` 读取状态
3. **Agent 执行**：Agent 调用工具 → `state_from_args` 回调提取状态更新
4. **Agent → 前端**：状态更新流回前端 → UI 自动重新渲染

### 🧩 并行工具调用与状态累加

**核心机制**：Agent 使用 `_state_accumulator`（agent/main.py:378）来合并多个并行工具的更新。

**为什么需要累加器？**

当多个工具在同一 LLM 响应中并行执行时，每个 `state_from_args` 都会看到相同的原始状态（`context.input_data.state`）。如果没有累加器，每个工具都会覆盖前一个工具的更新。

**解决方案**：
```python
# 请求作用域的状态累加器
_state_accumulator: dict = {}

def _get_current_state(context) -> dict:
    """获取合并了当前批次所有更新的状态"""
    base_state = dict(getattr(context.input_data, "state", {}))
    base_state.update(_state_accumulator)  # 合并之前的更新
    return base_state
```

### 📂 目录结构

```
strands-file-analyzer-demo/
├── agent/                      # Python 后端
│   ├── main.py                 # Strands Agent + ag_ui_strands 集成
│   ├── pdf_utils.py            # PDF 文本提取工具
│   └── pyproject.toml          # Python 依赖（uv 管理）
│
├── src/                        # TypeScript 前端
│   ├── app/
│   │   ├── page.tsx            # 主页面：useCoAgent + CopilotChat
│   │   ├── layout.tsx          # CopilotKit Provider 配置
│   │   └── api/copilotkit/     # CopilotKit Runtime 配置
│   │
│   ├── components/
│   │   ├── dashboard-panels.tsx # 四个分析面板组件
│   │   ├── file-upload.tsx      # 多文件上传组件
│   │   └── tool-cards.tsx       # 工具调用自定义渲染
│   │
│   └── types/
│       └── investigator.ts      # FileInvestigatorState 接口定义
│
├── scripts/                    # 启动脚本
│   ├── run-agent.sh           # Linux/macOS Agent 启动脚本
│   └── run-agent.bat          # Windows Agent 启动脚本
│
├── package.json               # Node.js 依赖
├── tsconfig.json              # TypeScript 配置
├── next.config.ts             # Next.js 配置
├── CLAUDE.md                  # Claude Code 项目指令
└── README.md                  # 项目文档（英文）
```

### 🗄️ 数据流图

```
用户上传 PDF
    │
    ▼
前端：FileUpload 组件
    │
    ▼
setState({ uploadedFiles: [...] })
    │
    ▼
AG-UI 协议同步
    │
    ▼
后端：build_investigator_prompt()
    │
    ├─► pdf_utils.py: extract_text_from_pdf()
    │       └─► 使用 pypdf 提取文本
    │
    ├─► 格式化为 XML
    │
    └─► 注入到 Agent Prompt
        │
        ▼
    Agent 调用工具：
    ├─► update_findings()
    ├─► update_redacted()
    ├─► update_tweets()
    └─► update_summary()
        │
        ▼
    state_from_args 回调
    （使用累加器合并更新）
        │
        ▼
    状态通过 AG-UI 返回前端
        │
        ▼
    UI 自动重新渲染
```

---

## 🛠️ 开发指南

### 📝 添加新工具（更新 UI）

当您需要添加能够更新 UI 的新工具时，请按以下步骤操作：

#### 1. 定义 Pydantic 模型（agent/main.py）

```python
from pydantic import BaseModel, Field

class MyNewData(BaseModel):
    """新工具的数据模型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = Field(description="数据标题")
    content: str = Field(description="数据内容")
```

#### 2. 创建工具函数

```python
@tool(
    inputSchema={
        "json": {
            "type": "object",
            "properties": {
                "data_list": {
                    "type": "object",
                    "properties": {
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "content": {"type": "string"}
                                },
                                "required": ["title", "content"]
                            }
                        }
                    },
                    "required": ["items"]
                }
            },
            "required": ["data_list"]
        }
    }
)
def update_my_panel(data_list: dict) -> Optional[str]:
    """更新我的面板"""
    items = data_list.get("items", []) if isinstance(data_list, dict) else []
    logging.getLogger("agent.frontend").info(f"update_my_panel called with {len(items)} items")
    return None
```

#### 3. 创建 state_from_args 函数

```python
async def my_data_state_from_args(context):
    """从 update_my_panel 调用中提取数据并合并到当前状态"""
    try:
        tool_input = context.tool_input
        if isinstance(tool_input, str):
            tool_input = json.loads(tool_input)

        data = tool_input.get("data_list", tool_input)
        raw_items = data.get("items", []) if isinstance(data, dict) else []

        # 确保每个项目都有必需字段
        items = []
        for item in raw_items:
            if isinstance(item, dict):
                items.append({
                    "id": item.get("id", str(uuid.uuid4())[:8]),
                    "title": item.get("title", ""),
                    "content": item.get("content", ""),
                })

        # 添加到累加器以支持并行工具调用
        _accumulate_state_update("myNewData", items)

        # 返回完整的累加状态
        current_state = _get_current_state(context)
        current_state["myNewData"] = items
        return current_state
    except Exception as e:
        logging.getLogger("agent.state").warning(f"my_data_state_from_args failed: {e}")
        return None
```

#### 4. 添加到工具行为配置

```python
config = StrandsAgentConfig(
    state_context_builder=build_investigator_prompt,
    tool_behaviors={
        # ... 现有工具
        "update_my_panel": ToolBehavior(
            skip_messages_snapshot=True,
            state_from_args=my_data_state_from_args,
        ),
    },
)
```

#### 5. 添加到 Agent

```python
strands_agent = Agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[
        # ... 现有工具
        update_my_panel,
    ],
)
```

#### 6. 更新前端

##### a. 更新 TypeScript 接口（src/types/investigator.ts）

```typescript
export interface MyNewData {
  id: string;
  title: string;
  content: string;
}

export interface FileInvestigatorState {
  // ... 现有属性
  myNewData: MyNewData[];
}
```

##### b. 更新初始状态

```typescript
export const INITIAL_STATE: FileInvestigatorState = {
  // ... 现有属性
  myNewData: [],
};
```

##### c. 创建面板组件（src/components/dashboard-panels.tsx）

```typescript
interface MyNewPanelProps {
  items: MyNewData[];
}

export function MyNewPanel({ items }: MyNewPanelProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
      <h2 className="text-lg font-semibold mb-4">My New Panel</h2>
      {items.length === 0 ? (
        <p className="text-slate-400">No data yet...</p>
      ) : (
        <div className="space-y-2">
          {items.map((item) => (
            <div key={item.id} className="border border-slate-100 rounded p-3">
              <h3 className="font-medium">{item.title}</h3>
              <p className="text-sm text-slate-600">{item.content}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

##### d. 在页面中使用（src/app/page.tsx）

```typescript
import { MyNewPanel } from "@/components/dashboard-panels";

export default function FileInvestigatorPage() {
  // ... 现有代码

  return (
    <div>
      {/* ... 现有 UI */}
      <MyNewPanel items={state.myNewData} />
    </div>
  );
}
```

### 🎨 前端开发

#### 状态管理

状态通过 `useCoAgent` hook 管理：

```typescript
const { state, setState } = useCoAgent<FileInvestigatorState>({
  name: "file_investigator",
  initialState: INITIAL_STATE,
});
```

**重要原则**：
- Agent 自动通过 `context.input_data.state` 接收新状态
- 只需在前端更新状态，Agent 会自动同步
- UI 从状态派生，状态更新时自动重新渲染

### 🔧 后端开发

#### PDF 处理策略

所有 PDF 都使用文本提取（pypdf）而非 Bedrock 文档块：

**为什么？**
- Bedrock 在整个对话历史中有 5 文档限制
- 文本提取避免了这个限制
- 对于大型文档集更可靠

**实现位置**：`build_investigator_prompt()` (agent/main.py:299)

#### 日志管理

项目使用自定义日志过滤器来处理二进制数据：

```python
class BinaryDataRedactingFilter(logging.Filter):
    """从日志消息中审查二进制/base64 数据"""
    # ... 实现
```

这可以防止 base64 blob 淹没日志。

---

## ⚠️ 重要注意事项

### 🔑 工具输入是 dict，不是 Pydantic 模型

ag_ui_strands 将 dict 传递给工具，而不是 Pydantic 模型。请参阅 agent/main.py:165。

### 🔄 状态累加器是请求作用域的

如果需要，必须通过 `_reset_state_accumulator()` 重置。

### 📝 二进制数据审查

日志过滤器防止 base64 blob 淹没日志（agent/main.py:11-95）。

### 📦 Next.js 外部包

`pino` 和 `thread-stream` 在 next.config.ts 中标记为外部。

### 🚫 并行工具调用注意事项

**关键**：当多个 `update_*` 工具在同一 LLM 响应中被并行调用时，每个 `state_from_args` 都会看到来自 `context.input_data.state` 的相同原始状态。如果没有累加器，每个都会覆盖前一个的更新。

**解决方案**：使用请求作用域的累加器模式来跟踪待处理的更新。

---

## 📚 技术栈

### 前端

- **框架**：Next.js 16.0.7
- **UI 库**：React 19.2.0
- **AI 集成**：CopilotKit 1.10.6
- **状态管理**：@ag-ui/core 0.0.41
- **样式**：Tailwind CSS 4
- **类型检查**：TypeScript 5.9.3
- **Markdown 渲染**：react-markdown 10.1.0

### 后端

- **框架**：FastAPI（通过 uvicorn）
- **AI Agent**：Strands Agents
- **协议**：ag_ui_strands 0.0.41
- **PDF 处理**：pypdf
- **LLM**：Amazon Bedrock (Claude Haiku)
- **包管理**：uv

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 🤝 贡献指南

我们欢迎各种形式的贡献！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 [Issue](https://github.com/your-repo/issues)
- 发起 [Discussion](https://github.com/your-repo/discussions)
- 邮件：your-email@example.com

---

## 🙏 致谢

- [CopilotKit](https://copilotkit.ai/) - 强大的 AI 集成框架
- [Strands](https://strands.ai/) - 灵活的 AI Agent 框架
- [Amazon Bedrock](https://aws.amazon.com/bedrock/) - 托管的 LLM 服务
- [Next.js](https://nextjs.org/) - React 框架

---

<div align="center">

**Made with ❤️ by the File Investigator Team**

[⬆ 返回顶部](#file-investator---ai-文档分析演示系统)

</div>
