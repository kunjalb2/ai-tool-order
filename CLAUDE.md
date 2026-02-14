# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kunjal Agents is an AI agent platform with a human-in-the-loop approval flow for sensitive operations. The system uses Server-Sent Events (SSE) for real-time bidirectional communication between a React frontend and FastAPI backend.

**Database**: PostgreSQL with SQLAlchemy ORM for persistent storage of users and orders.
**Authentication**: JWT tokens (24-hour expiry) stored in localStorage.

## Development Commands

### Local Development (without Docker)

Backend:
```bash
cd server && pip install -r requirements.txt
cd server && python api.py
cd server && python seed_db.py    # Seed database with sample data
```

Frontend:
```bash
cd frontend && npm install
cd frontend && npm run dev
cd frontend && npm run build
cd frontend && npm run lint
```

Both:
```bash
./start.sh  # Starts both backend (port 8000) and frontend (port 5173)
```

### Docker Development

```bash
# Build and start all services (postgres, backend, frontend)
docker-compose up -d --build

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Rebuild specific service
docker-compose up -d --build backend

# Execute commands in container
docker-compose exec backend env
docker-compose exec postgres psql -U kunjal_user -d kunjal_agents

# Stop all services
docker-compose down

# Stop and remove volumes (fresh database)
docker-compose down -v
```

**Important**: In Docker, frontend connects to backend via `http://backend:8000` (Docker service name), not `localhost:8000`. The `VITE_API_URL` environment variable handles this.

## Backend Architecture

The backend follows a modular FastAPI structure with separation of concerns:

```
server/
├── api.py                    # Main app (CORS, router registration, startup event)
├── config.py                 # Configuration (MODEL, tools, system prompt, CORS)
├── database.py               # SQLAlchemy models, email sending, init_db()
├── seed_db.py                # Database seeding script with sample data
├── models/
│   └── schemas.py            # Pydantic request/response models
├── routers/
│   ├── auth.py               # POST /api/auth/register, POST /api/auth/login
│   ├── chat.py               # POST /api/chat, POST /api/approval
│   └── events.py             # GET /api/events SSE endpoint, /health, /
└── services/
    ├── agent.py              # Agent processing (process_agent_message, handle_approval)
    ├── auth.py              # JWT tokens, password hashing (bcrypt)
    ├── session_manager.py    # SessionManager class (in-memory sessions)
    └── tools.py              # Database tools (order operations)
```

**Flow**: api.py → routers → services → database

**Database Initialization**: Tables are auto-created on backend startup via `init_db()` in `api.py`'s startup event handler.

## Frontend Architecture

React 18 + TypeScript + Tailwind CSS with Vite dev server.

**Key hooks**:
- `useChat` - Chat state management, API calls, event handlers
- `useSSE` - SSE connection with auto-reconnect (1s delay)

**Context**:
- `AuthContext` - User authentication state and logout

**Components**:
- `Chat.tsx` - Main chat container
- `ChatHeader.tsx` - Header with user info and logout button
- `ApprovalPrompt.tsx` - Human-in-the-loop approval modal
- `ChatInput.tsx` - Message input with submit button
- `ChatMessage.tsx` - Individual message display
- `TypingIndicator.tsx` - Shows when AI is "typing"

**Pages**:
- `Login.tsx` - Login form
- `Register.tsx` - Registration form

## Database Schema

### Users Table
- id (PK, Integer)
- name (String, not null)
- email (String, unique, not null)
- password_hash (String, not null) - bcrypt hashed
- created_at (DateTime)

### Orders Table
- id (PK, Integer, auto-increment)
- order_id (String, unique, not null) - e.g., "ORD-001"
- user_id (Integer, FK to users.id)
- customer_name (String, not null)
- status (String, not null) - processing, shipped, cancelled, etc.
- items (JSON, not null) - List of item names
- total (Float, not null)
- date (DateTime, not null)
- verification_codes (JSON, default=[]) - List of generated verification codes
- created_at (DateTime)
- updated_at (DateTime)

Relationship: orders.user_id -> users.id (Many-to-One)

## Session Management

Sessions are stored in-memory (not database) with:
- `history`: Conversation history for AI context
- `pending_approval`: Stashed approval state waiting for user response
- `event_queue`: Async queue for SSE events

Sessions are created with optional user linkage:
- If `current_user` provided (authenticated): Session linked to user record via database lookup
- If not authenticated: Session created without user linkage

**Important**: Sessions are NOT cleaned up when SSE disconnects. They persist to allow reconnection. Only server restart clears all sessions.

The `SessionManager` class in `services/session_manager.py` manages all sessions. When a session has `user_id`, user context (name, email) is automatically appended to the system prompt for AI calls.

## Authentication Flow

1. User registers or logs in via `/api/auth/register` or `/api/auth/login`
2. Backend validates credentials and creates JWT token (24-hour expiry)
3. Frontend stores token in localStorage
4. All subsequent API requests include `Authorization: Bearer <token>` header
5. Backend validates token via `get_current_user()` dependency in services/auth.py

## SSE Event Flow

User sends message -> POST /api/chat (with or without session_id)
    ↓
Backend creates/retrieves session, starts processing
    ↓
    ├─→ Simple query -> AI responds directly
    │                       ↓
    │              SSE: "message" event -> SSE: "done" event
    │
    └─→ Needs approval (e.g., cancel) -> AI calls generate_cancellation_code
                ↓                ↓
                ↓          Stores pending_approval in session (with code, order_id, user_email)
                ↓          Sends verification email
                ↓          SSE: "approval" event (with verification code)
                ↓
                User enters code and approves
                ↓
                ↓          POST /api/approval (with session_id, approved, userInput, current_user)
                ↓                ↓
                ↓          Backend verifies code, executes cancellation, continues AI processing
                ↓          AI processes tool result
                ↓          SSE: "message" event (result) -> SSE: "done" event

## Email Integration

Verification emails are sent when cancellation codes are generated via `send_verification_email()` in `database.py`:
- Uses Gmail SMTP with App Password (GMAIL_EMAIL, GMAIL_APP_PASSWORD in .env)
- Sends 6-digit code with order details
- Retrieves user email from database via Order.user relationship
- Email contains: verification code, order ID, customer name

## Tool Calling

The AI agent uses OpenAI-compatible function calling with three tools defined in `config.py`:
- `get_order_status(order_id)` - Query order information (with user authorization check)
- `generate_cancellation_code(order_id)` - Generate 6-digit code, send email, emit approval event
- `cancel_order_with_verification(order_id, verification_code)` - Execute cancellation

When `generate_cancellation_code` is called, the agent stores `pending_approval` in the session and returns early (waits for user approval). After approval via `/api/approval`, `handle_approval()` continues the agent loop with the tool result.

## Environment Variables

Required in `.env` (or passed to Docker):
- `OPENROUTER_API_KEY` - For AI model access (x-ai/grok-code-fast-1)
- `DATABASE_URL` - PostgreSQL connection string (auto-set in docker-compose)
- `GMAIL_EMAIL` - Gmail account for sending verification emails
- `GMAIL_APP_PASSWORD` - Gmail App Password (not regular password)

## Important Dependencies

**bcrypt==3.2.2** - Required for passlib 1.7.4 compatibility. bcrypt 4.x is incompatible with passlib 1.7.4 and will cause "password cannot be longer than 72 bytes" errors.

## Troubleshooting

### SSE Connection Issues

Problem: Status shows "Connecting" with RED icon, approval events not received

Causes:
- SSE connection dropping after approval event
- Event queue not being drained on reconnection
- Session timing out

Solutions:
1. Check backend logs for "SSE stream cancelled" messages
2. Verify /api/events?session_id=<id> is accessible
3. Check browser console for [SSE] prefixed logs
4. Ensure session_id is consistent between requests

### Approval Flow Not Working

Problem: Approval popup shows but submission gives errors

Causes:
- Session was cleaned up before approval submitted
- Event queue was recreated, losing pending events
- Frontend sending to wrong session
- Email not configured properly

Solutions:
1. Check backend logs for "Session not found" errors
2. Ensure session_id matches between approval event and approval request
3. Verify SSE connection is active when submitting approval
4. Check browser console for approval request logs
5. Check email configuration in .env (GMAIL_EMAIL, GMAIL_APP_PASSWORD)

### Database Issues

Problem: "relation \"users\" does not exist" or "relation \"orders\" does not exist"

Solution: Tables are auto-created on startup via `init_db()` in api.py. If still missing, restart backend container.

### Debug Logging

Backend has extensive DEBUG logging prefixed with "DEBUG:":
- `handle_approval called` - Approval request received
- `Sending message event to session` - Response being sent
- `Emitting event to session` - Event queued
- `Got event for session` - Event delivered via SSE
- `Creating new event queue for existing session` - Only when necessary (reconnecting)
- `Querying order for user` - Database operations

Frontend has `[SSE]` prefixed logs for connection state and `[Chat]` or implicit logs in useChat for message handling.
