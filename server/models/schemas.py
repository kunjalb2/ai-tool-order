"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict


# Auth Schemas
class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2)
    email: str
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    name: str
    email: str


# Chat Schemas
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    current_user: Optional[Dict[str, str]] = None


class ApprovalRequest(BaseModel):
    id: str  # Approval ID (can be session_id)
    approved: bool
    userInput: Optional[str] = None
    current_user: Optional[Dict[str, str]] = None
