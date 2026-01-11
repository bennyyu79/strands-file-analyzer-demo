# PDF 文件上传跟踪日志配置

## ✅ 已添加详细日志

现在后端会显示完整的 PDF 文件处理流程,包括:

### 📁 文件接收日志
```
INFO - agent.context - 📁 收到 1 个文件
INFO - agent.context - 📄 [1/1] 文件名: example.pdf, Base64 大小: 12345 字节
```

### 📦 文件处理日志
```
INFO - agent.context - 📦 解码后 PDF 大小: 1.23 MB
INFO - agent.context - ✅ 文本提取成功, 预览: 这是一段示例文本...
INFO - agent.context - 📝 提取的文本长度: 1234 字符
```

### 🎨 格式化日志
```
INFO - agent.context - 🎨 已将 1 个文件格式化为 XML
INFO - agent.context - 🎯 最终 prompt 长度: 5678 字符
```

### 🤖 模型调用日志
```
INFO - agent.model - ============================================================
INFO - agent.model - 🤖 开始处理用户消息
INFO - agent.model - 📨 用户消息: 请分析这个文档
INFO - agent.model - 📊 当前状态:
INFO - agent.model -   - 文件数: 1
INFO - agent.model -   - 发现: 0 条
INFO - agent.model -   - 涂黑: 0 条
INFO - agent.model -   - 推文: 0 条
INFO - agent.model -   - 摘要: 无
INFO - agent.model - 🔄 调用模型...
```

### ✅ 响应日志
```
INFO - agent.model - ============================================================
INFO - agent.model - ✅ 模型响应完成
INFO - agent.model - 🔧 模型调用了 4 个工具:
INFO - agent.model -   1. update_findings
INFO - agent.model -   2. update_redacted
INFO - agent.model -   3. update_tweets
INFO - agent.model -   4. update_summary
INFO - agent.model - ============================================================
```

## 🧪 测试方法

1. 访问 http://localhost:3000
2. 上传一个 PDF 文件
3. 发送消息: "请分析这个文档"
4. 查看终端输出,应该看到完整的处理流程

## 📊 日志级别

- `INFO`: 显示所有处理步骤
- `DEBUG`: 显示更详细的信息
- `WARNING`: 文件处理警告
- `ERROR`: 文件处理错误

## 🔧 查看日志

服务运行时,终端会实时显示所有日志,包含表情符号便于识别不同步骤。

---

**状态**: ✅ 详细日志已添加
