// FastAPIAdapter.ts
import { CopilotServiceAdapter } from "@copilotkit/runtime";
import fetch from "node-fetch";

export class FastAPIAdapter implements CopilotServiceAdapter {
  async process(request: any): Promise<any> {
    console.log(
      "Sending request payload to FastAPI:",
      JSON.stringify(request, null, 2)
    ); // Log payload

    const response = await fetch("http://localhost:8002/copilotkit", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request), // Send the request as JSON
    });

    if (!response.ok) {
      throw new Error(`FastAPI request failed with status ${response.status}`);
    }

    const data = await response.json();
    console.log(
      "Received response from FastAPI:",
      JSON.stringify(data, null, 2)
    ); // Log response

    return {
      text: data.response || "No response", // Adjust this based on FastAPI's response structure
      threadId: request.threadId || "default-thread-id",
    };
  }
}
