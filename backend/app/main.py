from fastapi import FastAPI

from app.agent.router import router as agent_router
from app.auth.router import router as auth_router
from app.health.router import router as health_router
from app.sessions.router import router as sessions_router
from app.tutors.router import router as tutors_router
from app.users.router import router as users_router
from fastapi import Request
from fastapi.responses import JSONResponse
from uuid import uuid4
from app.core.errors import AppError


def create_app() -> FastAPI:
    app = FastAPI(title="AgentTutor API")
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )
    
    @app.middleware("http")
    async def add_request_id(request, call_next):
        request_id = str(uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(users_router, prefix="/users", tags=["users"])
    app.include_router(tutors_router, prefix="/tutors", tags=["tutors"])
    app.include_router(sessions_router, prefix="/sessions", tags=["sessions"])
    app.include_router(agent_router, prefix="/agent", tags=["agent"])

    return app


app = create_app()

