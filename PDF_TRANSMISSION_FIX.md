# PDF 文件传输问题修复

## 问题描述

PDF 文件无法传输,虽然 AI 对话正常工作。

## 根本原因

**函数调用参数不匹配**:
- `extract_text_from_pdf(pdf_bytes)` - ❌ 缺少 `filename` 参数
- 正确调用: `extract_text_from_pdf(pdf_bytes, filename)` - ✅

**文件**: `agent/main.py:370`

## 修复内容

### 修改前
```python
extracted = extract_text_from_pdf(pdf_bytes)
```

### 修改后
```python
extracted = extract_text_from_pdf(pdf_bytes, file_name)
```

## 完整的数据流

1. ✅ 前端上传 PDF → `state.uploadedFiles` (camelCase)
2. ✅ AG-UI 协议自动转换 → `state.uploaded_files` (snake_case)
3. ✅ 后端读取状态 → `state.get("uploaded_files", [])`
4. ✅ 解码 base64 → `pdf_bytes = base64.b64decode(base64_data)`
5. ✅ **修复**: 提取文本时传递文件名 → `extract_text_from_pdf(pdf_bytes, file_name)`
6. ✅ 格式化为 XML → 添加到 prompt
7. ✅ Agent 分析文档 → 调用工具更新面板

## 验证

重启服务后:
1. 上传 PDF 文件
2. 发送消息给 Agent (如 "请分析这个文档")
3. 检查后端日志: 应该看到 `Processing {filename} ({size} MB)`
4. Agent 应该调用工具更新 4 个面板

## 相关文件

- ✅ `agent/main.py:370` - 修复函数调用
- ✅ `agent/pdf_utils.py:12` - 函数签名正确

---

**状态**: ✅ 已修复
