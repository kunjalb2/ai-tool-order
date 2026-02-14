"""
Session management for SSE connections
"""
import asyncio
import uuid
from typing import Optional, Dict
from sqlalchemy.orm import Session

from database import SessionLocal, User


class SessionManager:
    def __init__(self):
        # In-memory storage only for event queues (SSE streams)
        # Session data is not persisted, only event queues are kept
        self.event_queues: Dict[str, asyncio.Queue] = {}
        # Keep in-memory history and pending_approval for active sessions
        # These are not persisted to database
        self.sessions: Dict[str, Dict] = {}

    def create_session(self, current_user: Optional[Dict[str, str]] = None) -> str:
        """Create a new session with optional user information"""
        session_id = str(uuid.uuid4())

        # Build session data
        session_data = {
            "history": [],
            "pending_approval": None,
            "current_response": "",
        }

        # Add user info if provided
        if current_user:
            user_id = current_user.get("id")
            if user_id:
                # Fetch user from database
                db: Session = SessionLocal()
                try:
                    user = db.query(User).filter(User.id == user_id).first()
                    if user:
                        session_data["user_id"] = user.id
                        session_data["user_name"] = user.name
                        session_data["user_email"] = user.email
                        print(f"DEBUG: Created session {session_id} for user {user.id} ({user.email})")
                    else:
                        print(f"DEBUG: User {user_id} not found in database")
                finally:
                    db.close()

        self.sessions[session_id] = session_data
        self.event_queues[session_id] = asyncio.Queue()
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data from in-memory storage"""
        return self.sessions.get(session_id)

    def get_event_queue(self, session_id: str) -> Optional[asyncio.Queue]:
        """Get event queue for SSE streaming"""
        return self.event_queues.get(session_id)

    def get_or_create_event_queue(self, session_id: str) -> asyncio.Queue:
        """Get existing event queue or create a new one for the session"""
        if session_id not in self.event_queues:
            print(f"DEBUG: Creating new event queue for existing session {session_id}")
            self.event_queues[session_id] = asyncio.Queue()
        return self.event_queues[session_id]

    async def emit_event(self, session_id: str, event_type: str, data: dict):
        """Emit an event to the SSE stream"""
        queue = self.get_event_queue(session_id)
        if queue:
            event = {"type": event_type, "data": data}
            print(f"DEBUG: Emitting event to session {session_id}: {event_type}")
            await queue.put(event)
        else:
            print(f"DEBUG: No queue found for session {session_id}, cannot emit event {event_type}")

    def cleanup_session(self, session_id: str):
        """Clean up session data and event queue from memory"""
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.event_queues:
            del self.event_queues[session_id]


# Global session manager instance
session_manager = SessionManager()
