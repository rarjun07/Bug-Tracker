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

SQLAlchemy is configured for PostgreSQL and the shared declarative base is in place. Alembic configuration and the initial user schema migration were added with Day 2.

## Day 2: accounts and authentication

Before starting the API, set a private JWT signing key in `.env`. Generate one with:

```bash
openssl rand -hex 32
```

Paste the output as `JWT_SECRET_KEY` in `.env`. Then apply the user schema migration:

```bash
alembic -c backend/alembic.ini upgrade head
```

The authentication routes are `POST /auth/register`, `POST /auth/token`, and `GET /auth/me`. Registration accepts JSON; token login accepts OAuth2 form fields (`username` may contain a username or email, plus `password`). Protected routes can use the `get_current_user` dependency. Passwords are stored as Argon2 hashes, and only a user's public fields are returned by the API.

## Day 3: projects and teams

Create a project with `POST /projects` using a name, uppercase project key, and optional description. The creator is automatically added as a project admin. `GET /projects` lists the signed-in user's projects; project details and team routes require membership. Project admins can list, add, update the role of, and remove team members using `/projects/{project_id}/members`. Roles are `admin`, `developer`, and `viewer`, and every project must retain at least one admin.

Apply the project and membership schema after pulling Day 3:

```bash
alembic -c backend/alembic.ini upgrade head
```

## Day 4: issue tracking

Issues are scoped to a project and receive sequential keys such as `APP-1`. Members can create, list, view, update, and delete issues with `POST`, `GET`, `GET`, `PATCH`, and `DELETE` under `/projects/{project_id}/issues`. Issue fields include type (`bug`, `task`, `feature`), status (`todo`, `in_progress`, `done`), priority (`low`, `medium`, `high`, `urgent`), reporter, and optional assignee. Assignees must already belong to the project. Apply the new issue schema with `alembic -c backend/alembic.ini upgrade head`.

## Day 5: React issue workspace

The frontend lives in `frontend/`. Start it with `cd frontend && npm install && npm run dev`; it expects the FastAPI API at `http://localhost:8000` by default. Set `VITE_API_URL` in a frontend `.env` file to change that address. The backend allows the local Vite origin (`http://localhost:5173`) through CORS by default; change `FRONTEND_ORIGIN` in the backend `.env` when the frontend runs elsewhere.

The workspace supports account registration and sign-in, project selection, issue creation, and an issue list with live search. Create the first project from the backend Swagger docs at `http://localhost:8000/docs` after signing in; project creation UI is outside the Day 5 scope.

## Project layout

```text
backend/app/
  core/       settings
  db/         SQLAlchemy base, engine, and session dependency
  models/     users, projects, memberships, and issues
  schemas/    request and response models
  api/        authentication, project, and issue routes
  main.py     FastAPI app and health endpoints
backend/alembic/ database migration history
frontend/     React + TypeScript + Vite issue workspace
compose.yaml  local PostgreSQL service
```
