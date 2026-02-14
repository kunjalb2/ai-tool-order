"""
MCP Server module for Kunjal Agents using FastMCP
"""
from contextlib import asynccontextmanager
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Create MCP server instance
# Note: We'll use a simplified approach without FastMCP initially for stability
# The MCP tools will be defined and exposed through the API router
mcp_name = "kunjal-agents-mcp"
mcp_instructions = "E-commerce customer support agent for order management with human-in-the-loop approval"

# Global storage for MCP approval state (similar to existing session_manager)
mcp_approval_state: Dict[str, Dict[str, Any]] = {}

@asynccontextmanager
async def mcp_lifespan():
    """Lifespan context manager for MCP server"""
    logger.info("MCP Server starting...")
    yield
    logger.info("MCP Server shutting down...")
    mcp_approval_state.clear()


def get_approval_state(approval_id: str) -> Dict[str, Any] | None:
    """Get approval state by ID"""
    return mcp_approval_state.get(approval_id)


def set_approval_state(approval_id: str, state: Dict[str, Any]) -> None:
    """Set approval state by ID"""
    mcp_approval_state[approval_id] = state


def clear_approval_state(approval_id: str) -> None:
    """Clear approval state by ID"""
    if approval_id in mcp_approval_state:
        del mcp_approval_state[approval_id]


def get_all_approval_states() -> Dict[str, Dict[str, Any]]:
    """Get all approval states (for debugging)"""
    return mcp_approval_state.copy()
