from typing import List, TypedDict, Annotated
import re
import requests
from fpdf import FPDF
from langchain_core.agents import AgentAction
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from serpapi import GoogleSearch
from langgraph.graph import StateGraph, END
from pinecone import Pinecone, ServerlessSpec
import operator

# Initialize Pinecone
pc = Pinecone(api_key="")
doc_index_name = "assignment4-index"
arxiv_index_name = "arxiv-index"

# Ensure indexes exist
for index_name in [doc_index_name, arxiv_index_name]:
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=1536,
            metric='cosine',
            spec=ServerlessSpec(cloud='aws', region='us-east-1')
        )

doc_index = pc.Index(doc_index_name)
arxiv_index = pc.Index(arxiv_index_name)

# Define the state format for the agent
class AgentState(TypedDict):
    input: str
    chat_history: List[BaseMessage]
    intermediate_steps: Annotated[List[AgentAction], operator.add]

class AgentAction(TypedDict):
    tool: str
    tool_input: str
    output: str

# Define the LLM and prompt template
system_prompt = """You are the oracle, the great AI decision maker.
Given the user's query, decide which tool to use and handle it appropriately.

1. Start with a web search to gather research paper information.
2. Fetch ArXiv details based on research paper IDs found.
3. Conduct a RAG search if further information is needed.
4. Provide all results in a comprehensive format for chat. If accepted, autofill the report sections.
"""
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}")
])

llm = ChatOpenAI(
    model="gpt-4o",
    openai_api_key="",
    temperature=0
)

# Embedding model
embedding_model = OpenAIEmbeddings(api_key="")

# Tools

def fetch_document_titles():
    """Retrieve unique document titles from the document index in Pinecone."""
    try:
        results = doc_index.query(vector=[0] * 1536, top_k=100, include_metadata=True)
        unique_titles = list(set(item["metadata"].get("title", "No title") for item in results["matches"]))
        return unique_titles
    except Exception as e:
        print(f"Error fetching document titles: {e}")
        return []

def fetch_arxiv(state: AgentState) -> AgentState:
    """Fetch ArXiv abstract by paper ID and update intermediate steps."""
    arxiv_id = state["input"]
    try:
        res = requests.get(f"https://export.arxiv.org/abs/{arxiv_id}")
        abstract_pattern = re.compile(
            r'<blockquote class="abstract mathjax">\s*<span class="descriptor">Abstract:</span>\s*(.*?)\s*</blockquote>',
            re.DOTALL
        )
        match = abstract_pattern.search(res.text)
        abstract = match.group(1) if match else "Abstract not found."
    except Exception as e:
        abstract = f"Error fetching ArXiv abstract: {e}"

    action_output = {"tool": "fetch_arxiv", "tool_input": arxiv_id, "output": abstract}
    state["intermediate_steps"].append(action_output)
    return state

def web_search(query: str) -> str:
    """Perform web search using SerpAPI."""
    search = GoogleSearch({
        "engine": "google",
        "api_key": "",
        "q": query,
        "num": 5
    })
    results = search.get_dict()["organic_results"]
    return "\n---\n".join([f"{x['title']}\n{x['snippet']}\n{x['link']}" for x in results])

def rag_search(query: str, target_index: str = "docs") -> str:
    """Perform RAG search and return detailed results based on similar vectors."""
    try:
        query_embedding = embedding_model.embed_query(query)
        index = doc_index if target_index == "docs" else arxiv_index
        
        # Retrieve 100 similar vectors
        search_results = index.query(
            vector=query_embedding,
            top_k=100,
            include_metadata=True
        )

        # Process and format the results
        relevant_texts = []
        for match in search_results["matches"]:
            title = match["metadata"].get("title", "Unknown Document")
            content = match["metadata"].get("content", "No content available")
            relevant_texts.append(f"**Document Title**: {title}\n**Content**: {content}")

        combined_text = "\n\n---\n\n".join(relevant_texts).strip()
        return combined_text

    except Exception as e:
        print(f"Error during RAG search: {e}")
        return f"An error occurred during RAG search: {e}"

def generate_pdf_report(introduction, analysis, sources, document_title):
    """Generate a structured PDF report."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, "Research Report", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    sections = {"Introduction": introduction, "Analysis": analysis, "Sources": sources}
    for section, content in sections.items():
        pdf.cell(200, 10, section, ln=True)
        pdf.multi_cell(200, 10, content)
        pdf.ln(10)
    pdf_output = f"report_{document_title}.pdf"
    pdf.output(pdf_output)
    return pdf_output

def oracle_sequential_search(state: AgentState) -> AgentState:
    """Perform Oracle search using all tools sequentially for detailed responses."""
    query = state["input"]
    
    # Step 1: Web Search
    web_response = web_search(query)
    state["intermediate_steps"].append({
        "tool": "web_search",
        "tool_input": query,
        "output": web_response
    })
    
    # Step 2: Fetch ArXiv details (replace with actual ArXiv ID from web results if available)
    arxiv_id = "2401.04088"  # Placeholder for actual ArXiv ID
    # Passing full AgentState to fetch_arxiv with required keys
    arxiv_state = {
        "input": arxiv_id,
        "chat_history": state["chat_history"],
        "intermediate_steps": state["intermediate_steps"]
    }
    arxiv_response = fetch_arxiv(arxiv_state)
    state["intermediate_steps"].append({
        "tool": "fetch_arxiv",
        "tool_input": arxiv_id,
        "output": arxiv_response
    })
    
    # Step 3: RAG Search
    rag_response = rag_search(query)
    state["intermediate_steps"].append({
        "tool": "rag_search",
        "tool_input": query,
        "output": rag_response
    })

    # Compile all responses into a detailed analysis
    state["introduction"] = f"Oracle results for query: {query}"
    state["analysis"] = f"Web Search Results:\n{web_response}\n\nArXiv Results:\n{arxiv_response}\n\nRAG Results:\n{rag_response}"
    state["source"] = "Combined results from Web, ArXiv, and RAG searches"
    
    return state

# Construct LangGraph
graph = StateGraph(AgentState)
graph.add_node("oracle", lambda state: oracle_sequential_search(state))
graph.set_entry_point("oracle")
graph.add_edge("oracle", END)

runnable = graph.compile()

# Example Invocation
inputs = {
    "input": "2401.04088",
    "chat_history": [],
    "intermediate_steps": [],
    "target_index": "arxiv"
}
result = runnable.invoke(inputs)
print(result)
