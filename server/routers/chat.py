"""
Chat and approval endpoints
"""

import asyncio
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import SessionLocal, User
from models.schemas import ChatRequest, ApprovalRequest
from services.session_manager import session_manager
from services.agent import process_agent_message, handle_approval
from services.auth import get_current_user

router = APIRouter()


def get_user_dict(user: User) -> dict:
    """Convert User object to dict for passing to services"""
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
    }


@router.post("/api/chat")
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """Handle chat messages"""
    # Convert user to dict and override current_user
    user_dict = get_user_dict(current_user)

    # Get or create session with current_user info
    session_id = request.session_id or session_manager.create_session(user_dict)

    # Create database session for background task
    async def process_with_db():
        db = SessionLocal()
        try:
            await process_agent_message(request.message, session_id, db, user_dict)
        finally:
            db.close()

    # Start processing in the background
    asyncio.create_task(process_with_db())

    # Return session ID
    return {"session_id": session_id}


@router.post("/api/approval")
async def approval(
    request: ApprovalRequest, current_user: User = Depends(get_current_user)
):
    """Handle approval responses"""
    # Convert user to dict
    user_dict = get_user_dict(current_user)

    # Create database session for background task
    async def process_with_db():
        db = SessionLocal()
        try:
            await handle_approval(
                request.id, request.approved, request.userInput, db, user_dict
            )
        except Exception as e:
            print(f"ERROR in approval processing: {e}")
            import traceback

            traceback.print_exc()
            await session_manager.emit_event(request.id, "error", {"message": str(e)})
        finally:
            db.close()

    # Start processing in background (like chat endpoint)
    asyncio.create_task(process_with_db())

    return {"status": "ok"}
