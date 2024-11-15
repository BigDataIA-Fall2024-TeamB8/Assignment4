"use client";

import { useState } from "react";
import { useCopilotChat } from "@copilotkit/react-core";
import { Role, TextMessage } from "@copilotkit/runtime-client-gql";
import axios from "axios";

// Define the structure for the chatbot's response
interface ChatbotResponse {
  result: string;
}

export default function CustomChatInterface() {
  const { visibleMessages, appendMessage } = useCopilotChat();
  const [input, setInput] = useState("");

  // Function to handle sending messages
  const sendMessage = async (content: string) => {
    // Add the user's message to the chat history
    appendMessage(new TextMessage({ content, role: Role.User }));

    try {
      // Send the user's message to the backend API
      const response = await axios.post<ChatbotResponse>(
        "http://127.0.0.1:8002/chatbot",
        {
          message: content,
        }
      );

      // Add the assistant's response to the chat history
      appendMessage(
        new TextMessage({ content: response.data.result, role: Role.Assistant })
      );
    } catch (error) {
      console.error("Error fetching response from chatbot:", error);

      // Add an error message to the chat if there's an issue
      appendMessage(
        new TextMessage({
          content: "An error occurred. Please try again later.",
          role: Role.Assistant,
        })
      );
    }
  };

  return (
    <div className="p-6 bg-gray-50 rounded-lg shadow-md">
      <div className="chat-history flex flex-col space-y-2 overflow-y-auto h-64 p-4 bg-white rounded">
        {visibleMessages.map((msg, idx) => (
          <div
            key={idx}
            className={`p-2 rounded ${
              (msg as TextMessage).role === Role.User
                ? "bg-blue-500 text-white self-end"
                : "bg-gray-200 text-black self-start"
            }`}
          >
            {(msg as TextMessage).content || ""}
          </div>
        ))}
      </div>

      <div className="mt-4 flex">
        <input
          type="text"
          className="flex-grow p-2 border border-gray-300 rounded-l"
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              sendMessage(input);
              setInput(""); // Clear input field
            }
          }}
        />
        <button
          className="bg-blue-500 text-white p-2 rounded-r"
          onClick={() => {
            if (input.trim()) {
              sendMessage(input);
              setInput(""); // Clear input field
            }
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
}
