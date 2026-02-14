---
name: docker
description: "Manage Docker containers for Kunjal Agents - up, down, rebuild, logs, clean, or exec commands"
color: green
---

# Docker Management Skill

You manage Docker containers for Kunjal Agents using docker-compose. When invoked with a command, execute the appropriate docker-compose operation.

## Commands

- `up` - Start all services (postgres, backend, frontend)
- `down` - Stop all services
- `rebuild <service>` - Rebuild specific service (backend/frontend/postgres)
- `logs <service>` - Show and follow logs for a service
- `clean` - Stop all services and remove volumes (fresh database)
- `exec <service> <command>` - Execute command inside a container

## Implementation

Always run docker-compose from the project root directory.

Commands:
- **up**: `docker-compose up -d --build`
- **down**: `docker-compose down`
- **rebuild**: `docker-compose up -d --build <service>`
- **logs**: `docker-compose logs -f <service>`
- **clean**: `docker-compose down -v`
- **exec**: `docker-compose exec <service> <command>`

## Common Examples

- `docker exec backend env` - Check backend environment
- `docker exec postgres psql -U kunjal_user -d kunjal_agents` - Connect to PostgreSQL
- `docker logs backend` - Follow backend logs

## Context

Services in docker-compose.yml:
- **postgres**: PostgreSQL 15 on internal port 5432
- **backend**: FastAPI on port 8000
- **frontend**: Vite dev server on port 5173

Frontend connects to backend via `http://backend:8000` when running in Docker (not localhost:8000).
