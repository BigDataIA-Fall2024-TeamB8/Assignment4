import {
  CopilotRuntime,
  OpenAIAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import OpenAI from "openai";
import { NextRequest } from "next/server";

// Initialize OpenAI Adapter
// Replace 'your_openai_api_key_here' with the actual OpenAI API key
const openai = new OpenAI({
  apiKey: "",
});
const serviceAdapter = new OpenAIAdapter({ openai });

// Initialize Copilot Runtime
const runtime = new CopilotRuntime({
  remoteActions: [
    {
      url: "http://localhost:8005/copilotkit_remote", // URL of the FastAPI backend
    },
  ],
});

// Export the POST request handler for Next.js App Router
export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit", // Next.js API route for CopilotKit
  });

  return handleRequest(req);
};
