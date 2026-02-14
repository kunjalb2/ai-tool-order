"""
SSE event streaming endpoints
"""
import asyncio
import json
from typing import AsyncGenerator
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from services.session_manager import session_manager

router = APIRouter()


async def event_stream(session_id: str) -> AsyncGenerator[str, None]:
    """Generate SSE events for a session"""
    print(f"DEBUG: New SSE stream for session {session_id}")

    # Check if session exists
    session = session_manager.get_session(session_id)
    if not session:
        print(f"DEBUG: Session {session_id} not found")
        yield f"data: {json.dumps({'type': 'error', 'data': {'message': 'Session not found'}})}\n\n"
        return

    # Get or create event queue for this session (don't create new queue on reconnect)
    queue = session_manager.get_event_queue(session_id)
    if not queue:
        print(f"DEBUG: No queue for session {session_id}, creating new one")
        queue = session_manager.get_or_create_event_queue(session_id)

    try:
        # First, drain any pending events that might be in the queue
        print(f"DEBUG: Starting event stream for session {session_id}, queue size: {queue.qsize()}")

        while True:
            # Wait for events
            print(f"DEBUG: Waiting for events in session {session_id}...")
            try:
                # Use a timeout to avoid hanging forever
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                print(f"DEBUG: Got event for session {session_id}: {event.get('type')}, data: {str(event.get('data', {}))[:100]}")
                yield f"data: {json.dumps(event)}\n\n"
            except asyncio.TimeoutError:
                # Send a keepalive comment to keep the connection alive
                yield ":keepalive\n\n"
    except asyncio.CancelledError:
        # Client disconnected - don't cleanup session or queue, it may reconnect
        print(f"DEBUG: SSE stream cancelled for session {session_id}")
        pass


@router.get("/api/events")
async def events(session_id: str):
    """SSE endpoint for real-time events"""
    return StreamingResponse(
        event_stream(session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}


@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Agent Backend - Frontend Integration",
        "endpoints": {
            "POST /api/chat": "Send chat message",
            "GET /api/events": "SSE event stream",
            "POST /api/approval": "Handle approval",
            "GET /health": "Health check",
        },
    }
