#!/usr/bin/env python3
"""Fetch a fresh batch of German dative/accusative fill-in-the-blank questions
and reshape them for a quiz session.

POSTs to the quiz-service generate endpoint with ``lang=de&slug=article-case``,
then:
  * drops the ``keyword`` field from every question, and
  * splits the payload into two JSON documents on stdout:
      - ``questions``: the user-facing exam (number, category, type,
        sentenceQuiz, translation, hintZh) — NO rightAnswer/verb,
      - ``answers``:   a grading map keyed by question number, holding
        rightAnswer, sentence, category and type for the agent to check.

The exam question is ``sentenceQuiz`` (the sentence with 【】 blanked to
``____``); ``sentence`` is the reconstructed source only kept in ``answers`` so
the correct answer can be shown after grading.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "http://localhost:8070/api/quiz/generate"


def fetch_batch(base_url: str = BASE_URL) -> dict:
    url = f"{base_url}?lang=de&slug=article-case"
    req = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def reshape(payload: dict) -> dict:
    questions = []
    answers = {}
    for idx, item in enumerate(payload.get("questions", []), start=1):
        # 后端正常会返回 rightAnswer；若缺失则回退从 sentence 的 【...】 提取，
        # 保证批改永远有据可依。
        right_answer = item.get("rightAnswer")
        if not right_answer:
            m = re.search(r"【(.+?)】", item.get("sentence") or "")
            right_answer = m.group(1) if m else None
        questions.append(
            {
                "number": idx,
                "category": item.get("category"),
                "type": item.get("type"),
                "sentenceQuiz": item.get("sentenceQuiz"),
                "translation": item.get("translation"),
                "hintZh": item.get("hintZh"),
            }
        )
        answers[str(idx)] = {
            "rightAnswer": right_answer,
            "sentence": item.get("sentence"),
            "category": item.get("category"),
            "type": item.get("type"),
        }
    return {"batch_id": payload.get("batch_id"), "questions": questions, "answers": answers}


def main() -> None:
    try:
        payload = fetch_batch()
    except urllib.error.URLError as exc:
        print(f"请求失败（请确认后端已启动在 {BASE_URL}）: {exc}", file=sys.stderr)
        sys.exit(1)
    except TimeoutError as exc:
        print(f"请求超时（后端超过 60 秒未响应）: {exc}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"响应不是合法 JSON: {exc}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(reshape(payload), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()