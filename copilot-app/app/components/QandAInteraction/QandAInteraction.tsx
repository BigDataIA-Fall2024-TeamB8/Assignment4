// components/QandAInteraction.tsx
"use client";

import React, { useState } from "react";
import axios from "axios";

export default function QandAInteraction({
  documentId,
}: {
  documentId: string;
}) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");

  // Define the response type
  interface AskQuestionResponse {
    result: string;
  }

  async function handleQuestion() {
    try {
      const response = await axios.post<AskQuestionResponse>(
        "http://localhost:8002/ask_question/",
        {
          query: question,
          document_id: documentId,
        }
      );
      setAnswer(response.data.result);
    } catch (error) {
      console.error("Error asking question:", error);
    }
  }

  return (
    <div>
      <input
        type="text"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask a question"
      />
      <button onClick={handleQuestion}>Ask</button>
      <div>{answer}</div>
    </div>
  );
}
