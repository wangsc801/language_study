"""FastAPI entrypoint: uvicorn main:app"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

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

# Serve the built frontend (React Router client assets) from the static dir.
# Mounted last (after the API routers) so /api/* and /health always win.
STATIC_DIR = Path(__file__).resolve().parent / "app" / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}