# 外网反向代理验证

## 🔍 验证步骤

正在测试后端外网反向代理...

### 测试地址
- 前端代理: http://47.120.47.251:3002 ✅ (已知工作)
- 后端代理: http://47.120.47.251:3003 ❓ (待验证)

### 期望的配置

反向代理规则应该是:
```
47.120.47.251:3003 → 192.168.214.102:8000
```

### 需要 support WebSocket/SSE

AG-UI 协议使用 **Server-Sent Events (SSE)**,反向代理必须支持:
- ✅ HTTP POST 请求
- ✅ 保持连接 (流式响应)
- ✅ 不缓冲响应

### Nginx 配置示例

如果使用 Nginx,配置应该类似:
```nginx
location / {
    proxy_pass http://192.168.214.102:8000;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_set_header Host $host;

    # SSE 支持
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 86400s;
}
```

---

**等待测试结果...**
