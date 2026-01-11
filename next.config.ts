import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Note: pino and thread-stream removed from serverExternalPackages
  // to avoid version conflict warnings with @copilotkit/runtime dependencies

  // 允许跨域请求用于反向代理访问
  // 允许从外网地址 (47.120.47.251:3002) 访问开发服务器
  allowedDevOrigins: [
    "http://47.120.47.251:3002",
    "https://47.120.47.251:3002",
    "http://47.120.47.251",
    "https://47.120.47.251",
  ],
};

export default nextConfig;
