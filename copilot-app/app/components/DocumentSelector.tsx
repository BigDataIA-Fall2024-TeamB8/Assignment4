import React, { useEffect, useState } from "react";

interface Document {
  id: string;
  title: string;
}

interface DocumentSelectorProps {
  onDocumentSelect: (documentTitle: string) => void;
}

const DocumentSelector: React.FC<DocumentSelectorProps> = ({
  onDocumentSelect,
}) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchDocuments = async () => {
      setLoading(true);
      setError(null); // Clear previous errors
      try {
        const response = await fetch("http://localhost:8005/documents/");
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log("Fetched documents:", data); // Debugging log
        setDocuments(data.documents || []); // Fallback to an empty array
      } catch (err: unknown) {
        console.error("Error fetching documents:", err);
        setError(
          err instanceof Error
            ? err.message
            : "An unknown error occurred while fetching documents."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchDocuments();
  }, []);

  const handleSelection = (event: React.ChangeEvent<HTMLSelectElement>) => {
    onDocumentSelect(event.target.value);
  };

  return (
    <div>
      <label htmlFor="documentSelect">Select Document:</label>
      {loading && <p>Loading documents...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}
      {!loading && !error && (
        <select id="documentSelect" onChange={handleSelection} defaultValue="">
          <option value="" disabled>
            Choose a document
          </option>
          {documents.map((doc) => (
            <option key={doc.id} value={doc.title}>
              {doc.title}
            </option>
          ))}
        </select>
      )}
    </div>
  );
};

export default DocumentSelector;
