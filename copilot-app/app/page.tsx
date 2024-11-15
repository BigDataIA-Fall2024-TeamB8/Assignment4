// page.tsx
"use client";

import DocumentSelector from "./components/DocumentSelector";
import ResearchAgent from "./components/ResearchAgent";
import QandAInteraction from "./components/QandAInteraction";
import ExportOptions from "./components/ExportOptions";
import FinalAnswerForm from "./components/FinalAnswerForm"; // Import the FinalAnswerForm
import { useState } from "react";

export default function MainPage() {
  const [selectedDocument, setSelectedDocument] = useState("");

  return (
    <div>
      <h1>Research Tool Dashboard</h1>
      <DocumentSelector onDocumentSelect={setSelectedDocument} />
      {selectedDocument && (
        <>
          <ResearchAgent documentId={selectedDocument} />
          <QandAInteraction documentId={selectedDocument} />
          <FinalAnswerForm documentId={selectedDocument} />{" "}
          {/* Render the form */}
          <ExportOptions sessionId="session_12345" />
        </>
      )}
    </div>
  );
}
