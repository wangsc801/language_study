"""FastAPI entrypoint: uvicorn main:app"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database import (
    init_db,
    upsert_languages,
    upsert_prompt_templates,
)
from app.engines import REGISTRY
from app.routers import languages, prompts, quiz, settings, verbs


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    await upsert_languages(
        [
            {"language_code": cls.language_code, "display_name": cls.display_name}
            for cls in REGISTRY.values()
        ]
    )
    for code, engine_cls in REGISTRY.items():
        engine = engine_cls()
        await upsert_prompt_templates(code, engine.prompt_docs())
        try:
            engine.init()
        except RuntimeError:
            pass
    yield


app = FastAPI(
    title="Language Learning Quiz Service",
    description="多语言选词填空出题服务：LLM 创作 + 引擎标注（如日语假名）+ SQLite 存储",
    version="0.2.0",
    lifespan=lifespan,
)

app.include_router(quiz.flat_router)
app.include_router(quiz.router)
app.include_router(verbs.router)
app.include_router(settings.router)
app.include_router(prompts.router)
app.include_router(languages.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

# Serve the built frontend (React Router client assets) from the static dir.
# Mounted after the API routers and /health so those routes always win over the
# catch-all. StaticFiles(html=True) serves index.html only at exactly "/"; every
# other path is looked up as a real file and 404s if absent.
APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "app" / "static"
STATIC_DIR.mkdir(exist_ok=True)
INDEX_HTML = STATIC_DIR / "index.html"
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


@app.exception_handler(StarletteHTTPException)
async def spa_fallback(request: Request, exc: StarletteHTTPException):
    # React Router is an SPA: client-side routes (e.g. /quizzes) have no matching
    # file on disk, so StaticFiles raises 404. On direct navigation or refresh the
    # browser hits the server for that URL, so fall back to index.html. Preserve
    # real JSON 404s for unknown /api/* (and /health after routes are matched) so
    # API clients still get {"detail":"Not Found"}.
    if exc.status_code == 404 and not request.url.path.startswith("/api"):
        return FileResponse(INDEX_HTML)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})