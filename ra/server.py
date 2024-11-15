from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import FileResponse
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from pinecone import Pinecone, ServerlessSpec
from copilotkit import CopilotKitSDK, Action as CopilotAction
from fastapi.middleware.cors import CORSMiddleware
from agent import fetch_document_titles, rag_search, generate_pdf_report, oracle_sequential_search  # Ensure no circular imports
import logging

app = FastAPI()
logger = logging.getLogger(__name__)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002"],  # Adjust based on frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Pinecone
pc = Pinecone(api_key="pcsk_ikwqH_RmDnBhBR7zuztUqnNpQq1j3ftU9BbBk7wupMKDre1t5UvZ7HVTaQiVr3ksp5rUz")  # Replace with actual API key
index_name = "assignment4-index"
index = pc.Index(index_name)

# Global variable to store the last selected document title
selected_document_title = None

@app.get("/documents/")
async def get_processed_documents():
    """Fetch unique document titles stored in the Pinecone index."""
    try:
        results = index.query(vector=[0] * 1536, top_k=1000, include_metadata=True)
        
        unique_titles = set()
        documents = []

        for match in results["matches"]:
            title = match["metadata"].get("title", "No title")
            if title not in unique_titles:
                unique_titles.add(title)
                documents.append({"id": match["id"], "title": title})

        if not documents:
            logger.warning("No unique documents found in Pinecone index.")
        return {"documents": documents}
    except Exception as e:
        logger.error(f"Error fetching documents: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch documents.")

@app.post("/select_document/")
async def select_document(title: str = Body(..., embed=True)):
    """Selects a document for research purposes."""
    global selected_document_title
    if not title:
        raise HTTPException(status_code=400, detail="Document title is required")
    selected_document_title = title
    return {"selected_document": selected_document_title}

@app.post("/rag_search/")
async def rag_search_endpoint(query: str = Body(..., embed=True), target_index: str = "docs"):
    """Endpoint for RAG search with specified target index."""
    try:
        response = rag_search(query, target_index)
        return {"answer": response}
    except Exception as e:
        logger.error(f"Error during RAG search: {e}")
        raise HTTPException(status_code=500, detail="An error occurred during RAG search.")

@app.post("/generate_report/")
async def generate_report_endpoint(
    introduction: str = Body(...),
    research_steps: str = Body(...),
    main_body: str = Body(...),
    conclusion: str = Body(...),
    sources: str = Body(...),
):
    """Generate a PDF report."""
    global selected_document_title
    if not selected_document_title:
        raise HTTPException(status_code=400, detail="No document selected for report generation.")
    try:
        pdf_path = generate_pdf_report(introduction, research_steps, main_body, conclusion, sources, selected_document_title)
        return FileResponse(pdf_path, media_type="application/pdf", filename=f"{selected_document_title}_report.pdf")
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate the PDF report.")

# Initialize CopilotKit SDK
sdk = CopilotKitSDK(
    actions=[
        CopilotAction(
            name="get_document_titles",
            description="Fetches unique document titles from the Pinecone index.",
            handler=fetch_document_titles,
        ),
        CopilotAction(
            name="rag_search",
            description="Performs RAG search without filtering by specific document.",
            parameters=[{"name": "query", "type": "string", "required": True}],
            handler=rag_search_endpoint,
        ),
        CopilotAction(
            name="generate_report",
            description="Generates and downloads the final report as a PDF.",
            parameters=[
                {"name": "introduction", "type": "string", "required": True},
                {"name": "research_steps", "type": "string", "required": True},
                {"name": "main_body", "type": "string", "required": True},
                {"name": "conclusion", "type": "string", "required": True},
                {"name": "sources", "type": "string", "required": True},
            ],
            handler=generate_report_endpoint,
        ),
    ]
)

# Add CopilotKit endpoint to FastAPI
add_fastapi_endpoint(app, sdk, "/copilotkit_remote")

# This is necessary to run the server if executed as the main module
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
