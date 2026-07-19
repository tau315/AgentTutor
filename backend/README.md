# Backend

FastAPI backend for AgentTutor.

The backend is organized by domain. Each domain should eventually own its schemas, service layer, repository layer, and router.

Business logic belongs in services. Routers should stay thin. Agent tools should call services instead of touching database models directly.

## Request pipeline

`router -> service -> repository -> SQLAlchemy async session -> PostgreSQL`

Authentication-protected requests first pass through the JWT current-user dependency and, when needed, a role dependency. Every response includes an `X-Request-ID` that is also attached to request logs.

Scheduling stores recurring availability in a tutor's local time zone and stores actual sessions as UTC instants. PostgreSQL exclusion constraints are the final protection against student or tutor double booking.

Session changes create database notifications and enqueue delivery/reminder jobs in Redis. Run the worker with `python -m app.workers.main`.
