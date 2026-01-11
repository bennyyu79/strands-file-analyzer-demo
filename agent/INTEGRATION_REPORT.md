# 前后端配置检查报告

**检查时间**: 2026-01-10
**架构**: LangGraph + AG-UI Protocol + CopilotKit

---

## ✅ 配置完成状态

### 1. 后端配置 (Agent)

| 组件 | 状态 | 说明 |
|------|------|------|
| **框架** | ✅ LangGraph | 使用 LangGraph 构建 Agent 图 |
| **协议** | ✅ AG-UI | 通过 `ag-ui-langgraph` 集成 |
| **模型配置** | ✅ 自定义 API | 支持 `.env` 自定义 Anthropic 端点 |
| **FastAPI** | ✅ 已集成 | 使用 `add_langgraph_fastapi_endpoint` |
| **端口** | ✅ 8000 | 监听 0.0.0.0:8000 |
| **状态同步** | ✅ 自动 | AG-UI 协议自动处理 |

**文件**: `agent/main.py`

```python
# 关键配置
from ag_ui_langgraph import LangGraphAgent, add_langgraph_fastapi_endpoint

app = FastAPI(title="File Investigator Agent")
agent = LangGraphAgent(name="file_investigator", graph=graph)
add_langgraph_fastapi_endpoint(app, agent, path="/")
```

### 2. 前端配置 (Next.js + CopilotKit)

| 组件 | 状态 | 说明 |
|------|------|------|
| **框架** | ✅ Next.js 16 | React Server Components |
| **Agent 库** | ✅ @copilotkit/react-core | 使用 `useCoAgent` hook |
| **UI 库** | ✅ @copilotkit/react-ui | CopilotChat 组件 |
| **AG-UI 客户端** | ✅ @ag-ui/client | HttpAgent 连接后端 |
| **Agent URL** | ✅ localhost:8000 | 环境变量或默认值 |
| **状态管理** | ✅ useCoAgent | 自动同步前后端状态 |

**文件**: `src/app/api/copilotkit/route.ts`

```typescript
import { HttpAgent } from "@ag-ui/client";

const runtime = new CopilotRuntime({
  agents: {
    file_investigator: new HttpAgent({
      url: process.env.AGENT_URL || "http://localhost:8000",
    }),
  },
});
```

**文件**: `src/app/page.tsx`

```typescript
const { state, setState } = useCoAgent<FileInvestigatorState>({
  name: "file_investigator",
  initialState: INITIAL_STATE,
});
```

### 3. 依赖配置

#### Python (agent/pyproject.toml)

```toml
dependencies = [
    "ag-ui-protocol>=0.1.5",
    "ag-ui-langgraph==0.0.23",      # ✅ 新增
    "fastapi>=0.115.12",
    "uvicorn>=0.34.3",
    "langgraph>=0.2.74",
    "langchain-anthropic>=0.1.0",
    # ... 其他依赖
]
```

#### Node.js (package.json)

```json
{
  "dependencies": {
    "@ag-ui/client": "^0.0.41",
    "@ag-ui/core": "^0.0.41",
    "@ag-ui/langgraph": "^0.0.18",
    "@copilotkit/react-core": "1.10.6",
    "@copilotkit/react-ui": "1.10.6",
    "@copilotkit/runtime": "1.10.6"
  }
}
```

---

## 🔄 数据流

```
用户操作 → 前端 (CopilotKit)
    ↓
POST /api/copilotkit (Next.js API Route)
    ↓
HttpAgent → http://localhost:8000 (AG-UI Protocol)
    ↓
LangGraph Agent → 处理消息
    ↓
调用工具 (update_findings, update_redacted, etc.)
    ↓
更新 State → AG-UI 协议自动同步
    ↓
前端接收更新 → useCoAgent state 更新
    ↓
UI 重新渲染 (Dashboard 面板)
```

---

## 🎯 配置映射表

| 前端 State | 后端 State | AG-UI 映射 | 状态 |
|------------|------------|------------|------|
| `findings` | `findings: List[Finding]` | ✅ 自动 | ✅ |
| `redactedContent` | `redacted: List[RedactedItem]` | ⚠️ 字段名不同 | ⚠️ |
| `tweets` | `tweets: List[Tweet]` | ✅ 自动 | ✅ |
| `summary` | `summary: str` | ✅ 自动 | ✅ |
| `uploadedFiles` | `uploaded_files: List[dict]` | ⚠️ 命名风格 | ✅ |

---

## ⚠️ 发现的问题

### 1. 字段名不匹配

**问题**: 前端使用 `redactedContent`,后端使用 `redacted`

**前端** (`src/types/investigator.ts`):
```typescript
redactedContent: RedactedItem[]
```

**后端** (`agent/main.py`):
```python
redacted: List[RedactedItem]
```

**解决方案**: 需要统一字段名,建议在前端使用 `redacted` 与后端保持一致

### 2. 测试建议

启动完整应用测试:

```bash
# 1. 启动后端 (已在运行)
cd agent
uv run python main.py

# 2. 启动前端
cd ..
npm run dev

# 3. 测试流程
# - 打开 http://localhost:3000
# - 上传 PDF 文件
# - 发送消息给 Agent
# - 检查 4 个面板是否更新
```

---

## ✅ 完成清单

- [x] 后端使用 LangGraph
- [x] 后端集成 AG-UI 协议
- [x] 后端支持自定义 Anthropic API
- [x] 前端使用 CopilotKit + AG-UI 客户端
- [x] 前后端端口配置一致
- [x] 依赖包安装完成
- [ ] 字段名统一 (redactedContent → redacted)
- [ ] 完整集成测试

---

## 📝 下一步

1. **统一字段名**: 修改前端 `redactedContent` 为 `redacted`
2. **启动测试**: 运行 `npm run dev` 测试完整流程
3. **验证状态同步**: 确认工具调用后前端状态正确更新
4. **错误处理**: 添加适当的错误处理和用户反馈

---

**状态**: ✅ 配置基本完成,待完整集成测试
