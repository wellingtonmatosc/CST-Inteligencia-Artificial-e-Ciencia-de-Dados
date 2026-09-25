from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import admin, admin_dashboard, game, participants, question_pool
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(title=settings.app_name, version="1.0.0")
app.include_router(participants.router)
app.include_router(game.router)
app.include_router(admin.router)
app.include_router(admin_dashboard.router)
app.include_router(question_pool.router)

BASE = Path(__file__).resolve().parent
STATIC = BASE / "static"
ADMIN_UI_VERSION = "20260925-1845"
app.mount("/static", StaticFiles(directory=STATIC), name="static")


def _admin_html() -> str:
    html = (STATIC / "pages" / "admin.html").read_text(encoding="utf-8")
    html = html.replace(
        '<html lang="pt-BR">',
        f'<html lang="pt-BR" data-admin-ui-version="{ADMIN_UI_VERSION}">',
        1,
    )
    for asset in (
        "/static/css/styles.css",
        "/static/css/admin-panel.css",
        "/static/css/admin-ops.css",
        "/static/js/avatars.js",
        "/static/js/common.js",
        "/static/js/admin.js",
        "/static/js/admin-analytics.js",
    ):
        html = html.replace(asset, f"{asset}?v={ADMIN_UI_VERSION}")
    bootstrap = (
        "<script>"
        f"window.__ADMIN_UI_VERSION__='{ADMIN_UI_VERSION}';"
        "window.addEventListener('pageshow',function(e){"
        "if(e.persisted){location.reload();}"
        "});"
        "</script>"
    )
    return html.replace("</head>", bootstrap + "</head>", 1)


@app.middleware("http")
async def response_headers(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path.startswith("/static/js/admin") or path.startswith("/static/css/admin"):
        # O ADM muda com frequência durante a homologação. Nunca reutilizar uma
        # versão administrativa antiga em conjunto com HTML de outro deploy.
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    elif path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=0, must-revalidate"
    elif path in {"/", "/ranking", "/admin"} or path.startswith("/q/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(self), microphone=(self), geolocation=()"
    return response


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name, "version": "1.0.0"}


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "pages" / "index.html")


@app.get("/q/{code}", include_in_schema=False)
def scan_page(code: str):
    return FileResponse(STATIC / "pages" / "scan.html")


@app.get("/ranking", include_in_schema=False)
def ranking_page():
    return FileResponse(STATIC / "pages" / "ranking.html")


@app.get("/admin", include_in_schema=False)
def admin_page():
    return HTMLResponse(_admin_html())
