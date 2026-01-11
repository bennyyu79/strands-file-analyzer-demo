# LangGraph Checkpointer 修复

## 问题描述

后端服务出现错误:
```
ValueError: No checkpointer set
```

## 原因

LangGraph 的 AG-UI 集成需要 checkpointer 来支持状态持久化和会话管理。当调用 `agent.run()` 时,AG-UI 会尝试获取和更新 agent 状态,这需要 checkpointer。

## 解决方案

在 `create_graph()` 函数中添加 `MemorySaver` checkpointer:

**修改前**:
```python
def create_graph():
    """Create the LangGraph agent graph."""
    tools = [update_findings, update_redacted, update_tweets, update_summary]
    tool_node = ToolNode(tools)

    builder = StateGraph(FileInvestigatorState)

    builder.add_node("agent", call_model)
    builder.add_node("tools", tool_node)

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

    graph = builder.compile()  # ❌ 缺少 checkpointer

    return graph
```

**修改后**:
```python
def create_graph():
    """Create the LangGraph agent graph."""
    from langgraph.checkpoint.memory import MemorySaver

    tools = [update_findings, update_redacted, update_tweets, update_summary]
    tool_node = ToolNode(tools)

    builder = StateGraph(FileInvestigatorState)

    builder.add_node("agent", call_model)
    builder.add_node("tools", tool_node)

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

    # Add checkpointer for state persistence
    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)  # ✅ 添加 checkpointer

    return graph
```

## 什么是 Checkpointer?

LangGraph 的 checkpointer 用于:
1. **状态持久化**: 保存对话历史和 agent 状态
2. **会话恢复**: 支持中断后恢复对话
3. **多用户支持**: 通过 thread_id 隔离不同用户的会话
4. **AG-UI 集成**: AG-UI 协议需要 checkpointer 来管理状态

## MemorySaver 说明

- `MemorySaver`: 将状态保存在内存中
- 适合开发和测试
- 生产环境建议使用持久化存储 (如 PostgreSQL、Redis 等)

## 验证

服务重启后,应该能正常处理请求:
```bash
curl http://localhost:8000/
# 返回: {"detail":"Method Not Allowed"} ✅
```

---

**状态**: ✅ 已修复
**文件**: `agent/main.py:469,492`
