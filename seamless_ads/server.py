"""FastAPI server for the Seamless MCP Product Discovery Agent.

Run with: uvicorn seamless_ads.server:app --port 8001 --reload
"""

from __future__ import annotations

import asyncio

from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from seamless_ads.mcp_agent import run_discovery

app = FastAPI(title="Seamless Discovery Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track active discovery runs to prevent duplicates
_active_runs: set[str] = set()


class DiscoverRequest(BaseModel):
    content_id: str


async def _run_and_cleanup(content_id: str) -> None:
    try:
        await run_discovery(content_id)
    finally:
        _active_runs.discard(content_id)


@app.post("/api/discover")
async def discover(req: DiscoverRequest, background_tasks: BackgroundTasks):
    if req.content_id in _active_runs:
        return {"status": "already_running", "content_id": req.content_id}

    _active_runs.add(req.content_id)
    background_tasks.add_task(_run_and_cleanup, req.content_id)
    return {"status": "started", "content_id": req.content_id}


@app.get("/api/health")
async def health():
    return {"status": "ok"}
