"""
FastAPI Backend with SSE for AI Agent - Frontend Integration
================================================================
Main application entry point with CORS configuration and router setup.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS
from routers import chat, events, auth, mcp
from database import init_db

# Create FastAPI app
app = FastAPI()


# ============================================================================
# Startup Event - Initialize Database
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    init_db()


# ============================================================================
# CORS Configuration
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Include Routers
# ============================================================================

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(events.router)
app.include_router(mcp.router)

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
