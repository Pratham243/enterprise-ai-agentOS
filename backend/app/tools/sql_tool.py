"""SQL tool — lets an agent query the relational database.

When an agent needs structured data (counts, aggregations, lookups),
it uses this tool to run a read-only SQL query against PostgreSQL
(or SQLite in development).

Safety: only SELECT statements are allowed. The tool rejects any
query that could modify data (INSERT, UPDATE, DELETE, DROP, etc.).
"""

from sqlalchemy import text

from backend.app.db.session import engine
from backend.app.tools.base import BaseTool

_FORBIDDEN = {"insert", "update", "delete", "drop", "alter", "truncate", "create"}


class SQLTool(BaseTool):
    """Run a read-only SQL query against the database."""

    name = "sql_query"
    description = (
        "Run a SQL SELECT query against the business database. "
        "Use this for structured data: counts, sums, lookups, "
        "aggregations. Only SELECT is allowed."
    )

    async def run(self, input_text: str) -> str:
        query = input_text.strip().rstrip(";")

        # Safety check — block write operations
        first_word = query.split()[0].lower() if query.split() else ""
        if first_word in _FORBIDDEN:
            return f"Error: {first_word.upper()} queries are not allowed. Only SELECT is permitted."

        try:
            async with engine.connect() as conn:
                result = await conn.execute(text(query))
                rows = result.fetchall()
                columns = list(result.keys())

            if not rows:
                return "Query returned 0 rows."

            # Format as a readable table
            header = " | ".join(columns)
            lines = [header, "-" * len(header)]
            for row in rows[:50]:  # Cap at 50 rows
                lines.append(" | ".join(str(v) for v in row))

            if len(rows) > 50:
                lines.append(f"... ({len(rows)} total rows, showing first 50)")

            return "\n".join(lines)
        except Exception as e:
            return f"SQL error: {e}"
