"""
MCP Resources module for Kunjal Agents
Defines resources for read-only data access
"""
from typing import Dict
from sqlalchemy.orm import Session
import json
import logging

from database import SessionLocal, Order

logger = logging.getLogger(__name__)


async def get_user_orders_resource(user_id: str) -> str:
    """Get all orders for a user as a resource.

    URI Pattern: orders://{user_id}
    Example: orders://123

    Args:
        user_id: The user ID to fetch orders for

    Returns:
        JSON string containing user's orders
    """
    db = SessionLocal()
    try:
        orders = db.query(Order).filter(Order.user_id == int(user_id)).all()
        return json.dumps({
            "user_id": user_id,
            "orders": [
                {
                    "order_id": o.order_id,
                    "status": o.status,
                    "total": float(o.total),
                    "date": o.date.isoformat() if o.date else None
                }
                for o in orders
            ]
        }, indent=2)
    except Exception as e:
        logger.error(f"Error fetching user orders resource: {e}")
        return json.dumps({"error": str(e)}, indent=2)
    finally:
        db.close()


async def get_order_resource(order_id: str) -> str:
    """Get detailed order information as a resource.

    URI Pattern: order://{order_id}
    Example: order://ORD-001

    Args:
        order_id: The order ID to fetch details for

    Returns:
        JSON string containing order details
    """
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            return json.dumps({"error": "Order not found"}, indent=2)

        return json.dumps({
            "order_id": order.order_id,
            "customer_name": order.customer_name,
            "status": order.status,
            "items": order.items,
            "total": float(order.total),
            "date": order.date.isoformat() if order.date else None
        }, indent=2)
    except Exception as e:
        logger.error(f"Error fetching order resource: {e}")
        return json.dumps({"error": str(e)}, indent=2)
    finally:
        db.close()


# Resource metadata for listing available resources
MCP_RESOURCES_METADATA = [
    {
        "uri": "orders://{user_id}",
        "name": "User Orders",
        "description": "All orders for a specific user",
        "mime_type": "application/json"
    },
    {
        "uri": "order://{order_id}",
        "name": "Order Details",
        "description": "Detailed information about a specific order",
        "mime_type": "application/json"
    }
]

# Resource function mapping
MCP_RESOURCE_FUNCTIONS = {
    "orders://": get_user_orders_resource,
    "order://": get_order_resource
}
