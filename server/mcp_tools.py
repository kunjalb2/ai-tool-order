"""
MCP Tools module for Kunjal Agents
Defines NEW tools using MCP format with integrated approval flow
"""
from typing import Optional, Dict, List
import random
import string
import uuid
import logging

from sqlalchemy.orm import Session
from database import SessionLocal, Order, send_verification_email
from mcp_server import set_approval_state, get_approval_state

logger = logging.getLogger(__name__)


# NEW TOOL: Get Order Details (with more info than existing)
async def get_order_details(order_id: str, current_user_id: str) -> Dict:
    """Get complete details of an order including items, shipping info, and history.

    Args:
        order_id: The unique order identifier (e.g., ORD-001)
        current_user_id: The ID of the authenticated user

    Returns:
        Complete order details with items, total, status, and history
    """
    db = SessionLocal()
    try:
        order = db.query(Order).filter(
            Order.order_id == order_id,
            Order.user_id == int(current_user_id)
        ).first()

        if not order:
            return {"error": "Order not found", "success": False}

        return {
            "success": True,
            "order": {
                "order_id": order.order_id,
                "customer_name": order.customer_name,
                "status": order.status,
                "items": order.items,
                "total": float(order.total),
                "date": order.date.isoformat() if order.date else None,
                "verification_codes": order.verification_codes or []
            }
        }
    finally:
        db.close()


# NEW TOOL: Request Order Cancellation (with integrated approval)
async def request_order_cancellation(
    order_id: str,
    current_user_id: str,
    reason: Optional[str] = None
) -> Dict:
    """Request to cancel an order. This will generate a verification code and require user approval.

    Args:
        order_id: The unique order identifier
        current_user_id: The ID of the authenticated user
        reason: Optional reason for cancellation

    Returns:
        Cancellation request with verification code and approval status
    """
    db = SessionLocal()
    try:
        order = db.query(Order).filter(
            Order.order_id == order_id,
            Order.user_id == int(current_user_id)
        ).first()

        if not order:
            return {"error": "Order not found", "success": False}

        if order.status == "cancelled":
            return {"error": "Order already cancelled", "success": False}

        if order.status not in ["processing", "shipped"]:
            return {"error": f"Cannot cancel order with status '{order.status}'", "success": False}

        # Generate verification code
        code = "".join(random.choices(string.digits, k=6))

        # Initialize verification_codes list if None
        if order.verification_codes is None:
            order.verification_codes = []

        order.verification_codes.append(code)
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(order, "verification_codes")
        db.commit()

        # Store approval state
        approval_id = str(uuid.uuid4())
        set_approval_state(approval_id, {
            "order_id": order_id,
            "code": code,
            "user_id": current_user_id,
            "reason": reason,
            "status": "pending"
        })

        # Send email (reuse existing function)
        user_email = order.user.email if order.user else None
        user_name = order.user.name if order.user else order.customer_name
        if user_email:
            send_verification_email(order_id, code, user_email, user_name)

        logger.info(f"Cancellation requested for order {order_id}, approval_id: {approval_id}")

        return {
            "success": True,
            "requires_approval": True,
            "approval_id": approval_id,
            "message": f"Verification code sent to {user_email}. Please use the confirm_cancellation tool with the code.",
            "order_id": order_id
        }
    finally:
        db.close()


# NEW TOOL: Confirm Cancellation (completes the approval flow)
async def confirm_cancellation(
    approval_id: str,
    verification_code: str,
    current_user_id: str
) -> Dict:
    """Confirm and complete the order cancellation using the verification code.

    Args:
        approval_id: The approval ID from request_order_cancellation
        verification_code: The 6-digit code received via email
        current_user_id: The ID of the authenticated user

    Returns:
        Cancellation confirmation with refund details
    """
    # Check approval state
    approval = get_approval_state(approval_id)
    if not approval:
        return {"error": "Invalid approval ID", "success": False}

    if approval["status"] != "pending":
        return {"error": "Approval already processed", "success": False}

    if approval["user_id"] != current_user_id:
        return {"error": "Unauthorized", "success": False}

    # Execute cancellation
    db = SessionLocal()
    try:
        order = db.query(Order).filter(
            Order.order_id == approval["order_id"]
        ).first()

        if not order:
            return {"error": "Order not found", "success": False}

        # Verify code
        if not order.verification_codes or verification_code not in order.verification_codes:
            return {"error": "Invalid verification code", "success": False}

        # Cancel order
        order.status = "cancelled"
        order.verification_codes.remove(verification_code)
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(order, "verification_codes")
        db.commit()

        # Update approval state
        set_approval_state(approval_id, {
            **approval,
            "status": "approved"
        })

        logger.info(f"Order {approval['order_id']} cancelled successfully")

        return {
            "success": True,
            "message": f"Order {approval['order_id']} cancelled successfully",
            "refund_amount": float(order.total),
            "order_id": approval["order_id"]
        }
    finally:
        db.close()


# NEW TOOL: List User Orders
async def list_user_orders(
    current_user_id: str,
    status_filter: Optional[str] = None,
    limit: int = 10
) -> Dict:
    """List all orders for the current user with optional filtering.

    Args:
        current_user_id: The ID of the authenticated user
        status_filter: Optional filter by status (e.g., 'processing', 'shipped', 'cancelled')
        limit: Maximum number of orders to return

    Returns:
        List of orders with summary information
    """
    db = SessionLocal()
    try:
        query = db.query(Order).filter(Order.user_id == int(current_user_id))

        if status_filter:
            query = query.filter(Order.status == status_filter)

        orders = query.order_by(Order.created_at.desc()).limit(limit).all()

        return {
            "success": True,
            "orders": [
                {
                    "order_id": o.order_id,
                    "status": o.status,
                    "total": float(o.total),
                    "date": o.date.isoformat() if o.date else None,
                    "customer_name": o.customer_name,
                    "item_count": len(o.items) if o.items else 0
                }
                for o in orders
            ],
            "count": len(orders)
        }
    finally:
        db.close()


# Tool metadata for listing available tools
MCP_TOOLS_METADATA = [
    {
        "name": "get_order_details",
        "description": "Get complete details of an order including items, shipping info, and history",
        "parameters": {
            "order_id": {"type": "string", "description": "Order ID (e.g., ORD-001)", "required": True},
            "current_user_id": {"type": "string", "description": "Current user ID", "required": True}
        }
    },
    {
        "name": "request_order_cancellation",
        "description": "Request order cancellation (generates verification code and requires approval)",
        "parameters": {
            "order_id": {"type": "string", "description": "Order ID", "required": True},
            "current_user_id": {"type": "string", "description": "Current user ID", "required": True},
            "reason": {"type": "string", "description": "Optional reason for cancellation", "required": False}
        }
    },
    {
        "name": "confirm_cancellation",
        "description": "Confirm cancellation with verification code",
        "parameters": {
            "approval_id": {"type": "string", "description": "Approval ID from request_order_cancellation", "required": True},
            "verification_code": {"type": "string", "description": "6-digit verification code from email", "required": True},
            "current_user_id": {"type": "string", "description": "Current user ID", "required": True}
        }
    },
    {
        "name": "list_user_orders",
        "description": "List all orders for the current user with optional filtering",
        "parameters": {
            "current_user_id": {"type": "string", "description": "Current user ID", "required": True},
            "status_filter": {"type": "string", "description": "Optional filter by status", "required": False},
            "limit": {"type": "integer", "description": "Maximum number of orders to return", "required": False, "default": 10}
        }
    }
]

# Tool function mapping
MCP_TOOL_FUNCTIONS = {
    "get_order_details": get_order_details,
    "request_order_cancellation": request_order_cancellation,
    "confirm_cancellation": confirm_cancellation,
    "list_user_orders": list_user_orders
}
