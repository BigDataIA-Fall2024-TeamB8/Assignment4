import { CopilotKit } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui"; // Add this import
import "./globals.css";
import "@copilotkit/react-ui/styles.css";
import { ReactNode } from "react";

interface RootLayoutProps {
  children: ReactNode;
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en">
      <body className="bg-gray-50">
        <CopilotKit runtimeUrl="/api/copilotkit">
          <div className="flex h-screen">
            {/* Sidebar */}
            <div className="w-1/4 p-6 bg-white shadow-lg border-r border-gray-300 flex flex-col">
              <header className="mb-6">
                <h1 className="text-2xl font-semibold text-blue-800">
                  Research Helper
                </h1>
                <p className="text-sm text-gray-500 mt-1">
                  Your tool for efficient research exploration.
                </p>
              </header>
              <div className="overflow-y-auto flex-grow">{children}</div>
            </div>

            {/* Main Content Panel */}
            <div className="w-3/4 p-6 bg-gray-100 flex flex-col">
              <div className="flex-grow">
                <h2 className="text-lg font-semibold mb-4">Assistant</h2>
                <div className="w-full h-full shadow-lg rounded-lg overflow-hidden">
                  <CopilotChat
                    instructions="You are assisting the user with web searches and document Q&A."
                    labels={{
                      title: "Copilot Assistant",
                      initial: "Hi! 👋 How can I assist you today?",
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
        </CopilotKit>
      </body>
    </html>
  );
}
