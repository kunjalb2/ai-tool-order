---
name: database
description: "Manage PostgreSQL database operations for Kunjal Agents - seed, reset, init, or check status"
color: blue
---

# Database Management Skill

You manage the PostgreSQL database for Kunjal Agents project. When invoked with a command, execute the appropriate database operation.

## Commands

- `seed` - Run seed script to populate database with sample users and orders
- `reset` - Drop all tables and recreate them (fresh database)
- `status` - Check if database is accessible
- `init` - Initialize database tables

## Implementation

Always run commands from the server directory:

```bash
cd server
```

Then execute based on command:
- **seed**: `python seed_db.py`
- **reset**: `python reset_db.py`
- **init**: Database tables are auto-created on startup, just confirm connection
- **status**: Test database connection using DATABASE_URL from .env

## Context

- Database: PostgreSQL with SQLAlchemy ORM
- Models: User (users) and Order (orders) tables
- Connection: DATABASE_URL environment variable
- Scripts location: server/ directory
