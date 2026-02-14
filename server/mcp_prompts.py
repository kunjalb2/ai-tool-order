"""
MCP Prompts module for Kunjal Agents
Defines prompts for common workflows
"""
import logging

logger = logging.getLogger(__name__)


def check_status_prompt(order_id: str) -> str:
    """Generate a prompt for checking order status.

    Args:
        order_id: The order to check

    Returns:
        A formatted prompt for the agent
    """
    return f"""The user wants to check the status of order {order_id}.

Please use the get_order_details tool to:
1. Retrieve the order information
2. Summarize the current status
3. List the items in the order
4. Provide the total amount
5. Mention any relevant delivery information

Be friendly and professional in your response."""


def cancel_workflow_prompt(order_id: str, reason: str = "") -> str:
    """Generate a prompt for the cancellation workflow.

    Args:
        order_id: The order to cancel
        reason: Optional reason for cancellation

    Returns:
        A formatted prompt for the cancellation workflow
    """
    reason_text = f" Reason: {reason}" if reason else ""
    return f"""The user wants to cancel order {order_id}.{reason_text}

Follow this workflow:
1. Use get_order_details to verify the order exists and can be cancelled
2. Use request_order_cancellation to initiate the cancellation process
3. Inform the user that a verification code has been sent to their email
4. Wait for the user to provide the verification code
5. Use confirm_cancellation with the approval_id and verification_code

Be empathetic and helpful throughout the process."""


# Prompt metadata for listing available prompts
MCP_PROMPTS_METADATA = [
    {
        "name": "check_status_prompt",
        "description": "Generate a prompt for checking order status",
        "arguments": [
            {"name": "order_id", "type": "string", "required": True, "description": "Order ID to check"}
        ]
    },
    {
        "name": "cancel_workflow_prompt",
        "description": "Generate a prompt for the cancellation workflow",
        "arguments": [
            {"name": "order_id", "type": "string", "required": True, "description": "Order ID to cancel"},
            {"name": "reason", "type": "string", "required": False, "description": "Optional reason for cancellation"}
        ]
    }
]

# Prompt function mapping
MCP_PROMPT_FUNCTIONS = {
    "check_status_prompt": check_status_prompt,
    "cancel_workflow_prompt": cancel_workflow_prompt
}
