"""Workflow graph — the LangGraph-style orchestration engine.

This implements a directed graph where:
- Nodes are async functions that transform WorkflowState
- Edges connect nodes, with optional conditions for branching
- The engine runs nodes in order, following edges until it reaches END

We implement this without requiring the langgraph package so the
project runs standalone. When langgraph is added later, the nodes
and state are already compatible — only the runner changes.
"""

from backend.app.workflows.nodes import (
    classify_node,
    query_database_node,
    retrieve_documents_node,
    synthesize_node,
)
from backend.app.workflows.state import WorkflowState

# Special sentinel for the terminal node
END = "__end__"


class WorkflowGraph:
    """A simple graph executor inspired by LangGraph's API.

    Usage:
        graph = WorkflowGraph()
        graph.add_node("classify", classify_node)
        graph.add_edge("classify", "retrieve")
        graph.set_entry("classify")
        result = await graph.run({"question": "..."})
    """

    def __init__(self) -> None:
        self._nodes: dict[str, callable] = {}
        self._edges: dict[str, str | callable] = {}
        self._entry: str | None = None

    def add_node(self, name: str, func: callable) -> None:
        self._nodes[name] = func

    def add_edge(self, from_node: str, to_node: str) -> None:
        """Add a fixed edge from one node to another."""
        self._edges[from_node] = to_node

    def add_conditional_edge(
        self, from_node: str, condition: callable, mapping: dict[str, str]
    ) -> None:
        """Add a conditional edge that branches based on state.

        condition(state) returns a key, mapping[key] gives the next node.
        """
        self._edges[from_node] = (condition, mapping)

    def set_entry(self, name: str) -> None:
        self._entry = name

    async def run(
        self, initial_state: dict, on_step=None,
    ) -> WorkflowState:
        """Execute the graph from the entry node to END.

        Args:
            initial_state: initial workflow state dict.
            on_step: optional async callback called after each node
                     with (node_name, node_output, full_state).
        """
        state: WorkflowState = {**initial_state, "steps": []}
        current = self._entry

        while current and current != END:
            node_fn = self._nodes.get(current)
            if not node_fn:
                state["error"] = f"Unknown node: {current}"
                break

            # Run the node and merge its output into state
            updates = await node_fn(state)
            state = {**state, **updates}

            if on_step:
                await on_step(current, updates, state)

            # Resolve the next node
            edge = self._edges.get(current, END)
            if isinstance(edge, tuple):
                condition, mapping = edge
                key = condition(state)
                current = mapping.get(key, END)
            else:
                current = edge

        return state


def build_default_workflow() -> WorkflowGraph:
    """Build the standard question-answering workflow.

    Flow:
        classify ──┬── (rag) ──▶ retrieve_documents ──▶ synthesize ──▶ END
                   └── (sql) ──▶ query_database ──────▶ synthesize ──▶ END
    """
    graph = WorkflowGraph()

    graph.add_node("classify", classify_node)
    graph.add_node("retrieve_documents", retrieve_documents_node)
    graph.add_node("query_database", query_database_node)
    graph.add_node("synthesize", synthesize_node)

    # After classification, branch based on category
    graph.add_conditional_edge(
        "classify",
        condition=lambda state: state.get("category", "rag"),
        mapping={
            "rag": "retrieve_documents",
            "sql": "query_database",
        },
    )

    # Both paths converge at synthesize
    graph.add_edge("retrieve_documents", "synthesize")
    graph.add_edge("query_database", "synthesize")
    graph.add_edge("synthesize", END)

    graph.set_entry("classify")
    return graph
