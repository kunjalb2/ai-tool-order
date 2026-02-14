"""
Database seeding script for Kunjal Agents.
"""

import sys
from datetime import datetime
from sqlalchemy.orm import Session

sys.path.insert(0, ".")
from database import engine, SessionLocal, User, Order, init_db
from services.auth import get_password_hash


def seed_database():
    """Seed database with sample users and orders"""
    print("Starting database seeding...")
    init_db()

    session = SessionLocal()

    try:
        print("Clearing existing data...")
        session.query(Order).delete()
        session.query(User).delete()
        session.commit()

        print("Creating users...")
        users_data = [
            {
                "name": "Kunjal Bhavsar",
                "email": "bhavsarkunjal228@gmail.com",
                "password": "Admin@123",
            },
            {
                "name": "Indian Wizard",
                "email": "indianwizard2019@gmail.com",
                "password": "Admin@123",
            },
        ]

        users = []
        for user_data in users_data:
            password_hash = get_password_hash(user_data.pop("password"))
            user = User(**user_data, password_hash=password_hash)
            session.add(user)
            session.flush()
            users.append(user)

        session.commit()
        print(f"Created {len(users)} users")

        for user in users:
            session.refresh(user)

        print("Creating orders...")
        base_time = 1708000000

        user_map = {u.email: u for u in users}

        order_templates = [
            # Orders for bhavsarkunjal228@gmail.com
            {
                "order_id": "ORD-001",
                "user_id": user_map["bhavsarkunjal228@gmail.com"].id,
                "customer_name": user_map["bhavsarkunjal228@gmail.com"].name,
                "status": "processing",
                "items": ["Laptop"],
                "total": 1299.99,
                "date": datetime.fromtimestamp(base_time),
            },
            {
                "order_id": "ORD-002",
                "user_id": user_map["bhavsarkunjal228@gmail.com"].id,
                "customer_name": user_map["bhavsarkunjal228@gmail.com"].name,
                "status": "shipped",
                "items": ["Mouse"],
                "total": 49.99,
                "date": datetime.fromtimestamp(base_time + 86400),
            },
            {
                "order_id": "ORD-003",
                "user_id": user_map["bhavsarkunjal228@gmail.com"].id,
                "customer_name": user_map["bhavsarkunjal228@gmail.com"].name,
                "status": "delivered",
                "items": ["Keyboard"],
                "total": 89.99,
                "date": datetime.fromtimestamp(base_time + 86400 * 2),
            },
            {
                "order_id": "ORD-004",
                "user_id": user_map["bhavsarkunjal228@gmail.com"].id,
                "customer_name": user_map["bhavsarkunjal228@gmail.com"].name,
                "status": "processing",
                "items": ["Monitor"],
                "total": 499.99,
                "date": datetime.fromtimestamp(base_time + 86400 * 3),
            },
            # Orders for indianwizard2019@gmail.com
            {
                "order_id": "ORD-005",
                "user_id": user_map["indianwizard2019@gmail.com"].id,
                "customer_name": user_map["indianwizard2019@gmail.com"].name,
                "status": "processing",
                "items": ["Tablet"],
                "total": 399.99,
                "date": datetime.fromtimestamp(base_time + 86400 * 4),
            },
            {
                "order_id": "ORD-006",
                "user_id": user_map["indianwizard2019@gmail.com"].id,
                "customer_name": user_map["indianwizard2019@gmail.com"].name,
                "status": "shipped",
                "items": ["USB-C Hub"],
                "total": 79.99,
                "date": datetime.fromtimestamp(base_time + 86400 * 5),
            },
            {
                "order_id": "ORD-007",
                "user_id": user_map["indianwizard2019@gmail.com"].id,
                "customer_name": user_map["indianwizard2019@gmail.com"].name,
                "status": "delivered",
                "items": ["Headphones"],
                "total": 199.99,
                "date": datetime.fromtimestamp(base_time + 86400 * 6),
            },
            {
                "order_id": "ORD-008",
                "user_id": user_map["indianwizard2019@gmail.com"].id,
                "customer_name": user_map["indianwizard2019@gmail.com"].name,
                "status": "processing",
                "items": ["Webcam"],
                "total": 149.99,
                "date": datetime.fromtimestamp(base_time + 86400 * 7),
            },
        ]

        orders = []
        for order_data in order_templates:
            order = Order(**order_data)
            session.add(order)
            orders.append(order)

        session.commit()
        print(f"Created {len(orders)} orders")

        for user in users:
            order_count = session.query(Order).filter_by(user_id=user.id).count()
            print(f"  {user.name}: {order_count} orders")

        print("\nDatabase seeded successfully!")

    except Exception as e:
        print(f"Error seeding database: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()
