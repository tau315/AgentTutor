# AgentTutor

AgentTutor is a tutoring platform where students, tutors, and administrators can use traditional app workflows or ask an integrated AI agent to complete platform tasks.

This repository is currently a scaffold. It defines the project shape, module boundaries, and contracts without implementing business logic.

## Stack

- Frontend: Next.js, React, TypeScript, Tailwind CSS
- Backend: FastAPI, Python
- Database: PostgreSQL
- Cache and jobs: Redis
- AI: LangGraph-compatible agent service with bounded tools
- Vector search: pgvector first, external vector database later if needed

## Project Layout

```text
frontend/   Next.js application shell
backend/    FastAPI application shell and domain modules
infra/      Docker Compose and infrastructure placeholders
docs/       Architecture notes
```

## Development Status

Nothing is fully implemented yet. The codebase is intentionally structured around placeholders so the platform can be built feature by feature without changing the architecture.

