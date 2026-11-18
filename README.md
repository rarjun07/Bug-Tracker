# Bug Tracker

A Jira inspired issue tracker built with a FastAPI backend, PostgreSQL database, and React frontend. The project follows the mentor's 14 day outline, with each day's work reviewed and committed before the next day starts.

## Planned milestones

| Day | Scope |
| --- | --- |
| 1 | FastAPI project setup, PostgreSQL connection, SQLAlchemy base, and environment configuration |
| 2 | User model, JWT authentication, password hashing, and auth dependencies |
| 3 | Projects and team membership APIs |
| 4 | Issue models and CRUD APIs |
| 5 | React issue creation and listing |
| 6 | Responsive dashboard layout |
| 7 | API verification and refactoring |
| 8 | Drag and drop Kanban board |
| 9 | Issue comments and collaboration |
| 10 | Filtering and search |
| 11 | Edit/delete authorization and roles |
| 12 | Backend deployment |
| 13 | UI polish and documentation |
| 14 | Final verification and demo |

## Day 1: local setup

Requirements: Python 3.11+, Docker Compose, and Git.

1. Copy `.env.example` to `.env`.
2. Create and activate a virtual environment, then install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Start PostgreSQL:

   ```bash
   docker compose up -d db
   ```

4. From the repository root, run the API:

   ```bash
   uvicorn app.main:app --reload --app-dir backend
   ```

5. Open `http://127.0.0.1:8000/docs`. The health endpoints are `/health` and `/health/db`.

SQLAlchemy is configured for PostgreSQL and a shared declarative model base is ready. Alembic is included as a dependency; migration configuration and the first schema migration will be added with the first database models.

## Project layout

```text
backend/app/
  core/       settings
  db/         SQLAlchemy base, engine, and session dependency
  main.py     FastAPI app and health endpoints
compose.yaml  local PostgreSQL service
```
