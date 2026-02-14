"""
Database tool functions for order operations
"""
from typing import Optional, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.orm.attributes import flag_modified
import random
import string

from database import Order


def get_order_status(db: Session, order_id: str, current_user: Optional[Dict[str, str]] = None) -> dict:
    """Get order status by order ID from database"""
    try:
        # Query order with user join
        order = db.query(Order).options(
            joinedload(Order.user)
        ).filter(Order.order_id == order_id).first()

        if not order:
            return {"success": False, "error": "Order not found"}

        # Check if order belongs to current user if provided
        if current_user and current_user.get("id"):
            user_id = current_user.get("id")
            if order.user_id != user_id:
                return {"success": False, "error": "Order not found"}

        # Build response data
        order_data = {
            "order_id": order.order_id,
            "customer": order.customer_name,
            "status": order.status,
            "items": order.items,
            "total": order.total,
            "date": order.date.strftime("%Y-%m-%d") if order.date else None,
            "user_email": order.user.email if order.user else None,
            "user_name": order.user.name if order.user else None,
        }

        print(f"DEBUG: Retrieved order {order_id} for user {order.user_id}")
        return {"success": True, "order": order_data}

    except Exception as e:
        print(f"Error fetching order status: {e}")
        return {"success": False, "error": "Database error"}


def generate_cancellation_code(db: Session, order_id: str, current_user: Optional[Dict[str, str]] = None) -> dict:
    """Generate verification code for cancellation from database"""
    try:
        # Query order with user join
        order = db.query(Order).options(
            joinedload(Order.user)
        ).filter(Order.order_id == order_id).first()

        if not order:
            return {"success": False, "error": "Order not found"}

        # Authorization check: users can only access their own orders
        if current_user and current_user.get("id"):
            user_id = current_user.get("id")
            if order.user_id != user_id:
                return {"success": False, "error": "Order not found"}

        # Check if order is already cancelled
        if order.status == "cancelled":
            return {"success": False, "error": "This order has already been cancelled and cannot be cancelled again"}

        # Check if order can be cancelled (only processing or shipped orders can be cancelled)
        cancellable_statuses = ["processing", "shipped"]
        if order.status not in cancellable_statuses:
            return {"success": False, "error": f"This order cannot be cancelled because its status is '{order.status}'. Only orders with status 'processing' or 'shipped' can be cancelled"}

        # Get user email for sending email
        user_email = order.user.email if order.user else None
        user_name = order.user.name if order.user else order.customer_name

        # Generate verification code
        code = "".join(random.choices(string.digits, k=6))

        # Initialize verification_codes list if None
        if order.verification_codes is None:
            order.verification_codes = []

        # Add code to order's verification_codes
        order.verification_codes.append(code)

        # Flag the JSON column as modified (required for SQLAlchemy JSON columns)
        flag_modified(order, "verification_codes")

        db.commit()
        db.refresh(order)

        print(f"DEBUG: Stored verification code {code} in DB for order {order_id}, verification_codes now: {order.verification_codes}")

        # Send verification email
        if user_email:
            from database import send_verification_email
            send_verification_email(order_id, code, user_email, user_name)

        print(f"DEBUG: Generated verification code for order {order_id}")

        return {
            "success": True,
            "message": "Verification code generated",
            "code": code,
            "order_id": order_id,
            "requires_approval": True,
            "user_email": user_email,
            "user_name": user_name,
            "customer": order.customer_name,
        }

    except Exception as e:
        print(f"Error generating cancellation code: {e}")
        return {"success": False, "error": "Database error"}


def cancel_order_with_verification(db: Session, order_id: str, verification_code: str, current_user: Optional[Dict[str, str]] = None) -> dict:
    """Cancel order with verification code from database"""
    try:
        # Query order with user join
        order = db.query(Order).options(
            joinedload(Order.user)
        ).filter(Order.order_id == order_id).first()

        if not order:
            return {"success": False, "error": "Order not found"}

        # Authorization check: users can only access their own orders
        if current_user and current_user.get("id"):
            user_id = current_user.get("id")
            if order.user_id != user_id:
                return {"success": False, "error": "Order not found"}
        # Query order with user join
        order = db.query(Order).options(
            joinedload(Order.user)
        ).filter(Order.order_id == order_id).first()

        # Check if order belongs to current user if provided
        if current_user and current_user.get("id"):
            user_id = current_user.get("id")
            if order.user_id != user_id:
                return {"success": False, "error": "Order not found"}

        # Check verification code
        print(f"DEBUG: Checking verification code '{verification_code}' against codes in DB: {order.verification_codes}")
        if not order.verification_codes or verification_code not in order.verification_codes:
            return {"success": False, "error": "Invalid verification code"}

        # Update order status
        order.status = "cancelled"

        # Remove used verification code
        order.verification_codes.remove(verification_code)

        # Flag the JSON column as modified (required for SQLAlchemy JSON columns)
        flag_modified(order, "verification_codes")

        db.commit()

        user_name = order.user.name if order.user else order.customer_name
        user_email = order.user.email if order.user else None

        print(f"DEBUG: Cancelled order {order_id} with verification code")

        return {
            "success": True,
            "message": f"Order {order_id} cancelled successfully",
            "refund_amount": order.total,
            "user_email": user_email,
            "user_name": user_name,
        }

    except Exception as e:
        print(f"Error cancelling order: {e}")
        return {"success": False, "error": "Database error"}
