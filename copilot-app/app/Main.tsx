// app/Main.tsx
"use client"; // Required for Next.js App Router

import { CopilotPopup } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

export default function Main() {
  return (
    <div className="app-container">
      <h1>Welcome to the Copilot Assistant</h1>
      <p>This assistant will guide you through your queries.</p>
      <CopilotPopup
        instructions="You are an assistant. Provide answers and insights."
        labels={{
          title: "Copilot Assistant",
          initial: "How can I help you today?",
        }}
      />
    </div>
  );
}
