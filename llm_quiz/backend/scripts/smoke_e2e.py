"""End-to-end smoke test with a stubbed LLM (dev aid, not part of pytest)."""
import asyncio
import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main
from app import services
from app.database import init_db
from app.engines import get_engine
from tests.test_quiz import _sample

LANG = "ja"


async def fake_chat(messages):
    return json.dumps(_sample(), ensure_ascii=False)


async def seed() -> None:
    services.quiz_service.chat_json = fake_chat
    await services.quiz_service.generate_quiz(
        engine=get_engine(LANG),
        language=LANG,
    )


def run() -> None:
    asyncio.run(init_db())
    asyncio.run(seed())
    with TestClient(main.app) as client:
        print("frequent:", client.get(f"/api/{LANG}/verbs/frequent").json())
        print("since7:", client.get(f"/api/{LANG}/verbs/frequent?since_days=7&limit=3").json())
        history = client.get(f"/api/{LANG}/quiz/history").json()
        print("history rows:", len(history))
        first = client.get(f"/api/{LANG}/quiz/{history[0]['id']}").json()
        print("by id:", first["verb"], first["options"], first["answerPosition"])
        print("get_quiz key check:", list(first.keys()))
        print("unknown lang status:", client.get("/api/xx/quiz/history").status_code)


if __name__ == "__main__":
    run()