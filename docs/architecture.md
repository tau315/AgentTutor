# Architecture

AgentTutor is designed as a normal tutoring platform first, with the AI agent acting as another client of the application services.

The agent does not directly access the database. It calls a small set of validated tools that wrap normal backend services.

```text
Next.js Frontend
  |
  v
FastAPI Backend
  |
  +-- Application Services
  |     Auth, Users, Tutors, Sessions, Scheduling, Messaging, Notifications
  |
  +-- AI Agent Service
        Tool registry, planning, approval checks, audit logging
```

## Design Principles

- Keep business logic in services, not routers.
- Keep database access in repositories, not services or routers.
- Keep agent actions bounded by explicit tools.
- Require confirmation before sensitive write actions.
- Log every agent action.
- Start with simple infrastructure and add complexity only when needed.

## Agent Safety Model

Read-only tools may run immediately when the authenticated user has permission.

Write tools must declare whether they require confirmation. Examples include booking, cancelling, rescheduling, updating profile data, and sending messages.

Every tool receives an `AgentContext` so authorization can be checked against the actual user, role, and request.

