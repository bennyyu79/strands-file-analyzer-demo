# currentFiles undefined 错误修复

## 问题描述

前端运行时错误:
```
Runtime TypeError: undefined is not an object (evaluating 'currentFiles.length')
```

## 原因

`FileUpload` 组件的 `currentFiles` prop 在某些情况下可能是 `undefined`,导致无法访问 `.length` 属性。

## 解决方案

**修改文件**: `src/components/file-upload.tsx:35`

**修改前**:
```typescript
export function FileUpload({ onFilesChange, currentFiles }: FileUploadProps) {
```

**修改后**:
```typescript
export function FileUpload({ onFilesChange, currentFiles = [] }: FileUploadProps) {
```

添加默认值 `= []`,确保 `currentFiles` 始终是一个数组。

## 为什么会出现 undefined?

`useCoAgent` hook 初始化时,状态可能还未完全初始化,导致 `state.uploadedFiles` 暂时为 `undefined`。

## 验证

刷新页面后,错误应该消失。可以正常:
1. 上传 PDF 文件
2. 查看文件列表
3. 删除文件

---

**状态**: ✅ 已修复
