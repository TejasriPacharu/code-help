"""
This file has the routes and main server setup for the Copilot backend.

"""

from __future__ import annotations as _annotations

import json
import os
from typing import Any, Dict

from chatkit.server import StreamingResult
from fastapi import Depends, FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse

from server import CopilotServer


app = FastAPI(
    title="AI Software Engineering Copilot",
    description="Multi-agent system for code analysis, debugging, testing, security review, and documentation",
    version="1.0.0",
)

# Disable tracing for zero data retention orgs
os.environ.setdefault("OPENAI_TRACING_DISABLED", "1")

# CORS configuration (adjust as needed for deployment)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chat_server = CopilotServer()


def get_server() -> CopilotServer:
    return chat_server


@app.post("/chatkit")
async def chatkit_endpoint(
    request: Request, server: CopilotServer = Depends(get_server)
) -> Response:
    """Main chat endpoint - processes messages and streams responses."""
    payload = await request.body()
    result = await server.process(payload, {"request": request})
    if isinstance(result, StreamingResult):
        return StreamingResponse(result, media_type="text/event-stream")
    if hasattr(result, "json"):
        return Response(content=result.json, media_type="application/json")
    return Response(content=result)


@app.get("/chatkit/state")
async def chatkit_state(
    thread_id: str = Query(...),
    server: CopilotServer = Depends(get_server),
) -> Dict[str, Any]:
    """Returns current state snapshot for a thread."""
    return await server.snapshot(thread_id, {"request": None})


@app.get("/chatkit/bootstrap")
async def chatkit_bootstrap(
    server: CopilotServer = Depends(get_server),
) -> Dict[str, Any]:
    """Creates new thread and returns initial state."""
    return await server.snapshot(None, {"request": None})


@app.get("/chatkit/state/stream")
async def chatkit_state_stream(
    thread_id: str = Query(...),
    server: CopilotServer = Depends(get_server),
):
    """SSE endpoint for real-time state updates."""
    thread = await server.ensure_thread(thread_id, {"request": None})
    queue = server.register_listener(thread.id)

    async def event_generator():
        try:
            initial = await server.snapshot(thread.id, {"request": None})
            yield f"data: {json.dumps(initial, default=str)}\n\n"
            while True:
                data = await queue.get()
                yield f"data: {data}\n\n"
        finally:
            server.unregister_listener(thread.id, queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "ai-copilot"}


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint with service information."""
    return {
        "service": "AI Software Engineering Copilot",
        "version": "1.0.0",
        "agents": [
            "Triage Agent",
            "Bug Diagnosis Agent",
            "Refactoring Agent",
            "Test Generator Agent",
            "Security Review Agent",
            "Documentation Agent",
        ],
    }
