import os
import logging

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .auth import router as auth_router
from .users import router as users_router
from .tokens import router as tokens_router
from .health import router as health_router
from .jinja_env import env
from .vault_client import VaultClient

logger = logging.getLogger("admin-app")


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        public_paths = {"/auth/login", "/auth/callback", "/health", "/static"}
        if any(request.url.path.startswith(p) for p in public_paths):
            return await call_next(request)
        user = request.session.get("user")
        if not user:
            return RedirectResponse(url="/auth/login")
        return await call_next(request)


def create_app() -> FastAPI:
    app = FastAPI(title="Hermes Admin Panel", version="0.1.0")

    vault = VaultClient()

    session_secret = os.environ.get("SESSION_SECRET", "")
    if not session_secret:
        logger.warning("SESSION_SECRET not set — using ephemeral key (sessions lost on restart)")
        session_secret = os.urandom(32).hex()

    # Order matters: SessionMiddleware must be outermost so session loads before auth check
    app.add_middleware(AuthMiddleware)
    app.add_middleware(SessionMiddleware, secret_key=session_secret, max_age=86400)

    @app.get("/")
    async def root(request: Request):
        user = request.session.get("user")
        return env.get_template("dashboard.html").render(user=user)

    app.include_router(auth_router, prefix="/auth")
    app.include_router(users_router, prefix="/users")
    app.include_router(tokens_router, prefix="/tokens")
    app.include_router(health_router, prefix="/health")

    app.state.vault = vault
    app.state.jinja_env = env

    return app
