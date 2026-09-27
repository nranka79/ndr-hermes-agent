import os
import logging

from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .auth import router as auth_router
from .users import router as users_router
from .tokens import router as tokens_router
from .vocab import router as vocab_router
from .health import router as health_router
from .quota import router as quota_router
from .appstore_admin import router as appstore_router
from .tunnel_proxy import router as tunnel_router
from .key_admin import router as keys_router
from .dwd import router as dwd_router
from .device_auth import router as device_auth_router
from .jinja_env import env
from .openwebui import ensure_chat_defaults_in_background
from .vault_client import VaultClient, MANAGED_APPS

logger = logging.getLogger("admin-app")


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # /auth/device/* are the device-code API endpoints polled by CLI/
        # plugin clients -- no browser session involved, the device_code /
        # refresh_token itself is the credential.
        public_paths = {"/auth/login", "/auth/callback", "/health", "/static", "/quota/api", "/auth/device"}
        if any(request.url.path.startswith(p) for p in public_paths):
            return await call_next(request)

        if request.url.path.startswith("/device"):
            # The device approval page accepts EITHER a normal admin
            # session OR the lightweight device_user session set by the
            # "device:" branch in auth.py's callback (any known vault
            # identity, not admin-gated). Neither grants access to
            # anything beyond this one page -- device_auth.py itself
            # still checks the llm_gateway permission before approving
            # any device.
            if request.session.get("user") or request.session.get("device_user"):
                return await call_next(request)
            next_path = request.url.path
            if request.url.query:
                next_path += "?" + request.url.query
            import urllib.parse
            return RedirectResponse(url=f"/auth/login?next={urllib.parse.quote(next_path, safe='')}")

        user = request.session.get("user")
        if not user:
            next_path = request.url.path
            if request.url.query:
                next_path += "?" + request.url.query
            import urllib.parse
            return RedirectResponse(url=f"/auth/login?next={urllib.parse.quote(next_path, safe='')}")
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
        return HTMLResponse(env.get_template("dashboard.html").render(user=user))

    app.include_router(auth_router, prefix="/auth")
    app.include_router(users_router, prefix="/users")
    app.include_router(tokens_router, prefix="/tokens")
    app.include_router(vocab_router, prefix="/vocab")
    app.include_router(health_router, prefix="/health")
    app.include_router(quota_router)
    app.include_router(appstore_router)
    app.include_router(tunnel_router)
    app.include_router(keys_router)
    app.include_router(dwd_router)
    app.include_router(device_auth_router)

    static_dir = Path(__file__).parent / "static"

    @app.get("/static/{path:path}")
    async def static_files(path: str):
        file_path = static_dir / path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return HTMLResponse("Not found", status_code=404)

    app.state.vault = vault
    app.state.jinja_env = env
    app.state.hermes_home = os.environ.get("HERMES_HOME", "")

    # Open WebUI new-account defaults (active user, Hermes group) are applied
    # once at startup, so a fresh chat-data volume needs no manual setup.
    ensure_chat_defaults_in_background()

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Render a friendly error page instead of raw JSON for bad form input."""
        messages = []
        for err in exc.errors():
            loc = ".".join(str(x) for x in err.get("loc", []) if x not in ("body", "query"))
            messages.append(f"{loc or 'form'}: {err.get('msg', 'invalid')}")
        detail = "; ".join(messages)
        return HTMLResponse(
            env.get_template("error.html").render(
                user=request.session.get("user"),
                error=f"Invalid input — {detail}",
            ),
            status_code=422,
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return HTMLResponse(
            env.get_template("error.html").render(
                user=request.session.get("user"),
                error=str(exc.detail),
            ),
            status_code=exc.status_code,
        )

    return app
