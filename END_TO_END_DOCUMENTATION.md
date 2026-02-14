# Kunjal Agents - End-to-End Documentation

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Backend Documentation](#backend-documentation)
4. [Frontend Documentation](#frontend-documentation)
5. [Data Flow Diagrams](#data-flow-diagrams)
6. [API Reference](#api-reference)
7. [Troubleshooting Guide](#troubleshooting-guide)

---

## System Overview

**Kunjal Agents** is an AI-powered customer support platform for an e-commerce system. It features:

- **AI Agent Integration**: Uses x-ai/grok-code-fast-1 model via OpenRouter API
- **Human-in-the-Loop Approval**: Verification codes sent via email for sensitive operations
- **Real-time Communication**: Server-Sent Events (SSE) for instant updates
- **User Authentication**: JWT-based secure authentication
- **Order Management**: Full CRUD operations on e-commerce orders

### Technology Stack

| Layer | Technology | Purpose |
|--------|-------------|---------|
| **Frontend** | React 18.3 + TypeScript + Vite | User interface |
| **Backend** | FastAPI (Python 3.11) | API & business logic |
| **Database** | PostgreSQL 15 + SQLAlchemy ORM | Data persistence |
| **AI/LLM** | OpenRouter API (x-ai/grok-code-fast-1) | Conversational AI |
| **Email** | Gmail SMTP + App Password | Verification codes |
| **Real-time** | Server-Sent Events (SSE) | Bidirectional communication |

---

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                                │
│  ┌──────────────────┐              ┌──────────────────┐           │
│  │   React App      │              │   Login/Register│           │
│  │   (TypeScript)    │◄────────────▶│   (Pages)       │           │
│  └────────┬─────────┘              └──────────────────┘           │
│           │                                                            │
│           │ JWT Token (localStorage)                                    │
│           │                                                            │
└───────────┼────────────────────────────────────────────────────────────────┘
            │
            │ HTTP/SSE
            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                                │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐        │
│  │    Auth     │  │    Chat     │  │   Events     │        │
│  │   Router    │  │   Router    │  │   Router     │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘        │
│         │                  │                  │                      │
│         │                  │                  │                      │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼───────┐        │
│  │  Auth       │  │   Agent     │  │ Session      │        │
│  │  Service   │  │  Service   │  │  Manager    │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘        │
│         │                  │                  │                      │
│         │                  │                  │                      │
│  ┌──────▼──────────────────▼──────────────────▼───────┐        │
│  │              PostgreSQL Database                │        │
│  │         (users + orders tables)               │        │
│  └────────────────────────────────────────────────┘        │
│                                                                 │
│  ┌──────────────────────────────────────────────────┐        │
│  │          External Services                  │        │
│  │  - OpenRouter API (AI Model)               │        │
│  │  - Gmail SMTP (Verification Emails)       │        │
│  └──────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| **Auth Router** | User registration, login, JWT token generation |
| **Chat Router** | Message processing, approval handling |
| **Events Router** | SSE streaming, health checks |
| **Agent Service** | AI conversation flow, tool calling logic |
| **Auth Service** | Password hashing, JWT validation, user context |
| **Session Manager** | In-memory session storage, event queues |
| **Tools Service** | Database operations for orders |

---

## Backend Documentation

### Project Structure

```
server/
├── api.py                    # FastAPI app, CORS, router registration
├── config.py                 # AI model config, tools, system prompt
├── database.py               # SQLAlchemy models, email, DB init
├── seed_db.py                # Database seeding script
│
├── models/
│   └── schemas.py            # Pydantic models (request/response)
│
├── routers/
│   ├── auth.py               # /api/auth/* endpoints
│   ├── chat.py               # /api/chat, /api/approval
│   └── events.py             # /api/events SSE, /health
│
└── services/
    ├── agent.py              # AI processing, tool execution
    ├── auth.py               # JWT tokens, password hashing
    ├── session_manager.py    # In-memory session management
    └── tools.py              # Order database operations
```

### Database Schema

#### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Orders Table
```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR UNIQUE NOT NULL,        -- Format: "ORD-001"
    user_id INTEGER REFERENCES users(id),
    customer_name VARCHAR NOT NULL,
    status VARCHAR NOT NULL,                -- processing, shipped, cancelled, delivered
    items JSONB NOT NULL,                   -- Array of item names
    total FLOAT NOT NULL,
    date TIMESTAMP NOT NULL,
    verification_codes JSONB DEFAULT '[]',     -- Array of 6-digit codes
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Relationship**: One user has many orders (One-to-Many)

### Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant Database

    User->>Frontend: Enter credentials
    Frontend->>Backend: POST /api/auth/login
    Backend->>Database: Query user by email
    Database-->>Backend: User record
    Backend->>Backend: Verify password (bcrypt)
    Backend->>Backend: Generate JWT token
    Backend-->>Frontend: {access_token, name, email}
    Frontend->>Frontend: Store in localStorage
    Frontend->>Frontend: Redirect to /chat
```

**JWT Token Details**:
- **Algorithm**: HS256
- **Expiry**: 24 hours
- **Claims**: `{sub: user_email, exp: timestamp}`
- **Secret**: Configured in `services/auth.py` (CHANGE IN PRODUCTION!)

### AI Agent Flow

#### Conversation Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant AI
    participant DB

    User->>Frontend: Send message
    Frontend->>Backend: POST /api/chat + JWT
    Backend->>Backend: Create/Get session
    Backend->>DB: Get user context (if authenticated)
    DB-->>Backend: User info
    Backend->>Backend: Add to conversation history
    Backend->>AI: Call with history + tools
    AI-->>Backend: Response
    alt-- Tool Call
        Backend->>Backend: Execute tool
        Backend->>DB: Database operation
        DB-->>Backend: Result
        Backend->>AI: Continue with tool result
        AI-->>Backend: Final response
    end
    Backend-->>Frontend: SSE "message" event
    Backend-->>Frontend: SSE "done" event
```

#### Available Tools

| Tool | Purpose | Parameters | Returns |
|-------|---------|-------------|---------|
| `get_order_status` | Query order information | `order_id` (string) | Order details |
| `generate_cancellation_code` | Start cancellation process | `order_id` (string) | Verification code (via email) |
| `cancel_order_with_verification` | Complete cancellation | `order_id`, `verification_code` | Cancellation confirmation |

#### Cancellation Approval Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant AI
    participant Email

    User->>Frontend: "Cancel my order"
    Frontend->>Backend: POST /api/chat
    Backend->>AI: User message
    AI->>Backend: Call generate_cancellation_code()
    Backend->>Backend: Generate 6-digit code
    Backend->>Backend: Store in pending_approval
    Backend->>DB: Save verification code
    Backend->>Email: Send verification email
    Backend-->>Frontend: SSE "approval" event
    Frontend->>User: Show approval modal
    User->>Frontend: Enter code + Approve
    Frontend->>Backend: POST /api/approval
    Backend->>Backend: Verify code
    Backend->>DB: Update order status
    Backend->>AI: Continue with cancellation result
    AI-->>Backend: Final response
    Backend-->>Frontend: SSE "message" + "done"
```

### Session Management

**Session Storage** (In-memory, NOT persisted):

```python
{
    "session_id": {
        "history": [                          # Conversation for AI context
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."}
        ],
        "user_id": 123,                       # Linked user ID (if authenticated)
        "user_name": "John Doe",               # User context for AI
        "user_email": "john@example.com",
        "pending_approval": {                    # Stashed during approval flow
            "code": "123456",
            "order_id": "ORD-001",
            "user_email": "john@example.com"
        },
        "current_response": None,                # Active AI response
        "event_queue": asyncio.Queue()          # SSE event queue
    }
}
```

**Important Behaviors**:
- Sessions persist on SSE reconnect (allow reconnection)
- Sessions only cleared on server restart
- User context auto-injected into AI prompt when available
- Event queues recreated if needed on reconnect

### API Endpoints

#### Authentication Endpoints

**POST `/api/auth/register`**
- **Purpose**: Create new user account
- **Request**:
  ```json
  {
    "name": "John Doe",
    "email": "john@example.com",
    "password": "securepass123"
  }
  ```
- **Response** (201 Created):
  ```json
  {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhb...",
    "token_type": "bearer",
    "name": "John Doe",
    "email": "john@example.com"
  }
  ```
- **Error** (400 Bad Request):
  ```json
  {
    "detail": "Email already registered"
  }
  ```

**POST `/api/auth/login`**
- **Purpose**: Authenticate existing user
- **Request**:
  ```json
  {
    "email": "john@example.com",
    "password": "securepass123"
  }
  ```
- **Response** (200 OK):
  ```json
  {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhb...",
    "token_type": "bearer",
    "name": "John Doe",
    "email": "john@example.com"
  }
  ```
- **Error** (401 Unauthorized):
  ```json
  {
    "detail": "Invalid email or password"
  }
  ```

#### Chat Endpoints

**POST `/api/chat`**
- **Purpose**: Send message to AI agent
- **Authentication**: Required (JWT Bearer token)
- **Request**:
  ```json
  {
    "message": "What's my order status?",
    "session_id": "uuid-here"  // Optional: existing session
  }
  ```
- **Response** (200 OK):
  ```json
  {
    "session_id": "new-or-existing-uuid"
  }
  ```
- **Flow**: Actual responses come via SSE events

**POST `/api/approval`**
- **Purpose**: Submit approval decision
- **Authentication**: Required
- **Request**:
  ```json
  {
    "id": "session-uuid",
    "approved": true,
    "userInput": "123456"  // Optional: verification code
  }
  ```
- **Response** (200 OK):
  ```json
  {
    "status": "ok"
  }
  ```

#### Event Endpoints

**GET `/api/events?session_id={uuid}`**
- **Purpose**: SSE stream for real-time events
- **Response Type**: `text/event-stream`
- **Events**:
  - `message`: AI response message
  - `approval`: Approval request
  - `error`: Error message
  - `done`: Response complete marker

**GET `/health`**
- **Purpose**: Health check endpoint
- **Response** (200 OK): `{"status": "ok"}`

### SSE Event Types

#### Message Event
```
event: message
data: {"id":"uuid","role":"assistant","content":"...","timestamp":"..."}
```

#### Approval Event
```
event: approval
data: {"id":"session-uuid","type":"verification_code","message":"..."}
```

#### Error Event
```
event: error
data: {"message":"Error description"}
```

#### Done Event
```
event: done
data:
```

---

## Frontend Documentation

### Project Structure

```
frontend/src/
├── components/
│   ├── Chat.tsx                 # Main chat container
│   ├── ChatHeader.tsx            # Header with status + logout
│   ├── ChatMessage.tsx           # Message display
│   ├── ChatInput.tsx             # Input field + send button
│   ├── ApprovalPrompt.tsx        # Verification modal
│   ├── TypingIndicator.tsx       # Animated typing indicator
│   └── ProtectedRoute.tsx        # Auth guard for routes
│
├── context/
│   └── AuthContext.tsx           # Authentication state provider
│
├── hooks/
│   ├── useChat.ts                # Chat state + API logic
│   └── useSSE.ts                 # SSE connection management
│
├── pages/
│   ├── Login.tsx                 # Login page
│   ├── Register.tsx              # Registration page
│   └── Chat.tsx                  # Main chat page
│
├── types/
│   ├── auth.ts                   # Auth TypeScript interfaces
│   └── chat.ts                   # Chat TypeScript interfaces
│
├── App.tsx                      # Root component + routing
├── main.tsx                     # Application entry point
└── vite.config.ts               # Vite configuration
```

### TypeScript Interfaces

#### Auth Types (`types/auth.ts`)

```typescript
interface User {
  id: number;
  name: string;
  email: string;
}

interface LoginRequest {
  email: string;
  password: string;
}

interface RegisterRequest {
  name: string;
  email: string;
  password: string;
}

interface AuthResponse {
  access_token: string;
  token_type: string;
  name: string;
  email: string;
}
```

#### Chat Types (`types/chat.ts`)

```typescript
interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

interface ApprovalRequest {
  id: string;           // session_id
  type: string;         // 'verification_code'
  message: string;
  placeholder?: string;  // Input placeholder
}

type SSEEvent =
  | { type: 'message'; data: Message }
  | { type: 'approval'; data: ApprovalRequest }
  | { type: 'error'; data: { message: string } }
  | { type: 'done'; data: null };

interface ChatState {
  messages: Message[];
  isTyping: boolean;
  pendingApproval: ApprovalRequest | null;
  isConnected: boolean;
}
```

### Component Hierarchy

```
App (Router + AuthContext)
├── ProtectedRoute (auth check)
│   ├── Login Page (/login)
│   └── Register Page (/register)
│
└── ProtectedRoute (authenticated)
    └── Chat Page (/chat)
        ├── ChatHeader (status + user info + logout)
        ├── Message List (ChatMessage[])
        │   └── ChatMessage (individual message)
        ├── TypingIndicator (when AI typing)
        ├── ApprovalPrompt (when pendingApproval)
        └── ChatInput (input + send button)
```

### Custom Hooks

#### useChat Hook

**Purpose**: Manages all chat state and API interactions

**State Managed**:
- `messages`: Array of conversation messages
- `isTyping`: AI processing indicator
- `pendingApproval`: Active approval request
- `isConnected`: SSE connection status

**Functions Provided**:
- `sendMessage(message: string)`: Send to backend
- `sendApproval(approved: boolean, code?: string)`: Submit approval
- `handleSSEEvent(event: SSEEvent)`: Process SSE events

**Event Handlers**:
- `handleMessage`: Add AI message to state
- `handleApproval`: Show approval modal
- `handleError`: Display error toast
- `handleDone`: Clear typing indicator

#### useSSE Hook

**Purpose**: Manages SSE connection lifecycle

**Features**:
- Auto-reconnect with 1s delay on disconnect
- Event subscription system
- Connection status tracking
- Manual disconnect option

**Usage**:
```typescript
const { isConnected, subscribe, disconnect } = useSSE(sessionId);

useEffect(() => {
  const unsubscribe = subscribe((event) => {
    // Handle SSE event
  });
  return () => unsubscribe();
}, [sessionId]);
```

### Context Providers

#### AuthContext

**Purpose**: Global authentication state

**State**:
- `user`: User object or null
- `token`: JWT token or null
- `isLoading`: Loading state

**Functions**:
- `login(email, password)`: Authenticate user
- `register(name, email, password)`: Create account
- `logout()`: Clear auth state + redirect

**Storage**:
- Token and user stored in `localStorage`
- Persisted across page refreshes

### Page Routes

| Route | Component | Protected | Purpose |
|-------|-----------|------------|---------|
| `/` | Redirect | No | Redirects to `/chat` |
| `/login` | Login Page | No | User authentication |
| `/register` | Register Page | No | New user registration |
| `/chat` | Chat Page | Yes | Main chat interface |

### Styling

**Framework**: Tailwind CSS

**Key Classes Used**:
- Colors: `text-gray-900`, `bg-white`, `border-gray-200`
- Layout: `flex`, `items-center`, `gap-*`
- Spacing: `p-*`, `m-*`, `px-*`, `py-*`
- Typography: `text-*`, `font-*`, `font-semibold`
- Interactive: `hover:*`, `transition-*`, `disabled:*`

---

## Data Flow Diagrams

### Complete User Journey

```mermaid
flowchart TD
    Start([User opens app]) --> CheckAuth{Authenticated?}
    CheckAuth -->|No| ShowLogin[Show Login page]
    ShowLogin --> Login[User enters credentials]
    Login --> RegisterOrLogin{New user?}
    RegisterOrLogin -->|Yes| Register[Registration flow]
    RegisterOrLogin -->|No| LoginAPI[POST /api/auth/login]
    Register --> LoginAPI
    LoginAPI --> StoreToken[Store JWT in localStorage]
    StoreToken --> RedirectChat[Redirect to /chat]
    CheckAuth -->|Yes| RedirectChat

    RedirectChat --> ChatPage[Chat interface loads]
    ChatPage --> ConnectSSE[Connect to SSE]
    ConnectSSE --> SendMessage[User sends message]
    SendMessage --> ChatAPI[POST /api/chat + JWT]
    ChatAPI --> ProcessAI[AI processes message]
    ProcessAI --> NeedTools{Needs tools?}

    NeedTools -->|Yes| ToolCall[AI calls tool]
    ToolCall --> ApprovalTool{Approval needed?}
    ApprovalTool -->|Yes| SendEmail[Send verification email]
    SendEmail --> SSEApproval[SSE: approval event]
    SSEApproval --> ShowModal[Show approval modal]
    ShowModal --> UserCode[User enters code]
    UserCode --> ApprovalAPI[POST /api/approval]
    ApprovalAPI --> VerifyCode[Verify code]
    VerifyCode --> CancelOrder[Update order: cancelled]
    CancelOrder --> ContinueAI[AI continues]
    ApprovalTool -->|No| ExecuteTool[Execute tool]
    ExecuteTool --> ContinueAI
    NeedTools -->|No| ContinueAI

    ContinueAI --> SSEMessage[SSE: message event]
    SSEMessage --> DisplayMsg[Display message]
    DisplayMsg --> SSEDone[SSE: done event]
    SSEDone --> SendMessage{More messages?}
```

### Error Handling Flow

```mermaid
flowchart TD
    APIRequest[API Request] --> TryBlock{Try Block}
    TryBlock -->|Success| Success[Return response]
    TryBlock -->|Error| CatchBlock[Catch Exception]

    CatchBlock --> ErrorType{Error type?}
    ErrorType -->|HTTPException| HTTPError[Return HTTP error response]
    ErrorType -->|Database| DBError[Rollback transaction]
    ErrorType -->|Other| GenericError[Return 500 error]

    DBError --> LogError[Log error details]
    LogError --> HTTPError

    HTTPError --> SSEErrorEvent[SSE: error event]
    SSEErrorEvent --> ShowErrorToast[Display error to user]
```

---

## API Reference

### Quick Reference

| Method | Endpoint | Auth | Purpose |
|--------|----------|-------|---------|
| POST | `/api/auth/register` | No | Create new user |
| POST | `/api/auth/login` | No | Authenticate user |
| POST | `/api/chat` | Yes | Send message to AI |
| POST | `/api/approval` | Yes | Submit approval |
| GET | `/api/events` | No* | SSE stream |
| GET | `/health` | No | Health check |

*Authentication via session_id query parameter

### Request Headers

```http
Content-Type: application/json
Authorization: Bearer <jwt_token>
```

### Response Format

**Success Response**:
```json
{
  "field": "value",
  "another_field": "another_value"
}
```

**Error Response**:
```json
{
  "detail": "Error message description"
}
```

### Status Codes

| Code | Meaning |
|-------|---------|
| 200 | OK - Request successful |
| 201 | Created - Resource created |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Authentication failed |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error - Backend error |

---

## Troubleshooting Guide

### Common Issues

#### 1. SSE Connection Drops

**Symptoms**:
- Status shows "Connecting" (RED icon)
- Messages not received
- Approval events not showing

**Solutions**:
1. Check browser console for `[SSE]` logs
2. Verify `/api/events?session_id=<id>` is accessible
3. Check backend logs for "SSE stream cancelled"
4. Ensure consistent session_id across requests
5. Check CORS configuration

#### 2. Approval Flow Fails

**Symptoms**:
- Approval popup appears but submission errors
- Code verification fails
- Email not received

**Solutions**:
1. Verify Gmail App Password is correct
2. Check email spam/junk folder
3. Ensure database has verification_codes column
4. Check session_id matches between events and approval
5. Verify order status allows cancellation (processing/shipped)

#### 3. Authentication Issues

**Symptoms**:
- Login fails with correct credentials
- Token rejected on API calls
- Protected routes redirect to login

**Solutions**:
1. Verify password hash comparison (bcrypt)
2. Check JWT secret key consistency
3. Ensure token stored in localStorage
4. Verify Authorization header format: `Bearer <token>`
5. Check token expiration (24 hours)

#### 4. Database Errors

**Symptoms**:
- "relation does not exist" errors
- Orders not saving
- User lookup fails

**Solutions**:
1. Ensure `init_db()` called on startup
2. Check PostgreSQL is running
3. Verify DATABASE_URL environment variable
4. Run `seed_db.py` for sample data
5. Check database migrations/models match schema

#### 5. Docker Networking Issues

**Symptoms**:
- Frontend can't reach backend
- Backend can't reach database
- "Connection refused" errors

**Solutions**:
1. Use service names: `http://backend:8000` (not localhost)
2. Check depends_on in docker-compose.yml
3. Verify ports mapping (8000:8000, 5173:5173)
4. Check VITE_API_URL environment variable
5. Ensure all services in same Docker network

### Debug Logging

**Backend DEBUG Logs** (prefixed with "DEBUG:"):
- `handle_approval called` - Approval request received
- `Sending message event to session` - Response queued
- `Emitting event to session` - Event sent via SSE
- `Got event for session` - Event delivered
- `Querying order for user` - Database operation
- `Creating new event queue for existing session` - Reconnection detected

**Frontend Logs**:
- `[SSE]` - Connection state changes
- `[Chat]` - Message operations (implicit)
- Browser console - All SSE events

---

## Quick Start Guide

### For Developers

1. **Clone repository**
   ```bash
   git clone <repo-url>
   cd kunjal-agents
   ```

2. **Configure environment**
   ```bash
   # Create .env file
   OPENROUTER_API_KEY=your_key_here
   GMAIL_EMAIL=your@gmail.com
   GMAIL_APP_PASSWORD=your_app_password
   DATABASE_URL=postgresql://user:pass@localhost/db
   ```

3. **Start services**
   ```bash
   # Option 1: Using script
   ./start.sh

   # Option 2: Manual
   cd server && python api.py &
   cd frontend && npm run dev
   ```

4. **Access application**
   - Frontend: http://localhost:5173
   - Backend: http://localhost:8000
   - API Docs: http://localhost:8000/docs

5. **Register and login**
   - Create account at /register
   - Login at /login
   - Start chatting at /chat

---

## Summary

Kunjal Agents is a complete full-stack application demonstrating:

- **Modern Architecture**: FastAPI + React with SSE
- **AI Integration**: Tool calling with approval flow
- **Security**: JWT authentication + bcrypt hashing
- **Real-time**: Server-Sent Events for instant updates
- **Email Integration**: Verification codes for sensitive actions
- **Docker Support**: Full containerization ready

The system is production-ready with proper error handling, logging, and user feedback.
