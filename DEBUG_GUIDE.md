# PDF 上传调试指南

**更新时间**: 2026-01-10

---

## 🐛 前端调试日志已添加

已在以下文件中添加详细的调试日志:

### 1. 主页面 (`src/app/page.tsx`)

#### 全局网络拦截器
```javascript
// 拦截所有 /api/copilotkit 请求
✅ [DEBUG] Network interceptor installed
🌐 [DEBUG] Fetch Request: { url, method, body, hasFiles }
📥 [DEBUG] Fetch Response: { status, dataLength, preview }
```

#### 状态变化监听
```javascript
// 每次 state 变化时触发
🔄 [DEBUG] State changed: {
  uploadedFiles: N,
  fileNames: [...],
  analysisStatus: "...",
  findings: N,
  redacted: N,
  tweets: N,
  hasSummary: true/false
}
```

#### 文件上传处理
```javascript
// 用户上传文件时触发
📤 [DEBUG] Files uploaded: { count, files: [...] }
📤 [DEBUG] Calling setState with new state
```

### 2. 文件上传组件 (`src/components/file-upload.tsx`)

```javascript
// 文件处理流程
📁 [DEBUG] FileUpload: Starting file processing
📄 [DEBUG] FileUpload: Processing file { name, type, size }
🔄 [DEBUG] FileUpload: Reading file as base64...
✅ [DEBUG] FileUpload: Successfully read file { name, originalSize, base64Length }
📊 [DEBUG] FileUpload: Processed files { newFilesCount, currentFilesCount }
📤 [DEBUG] FileUpload: Calling onFilesChange
```

---

## 🔍 如何使用调试日志

### 步骤 1: 打开浏览器开发者工具

在浏览器中访问 `http://47.120.47.251:3002`

**Chrome/Edge**: `F12` 或 `Ctrl+Shift+I` (Windows) / `Cmd+Option+I` (Mac)
**Firefox**: `F12` 或 `Ctrl+Shift+K`

### 步骤 2: 切换到 Console 标签

确保可以看到所有日志输出。

### 步骤 3: 上传 PDF 文件

拖拽或选择一个 PDF 文件。

**预期日志**:
```
📁 [DEBUG] FileUpload: Starting file processing { totalFiles: 1, currentFilesCount: 0 }
📄 [DEBUG] FileUpload: Processing file { name: "test.pdf", type: "application/pdf", size: 12345 }
🔄 [DEBUG] FileUpload: Reading file as base64... test.pdf
✅ [DEBUG] FileUpload: Successfully read file { name: "test.pdf", originalSize: 12345, base64Length: 16432 }
📊 [DEBUG] FileUpload: Processed files { newFilesCount: 1, currentFilesCount: 0, totalBeforeLimit: 1 }
📤 [DEBUG] FileUpload: Calling onFilesChange { combinedCount: 1, files: [...] }
📤 [DEBUG] Files uploaded: { count: 1, files: [...] }
📤 [DEBUG] Calling setState with new state
🔄 [DEBUG] State changed: { uploadedFiles: 1, fileNames: [...], ... }
```

### 步骤 4: 发送消息给 Agent

在聊天框输入 "分析文档" 并发送。

**预期日志**:
```
🌐 [DEBUG] Fetch Request: {
  url: "/api/copilotkit",
  method: "POST",
  body: {
    messages: [...],
    state: {
      uploadedFiles: [
        {
          name: "test.pdf",
          base64: "JVBERi0xLjQK...",
          mimeType: "application/pdf",
          sizeBytes: 12345
        }
      ],
      ...
    }
  },
  hasFiles: true  ← ✅ 关键!应该是 true
}
```

---

## 🚨 问题诊断

### 问题 1: 没有看到任何日志

**原因**: 页面可能没有重新加载

**解决**:
1. 硬刷新页面: `Ctrl+Shift+R` (Windows) 或 `Cmd+Shift+R` (Mac)
2. 检查 Console 是否被清空
3. 检查是否有 JavaScript 错误阻止代码执行

### 问题 2: 看到文件上传日志,但 `hasFiles: false`

**日志示例**:
```
📤 [DEBUG] Files uploaded: { count: 1 }
🔄 [DEBUG] State changed: { uploadedFiles: 1 }
🌐 [DEBUG] Fetch Request: { hasFiles: false }  ← ❌ 问题!
```

**原因**: 状态没有正确同步到 CopilotKit

**解决**:
1. 检查 `state.uploadedFiles` 是否正确更新
2. 检查是否有延迟问题
3. 尝试在发送消息前等待 1-2 秒

### 问题 3: 看到 `hasFiles: true`,但后端收不到文件

**日志示例**:
```
🌐 [DEBUG] Fetch Request: { hasFiles: true }  ← ✅ 前端正确
```
后端日志:
```
INFO - agent.context - 📁 收到 0 个文件  ← ❌ 后端没有收到
```

**原因**: CopilotKit 或 AG-UI 协议传输问题

**解决**:
1. 检查网络请求是否成功 (status 200)
2. 检查响应数据是否正确
3. 查看后端是否有错误日志

---

## 📊 完整的数据流追踪

### 正常流程

```
1. 用户上传 PDF
   📁 [DEBUG] FileUpload: Starting file processing
   ↓
2. 文件读取为 base64
   ✅ [DEBUG] FileUpload: Successfully read file
   ↓
3. 更新前端状态
   📤 [DEBUG] Files uploaded
   🔄 [DEBUG] State changed
   ↓
4. 发送消息给 Agent
   🌐 [DEBUG] Fetch Request { hasFiles: true }
   ↓
5. 后端接收文件
   INFO - agent.context - 📁 收到 1 个文件
   ↓
6. Agent 分析并调用工具
   INFO - agent.model - ✅ 模型响应完成
   ↓
7. 前端面板更新
   🔄 [DEBUG] State changed { findings: 5, ... }
```

---

## 🔧 常见问题排查

### Q1: Console 显示 "Network interceptor installed" 但没有其他日志

**A**: 这说明拦截器已安装,但你还没有触发任何操作。请:
1. 上传一个 PDF 文件
2. 发送消息给 Agent

### Q2: 看到 "Failed to read file" 错误

**A**: 可能的原因:
- 文件损坏
- 文件不是真正的 PDF
- 浏览器安全限制

**解决**:
1. 尝试使用不同的 PDF 文件
2. 检查浏览器 Console 的完整错误信息
3. 尝试在无痕模式下测试

### Q3: 状态更新了,但发送消息时 `hasFiles: false`

**A**: 这可能是 CopilotKit 的状态同步问题。

**检查**:
```javascript
// 在发送消息前,在 Console 中运行:
console.log('Current state:', window.__DEBUG_STATE__);

// 如果未定义,说明状态没有暴露到全局
// 请查看状态变化日志中的 uploadedFiles 数量
```

---

## 📝 提供日志信息时请包含

如果需要帮助诊断问题,请提供:

### 1. 完整的 Console 日志

从页面加载到发送消息的完整日志,包括:
- ✅ [DEBUG] Network interceptor installed
- 📁 FileUpload 日志
- 🔄 State changed 日志
- 🌐 Fetch Request 日志
- 📥 Fetch Response 日志

### 2. 后端日志

特别关注:
```
INFO - agent.model - 📊 当前状态:
INFO - agent.model -   - 文件数: ?
INFO - agent.context - 📁 收到 ? 个文件
```

### 3. 浏览器 Network 标签截图

- `/api/copilotkit` 请求的详细信息
- Request Payload
- Response

---

## ✅ 成功的标志

当一切正常时,你应该看到:

**前端**:
```
✅ [DEBUG] Network interceptor installed
📁 [DEBUG] FileUpload: Starting file processing { totalFiles: 1 }
✅ [DEBUG] FileUpload: Successfully read file { base64Length: 16432 }
📤 [DEBUG] Files uploaded { count: 1 }
🔄 [DEBUG] State changed { uploadedFiles: 1 }
🌐 [DEBUG] Fetch Request { hasFiles: true }  ← ✅ 关键!
📥 [DEBUG] Fetch Response { status: 200 }
```

**后端**:
```
INFO - agent.model - 📊 当前状态:
INFO - agent.model -   - 文件数: 1  ← ✅ 关键!
INFO - agent.context - 📁 收到 1 个文件  ← ✅ 关键!
INFO - agent.context - ✅ 成功提取 test.pdf 文件 (12345 bytes)
INFO - agent.model - ✅ 模型响应完成
```

**前端界面**:
- 4 个面板显示分析结果
- 没有错误提示

---

## 🗑️ 移除调试日志

调试完成后,如果需要移除调试日志:

### 方式 1: 保留代码但禁用

在 `src/app/page.tsx` 顶部添加:
```typescript
const DEBUG_ENABLED = false;
```

然后所有 `console.log` 改为:
```typescript
if (DEBUG_ENABLED) console.log('...');
```

### 方式 2: 完全删除

删除所有标记为 `🐛 DEBUG` 的代码块。

---

**配置完成时间**: 2026-01-10
**状态**: ✅ 调试日志已添加,准备测试
