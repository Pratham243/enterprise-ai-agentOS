"""RAG tool — lets an agent search the document knowledge base.

When an agent decides it needs information from ingested documents,
it calls this tool with a question. The tool runs the RAG retrieval
pipeline and returns the most relevant text chunks.
"""

from backend.app.services.rag import retrieve
from backend.app.tools.base import BaseTool


class RAGTool(BaseTool):
    """Search ingested documents for relevant information."""

    name = "document_search"
    description = (
        "Search the document knowledge base. Use this when the question "
        "is about company documents, policies, reports, or uploaded files."
    )

    async def run(self, input_text: str) -> str:
        results = retrieve(input_text, top_k=3)
        if not results:
            return "No relevant documents found."
        chunks = [f"[Score: {r.score:.2f}] {r.text}" for r in results]
        return "\n---\n".join(chunks)
