"""
MCP Router module for Kunjal Agents
Defines MCP-specific API endpoints with JWT authentication
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

from services.auth import get_current_user
from database import User

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class ToolExecutionRequest(BaseModel):
    tool_name: str
    params: Dict[str, Any]


class ToolListResponse(BaseModel):
    tools: list


class ResourceListResponse(BaseModel):
    resources: list


class PromptListResponse(BaseModel):
    prompts: list


class HealthResponse(BaseModel):
    status: str
    message: str


# ============================================================================
# MCP Tools Endpoints
# ============================================================================

@router.get("/api/mcp/tools", response_model=ToolListResponse)
async def list_mcp_tools(current_user: User = Depends(get_current_user)):
    """List all available MCP tools"""
    from mcp_tools import MCP_TOOLS_METADATA

    return {
        "tools": MCP_TOOLS_METADATA
    }


@router.post("/api/mcp/tools/execute")
async def execute_mcp_tool(
    request: ToolExecutionRequest,
    current_user: User = Depends(get_current_user)
):
    """Execute an MCP tool"""
    user_dict = {"id": str(current_user.id), "email": current_user.email, "name": current_user.name}

    # Add user_id to params
    params = request.params.copy()
    params["current_user_id"] = user_dict["id"]

    # Import tool functions
    from mcp_tools import MCP_TOOL_FUNCTIONS

    tool_func = MCP_TOOL_FUNCTIONS.get(request.tool_name)
    if not tool_func:
        logger.error(f"Tool {request.tool_name} not found")
        raise HTTPException(status_code=404, detail=f"Tool {request.tool_name} not found")

    try:
        logger.info(f"Executing MCP tool: {request.tool_name} for user {user_dict['id']}")
        result = await tool_func(**params)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error executing tool {request.tool_name}: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# MCP Resources Endpoints
# ============================================================================

@router.get("/api/mcp/resources")
async def list_mcp_resources(current_user: User = Depends(get_current_user)):
    """List all available MCP resources"""
    from mcp_resources import MCP_RESOURCES_METADATA

    return {
        "resources": MCP_RESOURCES_METADATA
    }


@router.get("/api/mcp/resources/{uri}")
async def get_mcp_resource(uri: str, current_user: User = Depends(get_current_user)):
    """Get a specific MCP resource by URI"""
    from mcp_resources import MCP_RESOURCE_FUNCTIONS

    # Parse the URI to determine which resource to fetch
    for uri_pattern, resource_func in MCP_RESOURCE_FUNCTIONS.items():
        if uri.startswith(uri_pattern):
            # Extract the identifier from the URI
            identifier = uri[len(uri_pattern):]
            try:
                result = await resource_func(identifier)
                return {"success": True, "data": result}
            except Exception as e:
                logger.error(f"Error fetching resource {uri}: {e}")
                return {"success": False, "error": str(e)}

    return {"success": False, "error": f"Resource not found: {uri}"}


# ============================================================================
# MCP Prompts Endpoints
# ============================================================================

@router.get("/api/mcp/prompts")
async def list_mcp_prompts(current_user: User = Depends(get_current_user)):
    """List all available MCP prompts"""
    from mcp_prompts import MCP_PROMPTS_METADATA

    return {
        "prompts": MCP_PROMPTS_METADATA
    }


@router.post("/api/mcp/prompts/{prompt_name}")
async def get_mcp_prompt(
    prompt_name: str,
    params: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Get a specific MCP prompt by name with parameters"""
    from mcp_prompts import MCP_PROMPT_FUNCTIONS

    prompt_func = MCP_PROMPT_FUNCTIONS.get(prompt_name)
    if not prompt_func:
        return {"success": False, "error": f"Prompt {prompt_name} not found"}

    try:
        result = prompt_func(**params)
        return {"success": True, "prompt": result}
    except Exception as e:
        logger.error(f"Error generating prompt {prompt_name}: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# MCP Health Endpoint
# ============================================================================

@router.get("/api/mcp/health")
async def mcp_health() -> HealthResponse:
    """MCP health check endpoint"""
    from mcp_server import get_all_approval_states
    from mcp_tools import MCP_TOOLS_METADATA
    from mcp_resources import MCP_RESOURCES_METADATA
    from mcp_prompts import MCP_PROMPTS_METADATA

    approval_states = get_all_approval_states()

    return HealthResponse(
        status="ok",
        message=f"MCP server is running with {len(MCP_TOOLS_METADATA)} tools, "
                f"{len(MCP_RESOURCES_METADATA)} resources, "
                f"{len(MCP_PROMPTS_METADATA)} prompts, "
                f"and {len(approval_states)} pending approvals"
    )
