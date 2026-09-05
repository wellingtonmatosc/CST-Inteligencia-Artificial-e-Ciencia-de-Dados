from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from app.api import admin, game, participants
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(title=settings.app_name, version="0.1.0")
app.include_router(participants.router)
app.include_router(game.router)
app.include_router(admin.router)

BASE = Path(__file__).resolve().parent
STATIC = BASE / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name}


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
    return FileResponse(STATIC / "pages" / "admin.html")
