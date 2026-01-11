# CopilotKit JSON 错误修复

## 问题描述

前端出现错误:
```
Application error: GraphQLError: POST body sent invalid JSON.
```

## 原因

`.env.local` 中配置的外网地址 `http://47.120.47.251:3003` 可能还未配置反向代理,或者前端在尝试连接时出现问题。

## 解决方案

### 1. 恢复本地开发配置

**修改 `.env.local`**:
```bash
# 默认使用本地开发地址
AGENT_URL=http://localhost:8000

# 外网访问时再改为:
# AGENT_URL=http://47.120.47.251:3003
```

### 2. 修复 CopilotKit 配置

**修改 `src/app/api/copilotkit/route.ts`**:
```typescript
file_investigator: new HttpAgent({
  // 优先使用环境变量,否则默认为本地开发地址
  url: process.env.AGENT_URL || "http://localhost:8000",
}),
```

## 环境切换说明

### 本地开发
```bash
# .env.local
AGENT_URL=http://localhost:8000

# 访问: http://localhost:3000 或 http://192.168.214.102:3000
```

### 外网访问
```bash
# .env.local
AGENT_URL=http://47.120.47.251:3003

# 确保反向代理已配置: 47.120.47.251:3003 → 192.168.214.102:8000
# 访问: http://47.120.47.251:3002
```

## 验证

1. 重启前端服务:
```bash
npm run dev
```

2. 检查浏览器控制台,错误应该消失

3. 测试上传文件和 Agent 对话功能

---

**状态**: ✅ 已修复 (本地开发配置)
