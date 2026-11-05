"""Workflow nodes — individual processing steps in the graph.

Each function is a node that takes the current WorkflowState,
does one piece of work, and returns updated state fields.

When an LLM is available, nodes use it for classification, SQL
generation, and answer synthesis. Without an LLM, they fall back
to rule-based logic so the pipeline always works.
"""

from backend.app.agents.router import _classify
from backend.app.services.llm_client import llm
from backend.app.services.rag import retrieve
from backend.app.tools.sql_tool import SQLTool
from backend.app.workflows.state import WorkflowState


async def classify_node(state: WorkflowState) -> dict:
    """Classify the question as 'rag' or 'sql' using the LLM."""
    question = state["question"]

    result = await llm.chat_json(
        message=f"Classify this question:\n\n{question}",
        system=(
            "You are a question classifier. Decide whether the question "
            "should be answered using SQL (database queries, counts, totals, "
            "aggregations) or RAG (document search, explanations, policies).\n"
            "Respond with: {\"category\": \"sql\"} or {\"category\": \"rag\"}"
        ),
    )

    category = result.get("category", "rag")
    if category not in ("rag", "sql"):
        category = _classify(question)

    return {
        "category": category,
        "steps": state.get("steps", []) + [
            {"node": "classify", "result": category},
        ],
    }


async def retrieve_documents_node(state: WorkflowState) -> dict:
    """Retrieve relevant document chunks from the vector store."""
    results = retrieve(state["question"], top_k=3)
    context = "\n---\n".join(r.text for r in results) if results else "No documents found."
    return {
        "context": context,
        "steps": state.get("steps", []) + [
            {"node": "retrieve_documents", "chunks_found": len(results)},
        ],
    }


async def query_database_node(state: WorkflowState) -> dict:
    """Generate and run a SQL query using the LLM."""
    question = state["question"]
    sql_tool = SQLTool()

    response = await llm.chat(
        message=f"Generate a SQL query to answer: {question}",
        system=(
            "You are a SQL expert. Generate a single SELECT query for SQLite. "
            "The database has a table 'audit_logs' with columns: "
            "id, action, actor, detail, created_at. "
            "Return ONLY the SQL query, no explanation."
        ),
    )

    sql_query = response.content.strip()
    if sql_query.startswith("```"):
        sql_query = sql_query.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    try:
        result = await sql_tool.run(sql_query)
        context = f"SQL: {sql_query}\nResult: {result}"
        status = "executed"
    except Exception as e:
        context = f"SQL: {sql_query}\nError: {e}"
        status = "error"

    return {
        "context": context,
        "steps": state.get("steps", []) + [
            {"node": "query_database", "status": status, "sql": sql_query},
        ],
    }


async def synthesize_node(state: WorkflowState) -> dict:
    """Synthesize a final answer from retrieved context using the LLM."""
    question = state["question"]
    context = state.get("context", "No context available.")

    response = await llm.chat(
        message=(
            f"Question: {question}\n\n"
            f"Context:\n{context}\n\n"
            "Please provide a clear, helpful answer based on the context above."
        ),
        system=(
            "You are a helpful enterprise assistant. Answer the question "
            "using only the provided context. If the context is insufficient, "
            "say so honestly."
        ),
    )

    return {
        "answer": response.content,
        "steps": state.get("steps", []) + [
            {"node": "synthesize", "context_length": len(context)},
        ],
    }
