"""
Database module for PostgreSQL integration with SQLAlchemy.
"""

from sqlalchemy import create_engine, Column, String, Float, DateTime, JSON, ForeignKey, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime
from typing import Optional
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

# Database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/kunjal_agents")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship with orders
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")


class Order(Base):
    """Order model"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, nullable=False, index=True)  # e.g., "ORD-001"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    customer_name = Column(String, nullable=False)  # Derived from user relationship
    status = Column(String, nullable=False)  # processing, shipped, cancelled, etc.
    items = Column(JSON, nullable=False)  # List of item names
    total = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)
    verification_codes = Column(JSON, default=list)  # List of generated verification codes
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with user
    user = relationship("User", back_populates="orders")


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# Email Sending Functions
# ============================================================================

def send_verification_email(order_id: str, verification_code: str, user_email: str, user_name: str) -> bool:
    """Send verification code email to user using Gmail App Password"""
    try:
        # Get email configuration from environment
        gmail_email = os.getenv("GMAIL_EMAIL")
        gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")

        if not gmail_email or not gmail_app_password:
            print("Error: GMAIL_EMAIL and GMAIL_APP_PASSWORD must be set in environment")
            return False

        # Create email message
        message = MIMEMultipart()
        message['From'] = gmail_email
        message['To'] = user_email
        message['Subject'] = f"Order Cancellation Verification - {order_id}"

        body = f"""Hello {user_name},

Your verification code for order {order_id} is: {verification_code}

Please use this code to confirm the cancellation.

If you did not request this cancellation, please ignore this email.

Best regards,
Customer Support Team"""

        message.attach(MIMEText(body, 'plain'))

        # Send email using Gmail SMTP
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(gmail_email, gmail_app_password)
        server.send_message(message)
        server.quit()

        print(f"Email sent successfully to {user_email} for order {order_id}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def get_email_for_user(db: Session, user_id: int) -> Optional[str]:
    """Get email address for a user ID"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        return user.email if user else None
    except Exception as e:
        print(f"Error fetching user email: {e}")
        return None


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
