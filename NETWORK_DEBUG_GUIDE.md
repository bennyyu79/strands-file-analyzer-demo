# 网络请求调试指南

## 🔍 查看 Network 请求

### 步骤:

1. **打开开发者工具**
   - 按 F12
   - 或右键点击页面 → "检查"

2. **切换到 Network 标签**
   - 点击顶部的 "Network"

3. **清空之前的请求**
   - 点击 🚫 (禁止) 图标清空列表

4. **上传 PDF 文件**
   - 在页面上选择一个 PDF 文件上传

5. **发送消息**
   - 在聊天框输入: "请分析这个文档"
   - 点击发送

6. **查看请求**
   - 在 Network 列表中找到 `api/copilotkit` 请求
   - 点击这个请求
   - 右侧会显示详情
   - 点击 **"Payload"** 标签

7. **复制信息**
   - 查看 Payload 中的 JSON 数据
   - 告诉我:
     - 是否包含 `state` 字段?
     - `state` 里面是否有 `uploadedFiles` 或 `uploaded_files`?
     - 如果有,它的值是什么?

---

## 📸 预期看到的内容

正常情况下, Payload 应该类似:
```json
{
  "action": "initialize",
  "state": {
    "uploadedFiles": [...],  // ← 这里应该有文件数据
    "findings": [],
    "redacted": [],
    "tweets": [],
    "summary": null
  },
  "messages": [...]
}
```

---

**请告诉我 Payload 中看到了什么!**
