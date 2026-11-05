"""RAG API endpoints — document ingestion and retrieval.

These endpoints expose the RAG pipeline over HTTP:
- POST /rag/ingest  — upload a document to be chunked and stored
- POST /rag/query   — ask a question and get relevant document chunks
"""

from pydantic import BaseModel, Field
from fastapi import APIRouter

from backend.app.services.rag import ingest_document, retrieve
from backend.app.services.cache import app_cache

router = APIRouter(prefix="/rag", tags=["RAG"])


# --- Request / Response schemas -----------------------------------------------

class IngestRequest(BaseModel):
    """Request body for document ingestion."""

    text: str = Field(..., min_length=1, max_length=100000, description="Document text to ingest")
    source: str = Field(default="upload", max_length=200, description="Document source identifier")


class IngestResponse(BaseModel):
    """Response after ingesting a document."""

    chunks_stored: int
    source: str


class QueryRequest(BaseModel):
    """Request body for a RAG query."""

    question: str = Field(..., min_length=1, max_length=5000, description="Question to answer")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results")


class ChunkResult(BaseModel):
    """A single retrieved chunk."""

    id: str
    score: float
    text: str
    metadata: dict


class QueryResponse(BaseModel):
    """Response containing retrieved document chunks."""

    question: str
    results: list[ChunkResult]


# --- Endpoints ----------------------------------------------------------------

@router.post("/ingest", response_model=IngestResponse)
async def ingest(request: IngestRequest) -> IngestResponse:
    """Ingest a document: chunk it, embed it, store in the vector database."""
    count = ingest_document(request.text, source=request.source)
    return IngestResponse(chunks_stored=count, source=request.source)


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    """Query the knowledge base for relevant document chunks."""
    cached = app_cache.get("rag_query", request.question, request.top_k)
    if cached:
        return QueryResponse(**cached)

    results = retrieve(request.question, top_k=request.top_k)
    response = QueryResponse(
        question=request.question,
        results=[
            ChunkResult(
                id=r.id,
                score=r.score,
                text=r.text,
                metadata=r.metadata,
            )
            for r in results
        ],
    )
    app_cache.set("rag_query", request.question, request.top_k, value=response.model_dump())
    return response
