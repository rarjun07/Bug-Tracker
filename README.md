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

## Run locally

You need Python 3.11 or newer, Node.js with npm, and Docker Compose.

1. Create the backend environment file and generate a private JWT key:

   ```bash
   cp .env.example .env
   openssl rand -hex 32
   ```

   Paste the generated value into `JWT_SECRET_KEY` in `.env`.
2. Start the local PostgreSQL database:

   ```bash
   docker compose up -d db
   ```
3. Install backend packages, apply migrations, and start FastAPI from the repository root:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   alembic -c backend/alembic.ini upgrade head
   uvicorn app.main:app --reload --app-dir backend
   ```
4. In a second terminal, start React:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

Open the frontend at `http://localhost:5173` and the API reference at `http://localhost:8000/docs`. Set `VITE_API_URL` in `frontend/.env` to change the frontend's API address; `FRONTEND_ORIGIN` in the root `.env` controls allowed browser origins and can contain comma-separated origins. Create the first project with `POST /projects` in the API reference after signing in; use its **Authorize** button with the access token from `POST /auth/token`.

## Features and project roles

- Project scoped issues with types, priorities, statuses, and team assignments.
- Search, filtering, pagination, Kanban status updates, and threaded issue discussion.
- Project roles:

  | Role | Issue access |
  | --- | --- |
  | Admin | Create, edit, comment, and delete issues; manage project members |
  | Developer | Create and edit issues, update status, and comment |
  | Viewer | Read issues and discussions |

Issue create, update, delete, and comment permissions are checked by the API as well as reflected in the interface.

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

Issues are scoped to a project and receive sequential keys such as `APP-1`. Issue routes support create, list, detail, update, and delete operations under `/projects/{project_id}/issues`. Issue fields include type (`bug`, `task`, `feature`), status (`todo`, `in_progress`, `done`), priority (`low`, `medium`, `high`, `urgent`), reporter, and optional assignee. Assignees must already belong to the project. Current role permissions are described under [Features and project roles](#features-and-project-roles). Apply the issue schema with `alembic -c backend/alembic.ini upgrade head`.

## Day 5: React issue workspace

The frontend lives in `frontend/`. Start it with `cd frontend && npm install && npm run dev`; it expects the FastAPI API at `http://localhost:8000` by default. Set `VITE_API_URL` in a frontend `.env` file to change that address. The backend allows the local Vite origin (`http://localhost:5173`) through CORS by default; change `FRONTEND_ORIGIN` in the backend `.env` when the frontend runs elsewhere.

The workspace supports account registration and sign-in, project selection, issue creation, and an issue list with live search. Create the first project from the backend Swagger docs at `http://localhost:8000/docs` after signing in; project creation UI is outside the Day 5 scope.

## Day 6: project dashboard and responsive layout

The `/dashboard` page summarizes issue status and priority, shows recently created issues, and lists the project team. Switch between Dashboard and Issues in the sidebar; the selected project is remembered in the browser. The sidebar collapses on smaller screens, issue tables scroll horizontally, and dashboard panels stack for mobile layouts.

## Day 7: API checks and refactoring

Install the development dependencies and run the API suite from the repository root:

```bash
pip install -r requirements-dev.txt
python -m pytest
```

The API tests use a temporary SQLite database and cover registration, login, project membership, issue CRUD, sequential issue keys, and membership boundaries. They do not need the local PostgreSQL container.

## Day 8: Kanban board

The Kanban view groups project issues by status. Admins and developers can drag cards or choose a status; viewers see the board in read-only mode.

## Day 9: issue discussion

Issue discussions support top-level comments and one level of threaded replies. Project members can read comments; admins and developers can post and reply.

## Day 10: search and filters

The Issues view supports server-side search by issue key, title, and description; filters by status, type, priority, and assignee; sort order; and paginated results. The Kanban view applies filters and shows up to 100 matching issues.

## Day 11: edit/delete authorization

The backend enforces role permissions for issue creation, updates, comments, and deletion. Admins and developers can create and update issues and comment; only admins can delete issues. Viewers can read issues and discussions.

## Day 12: deploy the backend to Railway

The root `Dockerfile` packages the FastAPI service. Railway detects it automatically when the repository is deployed as a service. The container listens on Railway's `PORT`, runs as a non-root user, and accepts both Railway's standard PostgreSQL URLs and the local `postgresql+psycopg://` URL.

1. In Railway, create a project from the `rarjun07/Bug-Tracker` GitHub repository and add a PostgreSQL service. If you name the database service something other than `Postgres`, use that service name in the variable reference below.
2. Add these variables to the backend service:

   | Variable | Value |
   | --- | --- |
   | `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |
   | `JWT_SECRET_KEY` | A new secret from `openssl rand -hex 32` |
   | `APP_ENV` | `production` |
   | `FRONTEND_ORIGIN` | The exact deployed frontend origin, such as `https://your-app.example` |

   Keep secrets in Railway variables; do not commit them to this repository. For local browser access while developing, `FRONTEND_ORIGIN` can contain comma-separated origins such as `https://your-app.example,http://localhost:5173`.
3. Set the backend service's pre-deploy command to `alembic -c backend/alembic.ini upgrade head`. Railway runs it before the new application starts; a failed migration stops that deployment.
4. Set the healthcheck path to `/health`, then generate a public domain in the service's Networking settings.
5. Open `https://<your-backend-domain>/health` and `/health/db`. Both should return `200`; `/health/db` also confirms the managed database connection. `/docs` serves the API reference.

Railway deployment references: [Dockerfiles](https://docs.railway.com/builds/dockerfiles), [pre-deploy commands](https://docs.railway.com/deployments/pre-deploy-command), [healthchecks](https://docs.railway.com/deployments/healthchecks), and [PostgreSQL](https://docs.railway.com/databases/postgresql).

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
Dockerfile   production FastAPI container
.env.example safe local backend configuration template
```
