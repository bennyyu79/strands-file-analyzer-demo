import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";

import { HttpAgent } from "@ag-ui/client";
import { NextRequest } from "next/server";

// 1. Service adapter for multi-agent support
const serviceAdapter = new ExperimentalEmptyAdapter();

// 🐛 DEBUG: Log agent URL
const agentUrl = process.env.AGENT_URL || "http://47.120.47.251:3003";
console.log('🔧 [DEBUG] CopilotKit Runtime Agent URL:', agentUrl);

// 🔧 FIX: 创建 CopilotRuntime 实例
// 暂时不配置 agents，让基本的 GraphQL 查询（如 availableAgents）能正常工作
const runtime = new CopilotRuntime({
   agents: {
     file_investigator: new HttpAgent({
        url: agentUrl,
      }),
   },
});

// 后续可以动态添加 agents
// runtime.agents = {
//   file_investigator: new HttpAgent({ url: agentUrl }),
// };

// 3. Build a Next.js App Router Endpoint that handles the CopilotKit runtime requests.
export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};
