"""
Configuration and constants for application
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# OpenAI/OpenRouter Configuration
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

MODEL = "x-ai/grok-code-fast-1"

# System Prompt
SYSTEM_PROMPT = """You are a helpful customer support agent for an e-commerce company.

CANCELLATION PROCESS:
1. When user wants to cancel, call generate_cancellation_code(order_id)
2. Inform the user that a verification code has been generated
3. Wait for the user to provide the verification code
4. Call cancel_order_with_verification(order_id, code)

GUARDRAILS:
- ONLY answer order-related questions
- For non-order questions: "I can only assist with order-related queries."
- ALWAYS use verification for cancellations
- Be helpful and professional
"""

# Tools definition for the AI agent
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "Get order status by order ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "Order ID (ORD-XXX)"}
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_cancellation_code",
            "description": "Generate verification code for cancellation",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_order_with_verification",
            "description": "Cancel order with verification code",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                    "verification_code": {"type": "string"},
                },
                "required": ["order_id", "verification_code"],
            },
        },
    },
]

# CORS Configuration
CORS_ORIGINS = ["http://localhost:3000", "http://localhost:5173"]
