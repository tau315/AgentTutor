# Backend

FastAPI backend scaffold for AgentTutor.

The backend is organized by domain. Each domain should eventually own its schemas, service layer, repository layer, and router.

Business logic belongs in services. Routers should stay thin. Agent tools should call services instead of touching database models directly.

