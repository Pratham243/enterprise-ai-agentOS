"""Workflow state — the data object that flows through every graph node.

In LangGraph, state is a TypedDict that every node reads from and writes to.
We define it here so it's shared across all workflow definitions.

Each field represents a piece of information that accumulates as the
workflow progresses: the original question, what category it is,
retrieved context, the final answer, and a log of steps taken.
"""

from typing import TypedDict


class WorkflowState(TypedDict, total=False):
    """State that flows through a LangGraph workflow."""

    question: str
    category: str          # "rag" or "sql"
    context: str           # Retrieved document chunks or query results
    answer: str            # The final synthesized answer
    steps: list[dict]      # Trace of what happened at each node
    error: str | None      # Set if something goes wrong
