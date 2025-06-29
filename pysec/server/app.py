"""Web server for pysec with admin dashboard."""

from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import (
    Depends,
    FastAPI,
    Form,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

from pysec.config import get_or_create_server_config
from pysec.server.auth import (
    create_access_token,
    generate_token,
    get_password_hash,
    verify_password,
    verify_token,
)
from pysec.server.database import Client, DatabaseManager


class AuditLogRequest(BaseModel):
    """Request model for audit log submission."""

    timestamp: datetime
    event: str


class PackageListRequest(BaseModel):
    """Request model for package list submission."""

    packages: list[dict[str, str]]


class ClientCreateRequest(BaseModel):
    """Request model for client creation."""

    name: str


class SecurityInfoRequest(BaseModel):
    """Request model for security information submission."""

    disk_encrypted: bool | None = None
    screen_lock_timeout: int | None = None
    auto_updates_enabled: bool | None = None
    os_checker_available: bool = False
    error: str | None = None


class JSONResponseMiddleware(BaseHTTPMiddleware):
    """Middleware to ensure API endpoints return JSON responses."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process request and ensure JSON responses for API endpoints."""
        response = await call_next(request)

        # Only apply to API endpoints (not web UI)
        # If response is not already JSON and status code indicates error
        if (
            request.url.path.startswith("/api/")
            and response.status_code >= status.HTTP_400_BAD_REQUEST
            and response.headers.get(
                "content-type",
                "",
            ).startswith("text/html")
        ):
            # Convert to JSON error response
            return JSONResponse(
                status_code=response.status_code,
                content={
                    "error": "Internal server error",
                    "detail": "API endpoint error",
                },
            )

        return response


@lru_cache(maxsize=1)
def get_admin_password_hash() -> str:
    """Get the admin password hash, cached for performance."""
    config = get_or_create_server_config()
    return get_password_hash(config.admin_password)


app = FastAPI(title="PySec Server", description="Security monitoring server")
security = HTTPBearer(auto_error=False)  # Don't auto-error so we can check cookies

# Add middleware for JSON responses on API endpoints
app.add_middleware(JSONResponseMiddleware)


# Custom exception handler for API endpoints
@app.exception_handler(HTTPException)
async def api_http_exception_handler(request: Request, exc: HTTPException) -> Response:
    """Return custom JSON exception."""
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail, "status_code": exc.status_code},
        )
    # For non-API endpoints, use default handler
    return await http_exception_handler(request, exc)


@app.exception_handler(500)
async def internal_server_error_handler(
    request: Request,
    _exc: Exception,
) -> JSONResponse:
    """Handle internal server errors with JSON for API endpoints."""
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "status_code": 500},
        )
    # For web UI, return HTML error page
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )


# Initialize database
db = DatabaseManager()

# Templates directory
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))


def get_current_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Get current admin user from JWT token."""
    token = credentials.credentials
    username = verify_token(token)
    if username != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return username


def get_current_admin_user_from_cookie_or_header(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    """Get current admin user from cookie or Authorization header."""
    token = None

    # First try to get token from Authorization header
    if credentials:
        token = credentials.credentials
    else:
        # If no Authorization header, try to get from cookie
        cookie_value = request.cookies.get("access_token")
        if cookie_value and cookie_value.startswith("Bearer "):
            token = cookie_value[7:]  # Remove "Bearer " prefix

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    username = verify_token(token)
    if username != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return username


def get_current_client(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Client:
    """Get current client from token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    token = credentials.credentials
    client = db.get_client_by_token(token)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client token",
        )
    return client


@app.get("/", response_class=HTMLResponse)
async def root(request: Request) -> HTMLResponse:
    """Root endpoint with login form."""
    return templates.TemplateResponse(request, "login.html")


@app.post("/login")
async def login(password: str = Form(...)) -> RedirectResponse:
    """Admin login endpoint."""
    if not verify_password(password, get_admin_password_hash()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )

    config = get_or_create_server_config()
    access_token_expires = timedelta(minutes=config.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": "admin"},
        expires_delta=access_token_expires,
    )

    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
    )
    return response


@app.get("/dashboard", response_model=None)
async def dashboard(request: Request) -> HTMLResponse | RedirectResponse:
    """Admin dashboard."""
    # Check authentication via cookie
    token = request.cookies.get("access_token")
    if not token or not token.startswith("Bearer "):
        return RedirectResponse(url="/")

    username = verify_token(token[7:])  # Remove "Bearer " prefix
    if username != "admin":
        return RedirectResponse(url="/")

    clients = db.get_all_clients()
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"request": request, "clients": clients},
    )


@app.post("/api/clients")
async def create_client(
    request: Request,  # noqa: ARG001
    client_request: ClientCreateRequest,
    _current_user: str = Depends(get_current_admin_user_from_cookie_or_header),
) -> dict[str, Any]:
    """Create a new client."""
    # Check if client already exists
    existing_client = db.get_client_by_name(client_request.name)
    if existing_client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client already exists",
        )

    token = generate_token()
    client = db.create_client(client_request.name, token)

    return {
        "id": client.id,
        "name": client.name,
        "token": client.token,
        "created_at": client.created_at,
    }


@app.get("/api/clients")
async def list_clients(
    request: Request,  # noqa: ARG001
    _current_user: str = Depends(get_current_admin_user_from_cookie_or_header),
) -> list[dict[str, Any]]:
    """List all clients."""
    clients = db.get_all_clients()
    return [
        {
            "id": client.id,
            "name": client.name,
            "created_at": client.created_at,
            "last_seen": client.last_seen,
        }
        for client in clients
    ]


@app.post("/api/audit-log")
async def submit_audit_log(
    audit_request: AuditLogRequest,
    current_client: Client = Depends(get_current_client),
) -> dict[str, str]:
    """Submit audit log entry."""
    db.add_audit_log(
        client_id=current_client.id,
        timestamp=audit_request.timestamp,
        event=audit_request.event,
    )
    db.update_client_last_seen(current_client.id)
    return {"status": "success"}


@app.post("/api/packages")
async def submit_packages(
    package_request: PackageListRequest,
    current_client: Client = Depends(get_current_client),
) -> dict[str, str]:
    """Submit package list."""
    db.add_packages(
        client_id=current_client.id,
        packages=package_request.packages,
    )
    db.update_client_last_seen(current_client.id)
    return {"status": "success"}


@app.post("/api/security-info")
async def submit_security_info(
    security_request: SecurityInfoRequest,  # noqa: ARG001
    current_client: Client = Depends(get_current_client),
) -> dict[str, str]:
    """Submit security information."""
    # For now, just acknowledge receipt
    # In a real implementation, you might want to store this in the database
    db.update_client_last_seen(current_client.id)
    return {"status": "success", "message": "Security information received"}


@app.get("/api/audit-logs")
async def get_audit_logs(
    request: Request,  # noqa: ARG001
    client_id: int | None = None,
    _current_user: str = Depends(get_current_admin_user_from_cookie_or_header),
) -> list[dict[str, Any]]:
    """Get audit logs."""
    logs = db.get_audit_logs(client_id)
    return [
        {
            "id": log.id,
            "client_id": log.client_id,
            "timestamp": log.timestamp,
            "event": log.event,
            "created_at": log.created_at,
        }
        for log in logs
    ]


@app.get("/api/packages")
async def get_packages(
    request: Request,  # noqa: ARG001
    client_id: int | None = None,
    _current_user: str = Depends(get_current_admin_user_from_cookie_or_header),
) -> list[dict[str, Any]]:
    """Get packages."""
    packages = db.get_packages(client_id)
    return [
        {
            "id": package.id,
            "client_id": package.client_id,
            "name": package.name,
            "version": package.version,
            "submitted_at": package.submitted_at,
        }
        for package in packages
    ]


@app.get("/client/{client_id}", response_model=None)
async def client_detail(
    client_id: int,
    request: Request,
) -> HTMLResponse | RedirectResponse:
    """Client detail page."""
    # Check authentication via cookie
    token = request.cookies.get("access_token")
    if not token or not token.startswith("Bearer "):
        return RedirectResponse(url="/")

    username = verify_token(token[7:])  # Remove "Bearer " prefix
    if username != "admin":
        return RedirectResponse(url="/")

    # Get client directly from database by ID
    with db.get_session() as session:
        client = session.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    audit_logs = db.get_audit_logs(client_id)
    packages = db.get_packages(client_id)

    return templates.TemplateResponse(
        request,
        "client_detail.html",
        {
            "request": request,
            "client": client,
            "audit_logs": audit_logs,
            "packages": packages,
        },
    )


def start_server(
    host: str = "127.0.0.1",
    *,
    port: int = 8000,
    reload: bool = False,
) -> None:
    """Start the web server."""
    uvicorn.run("pysec.server.app:app", host=host, port=port, reload=reload)
