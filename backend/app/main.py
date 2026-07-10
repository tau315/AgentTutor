from fastapi import FastAPI

from app.agent.router import router as agent_router
from app.auth.router import router as auth_router
from app.health.router import router as health_router
from app.sessions.router import router as sessions_router
from app.tutors.router import router as tutors_router
from app.users.router import router as users_router


def create_app() -> FastAPI:
    app = FastAPI(title="AgentTutor API")

    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(users_router, prefix="/users", tags=["users"])
    app.include_router(tutors_router, prefix="/tutors", tags=["tutors"])
    app.include_router(sessions_router, prefix="/sessions", tags=["sessions"])
    app.include_router(agent_router, prefix="/agent", tags=["agent"])

    return app


app = create_app()

