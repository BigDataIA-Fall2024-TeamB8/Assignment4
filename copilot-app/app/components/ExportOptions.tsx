// components/ExportOptions.tsx
"use client";

import React from "react";
import axios from "axios";

export default function ExportOptions({ sessionId }: { sessionId: string }) {
  // Define the response types
  interface PDFExportResponse {
    pdf_path: string;
  }

  interface CodelabsExportResponse {
    codelabs_url: string;
  }

  async function handlePDFExport() {
    try {
      const response = await axios.get<PDFExportResponse>(
        `http://localhost:8002/export_pdf/?session_id=${sessionId}`
      );
      alert("PDF exported successfully! Path: " + response.data.pdf_path);
    } catch (error) {
      console.error("Error exporting PDF:", error);
    }
  }

  async function handleCodelabsExport() {
    try {
      const response = await axios.get<CodelabsExportResponse>(
        `http://localhost:8002/export_codelabs/?session_id=${sessionId}`
      );
      alert(
        "Codelabs exported successfully! URL: " + response.data.codelabs_url
      );
    } catch (error) {
      console.error("Error exporting Codelabs:", error);
    }
  }

  return (
    <div>
      <button onClick={handlePDFExport}>Export PDF</button>
      <button onClick={handleCodelabsExport}>Export Codelabs</button>
    </div>
  );
}
