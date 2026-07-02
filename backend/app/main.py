from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.config import BASE_DIR, settings
from backend.app.routers import health, temperature


app = FastAPI(title="CWA Temperature API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(temperature.router)
app.include_router(health.router)

frontend_dir = BASE_DIR / "frontend"
assets_dir = frontend_dir / "assets"

if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


@app.get("/")
def index():
    return FileResponse(frontend_dir / "index.html")
