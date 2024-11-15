"use client";

import React, { useState } from "react";
import axios from "axios";

export default function ResearchAgent({ documentId }: { documentId: string }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState("");

  interface ArxivResponse {
    abstract: string;
  }

  interface WebSearchResponse {
    result: string;
  }

  interface RAGSearchResponse {
    result: string;
  }

  interface ArxivTopicResponse {
    abstracts: { arxiv_id: string; abstract: string }[];
  }

  // Inline type guard for AxiosError
  function isAxiosError(error: any): error is { response: { status: number } } {
    return error?.isAxiosError === true;
  }

  // Function to determine if the query is an ArXiv ID (basic check for typical ArXiv ID format)
  function isArxivId(query: string): boolean {
    return /^[\d.]+$/.test(query);
  }

  async function handleArxivSearch() {
    if (!query) {
      setResults("Please enter a valid ArXiv ID or topic.");
      return;
    }

    try {
      if (isArxivId(query)) {
        // Query is an ArXiv ID; fetch the abstract directly
        const response = await axios.get<ArxivResponse>(
          `http://127.0.0.1:8002/fetch_arxiv/${query}`
        );
        setResults(
          response.data.abstract || "No abstract found for the given ArXiv ID."
        );
      } else {
        // Query is a topic; perform a search to get related ArXiv papers
        const response = await axios.get<ArxivTopicResponse>(
          "http://127.0.0.1:8002/search_arxiv_by_topic/",
          { params: { query } }
        );
        if (response.data.abstracts.length > 0) {
          const formattedResults = response.data.abstracts
            .map(
              (item) => `ArXiv ID: ${item.arxiv_id}\nAbstract: ${item.abstract}`
            )
            .join("\n\n---\n\n");
          setResults(formattedResults);
        } else {
          setResults("No related ArXiv papers found for this topic.");
        }
      }
    } catch (error) {
      console.error("Error fetching ArXiv data:", error);
      if (isAxiosError(error) && error.response) {
        setResults("An error occurred. Please try again.");
      } else {
        setResults("An unknown error occurred.");
      }
    }
  }

  async function handleWebSearch() {
    try {
      const response = await axios.get<WebSearchResponse>(
        "http://127.0.0.1:8002/web_search/",
        { params: { query } }
      );
      setResults(response.data.result);
    } catch (error) {
      console.error("Error performing web search:", error);
      setResults("An error occurred during the web search.");
    }
  }

  async function handleRAGSearch() {
    try {
      const response = await axios.get<RAGSearchResponse>(
        "http://127.0.0.1:8002/rag_search/",
        { params: { query } }
      );
      setResults(response.data.result);
    } catch (error) {
      console.error("Error performing RAG search:", error);
      setResults("An error occurred during the RAG search.");
    }
  }

  return (
    <div className="p-4 bg-white rounded-lg shadow-md">
      <h2 className="text-lg font-semibold text-gray-800 mb-2">
        Research Agent
      </h2>
      <p className="text-gray-600 mb-4">
        Use this agent to search for relevant research papers.
      </p>

      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Enter your search topic or ArXiv ID"
        className="w-full p-2 border border-gray-300 rounded mb-2"
      />

      <div className="space-x-2">
        <button
          onClick={handleArxivSearch}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
        >
          Search Arxiv
        </button>
        <button
          onClick={handleWebSearch}
          className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
        >
          Search Web
        </button>
        <button
          onClick={handleRAGSearch}
          className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600"
        >
          Search RAG
        </button>
      </div>

      <div className="mt-4 p-4 bg-gray-100 rounded-lg shadow-sm">{results}</div>
    </div>
  );
}
