"""Background task endpoints — submit, poll, and list async jobs.

POST /tasks/submit   — fire-and-forget an agent or workflow job
GET  /tasks/{id}     — poll a task's status and result
GET  /tasks/         — list recent tasks (paginated)
GET  /tasks/stats    — summary of task states
"""

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends

from backend.app.api.pagination import PaginatedResponse, PaginationParams
from backend.app.api.throttle import throttle
from backend.app.exceptions import NotFoundError, ValidationError
from backend.app.services.task_manager import task_manager

router = APIRouter(prefix="/tasks", tags=["Background Tasks"])


class TaskSubmitRequest(BaseModel):
    job_type: str = Field(
        ...,
        pattern="^(agent_query|workflow_run)$",
        description="Job type: agent_query or workflow_run",
    )
    question: str = Field(..., min_length=1, max_length=5000, description="Input question")


class TaskSubmitResponse(BaseModel):
    task_id: str
    job_type: str
    status: str


class TaskStatusResponse(BaseModel):
    task_id: str
    job_type: str
    status: str
    result: dict | None = None
    error: str | None = None
    created_at: str
    completed_at: str | None = None


async def _run_agent_query(question: str) -> dict:
    from backend.app.agents.router import route_query
    result = await route_query(question)
    return {
        "question": question,
        "answer": result.answer,
        "tool_used": result.tool_used,
        "steps": result.steps,
    }


async def _run_workflow(question: str) -> dict:
    from backend.app.workflows.graph import build_default_workflow
    graph = build_default_workflow()
    result = await graph.run({"question": question})
    return {
        "question": question,
        "category": result.get("category", "unknown"),
        "answer": result.get("answer", "No answer produced."),
        "steps": result.get("steps", []),
    }


_JOB_RUNNERS = {
    "agent_query": _run_agent_query,
    "workflow_run": _run_workflow,
}


@router.post("/submit", response_model=TaskSubmitResponse)
async def submit_task(request: TaskSubmitRequest) -> TaskSubmitResponse:
    """Submit a background job and get a task ID for polling."""
    runner = _JOB_RUNNERS.get(request.job_type)
    if not runner:
        raise ValidationError(f"Unknown job type: {request.job_type}")

    task_id = task_manager.submit(request.job_type, runner, request.question)
    record = task_manager.get(task_id)
    return TaskSubmitResponse(
        task_id=task_id,
        job_type=request.job_type,
        status=record.status.value,
    )


@router.get("/stats")
async def task_stats(_throttle=throttle("relaxed")) -> dict:
    """Summary of task states."""
    return task_manager.stats()


@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task(task_id: str, _throttle=throttle("relaxed")) -> TaskStatusResponse:
    """Poll a task's current status and result."""
    record = task_manager.get(task_id)
    if not record:
        raise NotFoundError("Task", task_id)
    return TaskStatusResponse(**record.to_dict())


@router.get("/", response_model=PaginatedResponse)
async def list_tasks(params: PaginationParams = Depends()) -> PaginatedResponse:
    """List recent tasks with pagination."""
    tasks, total = task_manager.list_tasks(offset=params.offset, limit=params.page_size)
    items = [t.to_dict() for t in tasks]
    return PaginatedResponse.create(items, total, params.page, params.page_size)
