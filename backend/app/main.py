from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.agent.router import router as agent_router
from app.admin.router import router as admin_router
from app.analytics.router import router as analytics_router
from app.audit.router import router as audit_router
from app.auth.router import router as auth_router
from app.health.router import router as health_router
from app.messaging.router import router as messaging_router
from app.notifications.router import router as notifications_router
from app.scheduling.router import router as scheduling_router
from app.sessions.router import router as sessions_router
from app.tutors.router import router as tutors_router
from app.users.router import router as users_router
from app.core.config import settings
from app.core.errors import AppError
from app.audit.service import AuditService
from app.core.database import AsyncSessionLocal
from app.core.logging import logger, request_id_context


def create_app() -> FastAPI:
    app = FastAPI(title="AgentTutor API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "unknown")
        logger.exception("Unhandled request error path=%s", request.url.path)
        try:
            async with AsyncSessionLocal() as db:
                await AuditService(db).record(
                    None,
                    "system.error",
                    "request",
                    request_id,
                    {"path": request.url.path, "error_type": type(exc).__name__},
                )
        except Exception:
            logger.exception("Could not persist system error audit record")
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected server error occurred", "request_id": request_id},
            headers={"X-Request-ID": request_id},
        )
    
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request.state.request_id = request_id
        token = request_id_context.set(request_id)
        started_at = perf_counter()

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            logger.info(
                "%s %s completed status=%s duration_ms=%.2f",
                request.method,
                request.url.path,
                response.status_code,
                (perf_counter() - started_at) * 1000,
            )
            return response
        finally:
            request_id_context.reset(token)

    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(users_router, prefix="/users", tags=["users"])
    app.include_router(tutors_router, prefix="/tutors", tags=["tutors"])
    app.include_router(sessions_router, prefix="/sessions", tags=["sessions"])
    app.include_router(agent_router, prefix="/agent", tags=["agent"])
    app.include_router(scheduling_router, prefix="/scheduling", tags=["scheduling"])
    app.include_router(messaging_router, prefix="/messages", tags=["messages"])
    app.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
    app.include_router(admin_router, prefix="/admin", tags=["admin"])
    app.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
    app.include_router(audit_router, prefix="/audit-logs", tags=["audit"])

    return app


app = create_app()
