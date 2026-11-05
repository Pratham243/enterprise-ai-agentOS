"""Async task manager — in-memory job tracking (Celery-ready interface).

Submits background work via asyncio.create_task, tracks state
(pending → running → completed | failed), and stores results so
clients can poll. Swap the in-memory store for Redis/Celery in
production without changing the API layer.
"""

import asyncio
import datetime
import uuid
from collections import OrderedDict
from enum import Enum
from threading import Lock
from typing import Any, Callable, Coroutine


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskRecord:
    __slots__ = ("id", "job_type", "status", "result", "error", "created_at", "completed_at")

    def __init__(self, task_id: str, job_type: str):
        self.id = task_id
        self.job_type = job_type
        self.status = TaskStatus.PENDING
        self.result: Any = None
        self.error: str | None = None
        self.created_at = datetime.datetime.now(datetime.timezone.utc)
        self.completed_at: datetime.datetime | None = None

    def to_dict(self) -> dict:
        return {
            "task_id": self.id,
            "job_type": self.job_type,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class TaskManager:
    """In-memory async task manager with bounded history."""

    def __init__(self, max_tasks: int = 1000):
        self._tasks: OrderedDict[str, TaskRecord] = OrderedDict()
        self._max_tasks = max_tasks
        self._lock = Lock()

    def submit(
        self,
        job_type: str,
        coro_fn: Callable[..., Coroutine],
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """Submit a background job. Returns the task ID immediately."""
        task_id = uuid.uuid4().hex[:12]
        record = TaskRecord(task_id, job_type)

        with self._lock:
            self._tasks[task_id] = record
            while len(self._tasks) > self._max_tasks:
                self._tasks.popitem(last=False)

        asyncio.create_task(self._run(record, coro_fn, *args, **kwargs))
        return task_id

    async def _run(
        self,
        record: TaskRecord,
        coro_fn: Callable[..., Coroutine],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        record.status = TaskStatus.RUNNING
        try:
            record.result = await coro_fn(*args, **kwargs)
            record.status = TaskStatus.COMPLETED
        except Exception as exc:
            record.error = str(exc)
            record.status = TaskStatus.FAILED
        finally:
            record.completed_at = datetime.datetime.now(datetime.timezone.utc)

    def get(self, task_id: str) -> TaskRecord | None:
        return self._tasks.get(task_id)

    def list_tasks(self, offset: int = 0, limit: int = 20) -> tuple[list[TaskRecord], int]:
        with self._lock:
            all_tasks = list(reversed(self._tasks.values()))
            total = len(all_tasks)
            return all_tasks[offset:offset + limit], total

    def stats(self) -> dict:
        with self._lock:
            statuses = [t.status.value for t in self._tasks.values()]
        return {
            "total": len(statuses),
            "pending": statuses.count("pending"),
            "running": statuses.count("running"),
            "completed": statuses.count("completed"),
            "failed": statuses.count("failed"),
        }


task_manager = TaskManager()
