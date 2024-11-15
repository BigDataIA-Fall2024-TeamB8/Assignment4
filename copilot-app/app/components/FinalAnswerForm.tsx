// components/FinalAnswerForm.tsx
import { useState } from "react";

export default function FinalAnswerForm({
  documentId,
}: {
  documentId: string;
}) {
  const [introduction, setIntroduction] = useState("");
  const [researchSteps, setResearchSteps] = useState("");
  const [mainBody, setMainBody] = useState("");
  const [conclusion, setConclusion] = useState("");
  const [sources, setSources] = useState("");

  const handleGenerateReport = () => {
    // Add logic here to handle the report generation (e.g., POST request to backend)
    console.log({
      introduction,
      researchSteps,
      mainBody,
      conclusion,
      sources,
    });
  };

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Generate Final Report</h2>

      <div>
        <label className="block text-sm font-medium">Introduction</label>
        <textarea
          value={introduction}
          onChange={(e) => setIntroduction(e.target.value)}
          className="w-full p-2 border border-gray-300 rounded-md"
          placeholder="Write the introduction here..."
        />
      </div>

      <div>
        <label className="block text-sm font-medium">Research Steps</label>
        <textarea
          value={researchSteps}
          onChange={(e) => setResearchSteps(e.target.value)}
          className="w-full p-2 border border-gray-300 rounded-md"
          placeholder="List the research steps here..."
        />
      </div>

      <div>
        <label className="block text-sm font-medium">Main Body</label>
        <textarea
          value={mainBody}
          onChange={(e) => setMainBody(e.target.value)}
          className="w-full p-2 border border-gray-300 rounded-md"
          placeholder="Write the main body of the report here..."
        />
      </div>

      <div>
        <label className="block text-sm font-medium">Conclusion</label>
        <textarea
          value={conclusion}
          onChange={(e) => setConclusion(e.target.value)}
          className="w-full p-2 border border-gray-300 rounded-md"
          placeholder="Write the conclusion here..."
        />
      </div>

      <div>
        <label className="block text-sm font-medium">Sources</label>
        <textarea
          value={sources}
          onChange={(e) => setSources(e.target.value)}
          className="w-full p-2 border border-gray-300 rounded-md"
          placeholder="List the sources here..."
        />
      </div>

      <button
        onClick={handleGenerateReport}
        className="px-4 py-2 bg-blue-600 text-white rounded-md mt-4"
      >
        Generate Report
      </button>
    </div>
  );
}
