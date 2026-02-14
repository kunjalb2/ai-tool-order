"""
Reset database - drop all tables and recreate with new schema
"""
from database import init_db, Base, engine, SessionLocal, User, Order

def reset_database():
    """Drop all tables and recreate them"""
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating tables with new schema...")
    init_db()
    print("Database reset complete!")

if __name__ == "__main__":
    reset_database()
