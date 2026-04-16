# Main FastAPI Application

import logging
import os

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.config import config
from src.rag_pipeline import RAGPipeline

logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AIRag",
    description="AI-powered financial document analysis with RAG",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure upload directory exists
os.makedirs(config.UPLOAD_DIR, exist_ok=True)

# Initialise RAG pipeline (shared across requests)
rag = RAGPipeline()

# Serve the frontend as static files
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# ------------------------------------------------------------------
# Request / Response models
# ------------------------------------------------------------------

class QueryRequest(BaseModel):
    question: str
    top_k: int = 5


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]


class IngestTextRequest(BaseModel):
    text: str
    metadata: dict | None = None


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

@app.get("/")
async def root():
    """Serve the frontend index page."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Welcome to AIRag – AI-powered financial analysis"}


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    warnings = config.validate()
    return {
        "status": "ok",
        "vector_store_size": rag.vector_store.size,
        "warnings": warnings,
    }


@app.post("/api/upload", response_model=dict)
async def upload_file(file: UploadFile = File(...)):
    """Upload a document (CSV or plain text) for ingestion."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Check file size
    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > config.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f} MB). Max allowed: {config.MAX_UPLOAD_SIZE_MB} MB",
        )

    # Save to disk
    safe_filename = os.path.basename(file.filename)
    filepath = os.path.join(config.UPLOAD_DIR, safe_filename)
    with open(filepath, "wb") as fh:
        fh.write(contents)

    # Ingest based on file type
    try:
        if safe_filename.lower().endswith(".csv"):
            result = rag.ingest_csv(filepath)
            return {
                "message": f"CSV file '{safe_filename}' ingested successfully",
                "chunks": result["chunks"],
                "analysis": result["analysis"],
            }
        else:
            # Treat as plain text
            text = contents.decode("utf-8", errors="replace")
            chunks = rag.ingest_text(text, metadata={"source": safe_filename})
            return {
                "message": f"File '{safe_filename}' ingested successfully",
                "chunks": chunks,
            }
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/ingest-text", response_model=dict)
async def ingest_text(request: IngestTextRequest):
    """Ingest raw text directly."""
    try:
        chunks = rag.ingest_text(request.text, metadata=request.metadata)
        return {"message": "Text ingested successfully", "chunks": chunks}
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Query the RAG pipeline."""
    try:
        result = rag.query(request.question, top_k=request.top_k)
        return QueryResponse(**result)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.delete("/api/documents")
async def clear_documents():
    """Clear all ingested documents from the vector store."""
    rag.vector_store.clear()
    return {"message": "All documents cleared"}
