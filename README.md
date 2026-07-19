# AgentTutor

AgentTutor is a tutoring marketplace and scheduling platform with a permission-aware AI assistant. Students and tutors can use normal screens or ask the assistant to search, read, and propose actions; every data-changing AI action waits for explicit confirmation.

Payments are intentionally outside this project.

## Project Status

AgentTutor is a complete, locally runnable MVP for the core tutoring workflows described below. It is suitable for development, learning, demonstrations, and continued product work, but it should not yet be treated as a finished commercial service handling real users without additional security testing and deployment work.

The following larger production features are not implemented yet:

- OAuth, password reset, email verification, and multi-factor authentication
- Real email delivery and recurring tutoring sessions
- Streaming AI responses and file uploads for homework
- Model-generated embeddings and conversation summaries
- Production rate limiting and deeper prompt-injection defenses
- Full browser, accessibility, load, penetration, and disaster-recovery testing
- Cloud hosting, DNS, HTTPS, automated backups, and external monitoring

The current embeddings are deterministic and local, and the default agent planner is rule-based. These choices keep the complete application usable without paid services while preserving interfaces that can be upgraded later.

## What Is Implemented

- Student, tutor, and admin JWT accounts with role-protected APIs
- Tutor profiles, subjects, expertise, rates, visibility, search, and sorting
- Weekly tutor availability, blocked times, timezone-aware sessions, and database-enforced conflict prevention
- Session requests, decisions, cancellation, rescheduling, history, messaging, reports, and in-app notifications
- Redis reminder and notification jobs with a separate worker process
- Stored AI conversations, read tools, confirmed write tools, error recovery, and complete agent audit logs
- pgvector-backed platform documentation, homework retrieval, and user-controlled preference memory
- Admin user/session/report management plus request, agent failure, and latency observability
- Next.js interfaces for every implemented workflow
- Alembic migrations, automated tests, GitHub Actions, and deployable Docker images

## Architecture

```text
Browser (Next.js)
       |
       | JSON + JWT
       v
FastAPI routers -> domain services -> repositories -> PostgreSQL + pgvector
                         |
                         +-> notification jobs -> Redis -> worker

AI chat -> planner -> finite tool registry -> domain services
                    |
                    +-> read tool: execute now
                    +-> write tool: pending_actions -> user confirms -> execute
```

The frontend never connects to PostgreSQL or Redis. It calls FastAPI. Routers validate HTTP input, services enforce business rules, repositories perform database queries, and PostgreSQL stores durable state. Redis only holds short-lived background jobs.

The AI tools call the same services as the normal API routes. They do not receive unrestricted database access. Each tool gets the authenticated `CurrentUser`, declares allowed roles, and returns only information that the service permits that user to see.

## Main Pipelines

### Authentication

```text
POST /auth/login -> verify password -> sign JWT -> browser stores token
request -> Authorization: Bearer <JWT> -> load active user -> role dependency -> endpoint
```

### Scheduling

```text
student request -> validate tutor availability -> check blocked periods
-> insert session -> PostgreSQL exclusion constraints reject overlaps
-> notification row -> Redis delivery job -> worker
```

Both tutor and student overlap constraints live in PostgreSQL, so two simultaneous requests cannot bypass conflict detection.

### Safe AI Action

```text
POST /agent/chat -> store user message -> planner chooses one registered tool
-> permission check -> store pending action -> return confirmation card
-> POST /agent/actions/{id}/confirm -> recheck owner, expiry, and role
-> call domain service -> store result + audit duration/status
```

Read tools execute immediately. Write tools expire after 15 minutes and never execute from the first chat request.

### RAG And Memory

```text
document text -> deterministic 384-value embedding -> pgvector column
question -> query embedding -> cosine-distance search -> authorized documents -> answer
```

Platform documents are global and admin-managed. Homework is private to its owner. Memories belong to one user, exclude obvious sensitive text from automatic storage, and can be viewed or deleted at `/memory`.

## Run Everything With Docker

Install and open Docker Desktop, then run from the repository root:

```powershell
docker compose -f infra/docker-compose.yml up --build
```

This starts five containers:

- `postgres`: PostgreSQL with pgvector
- `redis`: background job queue
- `api`: migrations followed by FastAPI on `http://localhost:8000`
- `worker`: reminder and notification processing
- `frontend`: Next.js on `http://localhost:3000`

Swagger API documentation is at `http://localhost:8000/docs`. Stop everything with:

```powershell
docker compose -f infra/docker-compose.yml down
```

Named PostgreSQL data remains after `down`. Add `-v` only when you deliberately want to delete local database data.

## Run Services Separately

Infrastructure:

```powershell
docker compose -f infra/docker-compose.yml up -d postgres redis
```

Backend, from `backend`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Worker, from a second activated backend terminal:

```powershell
python -m app.workers.main
```

Frontend, from `frontend`:

```powershell
npm install
npm run dev
```

## Account Creation

Students and tutors use `/auth` or `POST /auth/signup`. Admin signup is deliberately unavailable publicly. Create a new admin from `backend`:

```powershell
python -m scripts.create_admin --email admin@example.com
```

To promote an existing user without changing their password:

```powershell
python -m scripts.create_admin --email existing@example.com --keep-password
```

## AI Provider

The default `LLM_PROVIDER=stub` uses a deterministic planner, so the complete safety and tool pipeline works without an API key or paid model. It recognizes the supported task shapes and asks for IDs or exact timezone-aware times when necessary.

### Current Ollama Installation

This development computer currently has:

```text
Ollama version: 0.32.0
Installed model: llama3.2:latest
Model size: 2.0 GB
```

You can check this again at any time:

```powershell
ollama --version
ollama list
```

There is currently no `backend/.env` file, so FastAPI uses the defaults from `backend/app/core/config.py`. That means it still uses `LLM_PROVIDER=stub` until you explicitly configure Ollama.

### Use Ollama With A Separately Run Backend

Create `backend/.env` with:

```env
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.2:latest
```

Restart FastAPI after changing `.env`. You can confirm that Ollama itself responds with:

```powershell
ollama run llama3.2:latest "Say hello in one sentence."
```

### Use Ollama With Docker Compose

When the API runs inside Docker, `localhost` would refer to the API container rather than your Windows computer. The Compose file therefore uses:

```env
LLM_PROVIDER=ollama
LLM_BASE_URL=http://host.docker.internal:11434
LLM_MODEL=llama3.2:latest
```

In PowerShell, start the stack with those values like this:

```powershell
$env:LLM_PROVIDER = "ollama"
$env:LLM_MODEL = "llama3.2:latest"
docker compose -f infra/docker-compose.yml up --build
```

The Compose file already supplies the `host.docker.internal` URL. If Ollama is unavailable or model planning fails, the agent falls back to the deterministic planner. The finite tool registry, role checks, confirmation system, and service boundaries remain the same with either planner.

## Verification

```powershell
cd backend
pytest -q
ruff check app tests scripts
alembic check

cd ..\frontend
npm run typecheck
npm run build
```

GitHub Actions runs these checks and builds both Docker images on every push and pull request.

## Production Deployment

Deploy the frontend image to a web host, the API and worker images to a container host, and use managed PostgreSQL with pgvector plus managed Redis. Configure `APP_ENV=production`, `DATABASE_URL`, `REDIS_URL`, `FRONTEND_URL`, and a strong random `JWT_SECRET` through the host's secret manager.

The app refuses to start in production with the development JWT secret. The API should run migrations as a release step before new containers receive traffic. Runtime logs should be shipped to the hosting provider's log service; durable request failures and all agent actions are also available in the admin audit dashboard.

Actual cloud resources, DNS, TLS certificates, and provider secrets are external account operations and are not created by this repository.
