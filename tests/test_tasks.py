"""Tests for the background task manager and task endpoints."""

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app
from backend.app.services.task_manager import TaskManager, TaskRecord, TaskStatus


# ---------------------------------------------------------------------------
# Unit tests — TaskManager in isolation
# ---------------------------------------------------------------------------

class TestTaskManager:
    def setup_method(self):
        self.mgr = TaskManager(max_tasks=5)

    @pytest.mark.asyncio
    async def test_submit_and_get(self):
        async def dummy(x):
            return {"echo": x}

        task_id = self.mgr.submit("test_job", dummy, "hello")
        record = self.mgr.get(task_id)
        assert record is not None
        assert record.job_type == "test_job"
        assert record.status in (TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.COMPLETED)

        await asyncio.sleep(0.1)
        record = self.mgr.get(task_id)
        assert record.status == TaskStatus.COMPLETED
        assert record.result == {"echo": "hello"}
        assert record.completed_at is not None

    @pytest.mark.asyncio
    async def test_failed_task(self):
        async def fail(x):
            raise ValueError("boom")

        task_id = self.mgr.submit("bad_job", fail, "oops")
        await asyncio.sleep(0.1)

        record = self.mgr.get(task_id)
        assert record.status == TaskStatus.FAILED
        assert record.error == "boom"
        assert record.completed_at is not None

    @pytest.mark.asyncio
    async def test_bounded_history(self):
        async def noop():
            return {}

        ids = []
        for _ in range(7):
            ids.append(self.mgr.submit("job", noop))
        await asyncio.sleep(0.1)

        assert len(self.mgr._tasks) == 5
        assert self.mgr.get(ids[0]) is None
        assert self.mgr.get(ids[1]) is None
        assert self.mgr.get(ids[-1]) is not None

    @pytest.mark.asyncio
    async def test_list_tasks(self):
        async def noop():
            return {}

        for _ in range(3):
            self.mgr.submit("job", noop)
        await asyncio.sleep(0.1)

        tasks, total = self.mgr.list_tasks(offset=0, limit=10)
        assert total == 3
        assert len(tasks) == 3

        tasks, total = self.mgr.list_tasks(offset=0, limit=2)
        assert len(tasks) == 2

    @pytest.mark.asyncio
    async def test_stats(self):
        async def noop():
            return {}

        self.mgr.submit("job", noop)
        self.mgr.submit("job", noop)
        await asyncio.sleep(0.1)

        stats = self.mgr.stats()
        assert stats["total"] == 2
        assert stats["completed"] == 2
        assert stats["failed"] == 0

    def test_to_dict(self):
        record = TaskRecord("abc123", "test_job")
        d = record.to_dict()
        assert d["task_id"] == "abc123"
        assert d["job_type"] == "test_job"
        assert d["status"] == "pending"
        assert d["result"] is None
        assert d["error"] is None
        assert d["completed_at"] is None

    def test_get_nonexistent(self):
        assert self.mgr.get("does_not_exist") is None


# ---------------------------------------------------------------------------
# Integration tests — HTTP endpoints
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_submit_agent_query():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/tasks/submit", json={
            "job_type": "agent_query",
            "question": "What is revenue?",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "task_id" in data
        assert data["job_type"] == "agent_query"
        assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_submit_workflow_run():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/tasks/submit", json={
            "job_type": "workflow_run",
            "question": "Analyze risk factors",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_type"] == "workflow_run"


@pytest.mark.asyncio
async def test_submit_invalid_job_type():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/tasks/submit", json={
            "job_type": "invalid_type",
            "question": "test",
        })
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_poll_task_status():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        submit = await client.post("/tasks/submit", json={
            "job_type": "agent_query",
            "question": "What is revenue?",
        })
        task_id = submit.json()["task_id"]

        await asyncio.sleep(0.5)

        resp = await client.get(f"/tasks/{task_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == task_id
        assert data["status"] in ("pending", "running", "completed", "failed")


@pytest.mark.asyncio
async def test_poll_nonexistent_task():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/tasks/does_not_exist")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_tasks_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/tasks/")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data


@pytest.mark.asyncio
async def test_task_stats_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/tasks/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "pending" in data
        assert "completed" in data
        assert "failed" in data


@pytest.mark.asyncio
async def test_v1_task_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/tasks/submit", json={
            "job_type": "agent_query",
            "question": "v1 test",
        })
        assert resp.status_code == 200

        resp = await client.get("/api/v1/tasks/stats")
        assert resp.status_code == 200

        resp = await client.get("/api/v1/tasks/")
        assert resp.status_code == 200
