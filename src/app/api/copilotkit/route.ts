import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { LangGraphHttpAgent } from "@copilotkit/runtime/langgraph";
import { NextRequest } from "next/server";

// Service adapter for multi-agent support
const serviceAdapter = new ExperimentalEmptyAdapter();

// CopilotRuntime with LangGraph agents
const runtime = new CopilotRuntime({
  agents: {
    file_investigator: new LangGraphHttpAgent({
      url: process.env.AGENT_URL || "http://localhost:8000/copilotkit",
    }),
  },
});

// Next.js API route handler
export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};
