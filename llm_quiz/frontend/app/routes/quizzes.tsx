import { useEffect, useMemo, useState } from "react";

import { getJSON } from "../lib/api";

import type { Route } from "./+types/quizzes";

type LanguageInfo = {
  language_code: string;
  display_name: string;
};

type QuizItem = {
  id: number;
  language: string;
  batch_id: string;
  created_at: string;
  category: string;
  type: string;
  keyword?: string; // Japanese
  verb?: string; // German
  keywordFurigana?: string;
  sentence?: string;
  sentenceFurigana?: string;
  sentenceQuiz?: string;
  translation?: string;
  rightAnswer?: string;
  hintZh?: string | null;
};

type Batch = {
  batch_id: string;
  created_at: string;
  questions: QuizItem[];
};

function groupByBatch(list: QuizItem[]): Batch[] {
  const map = new Map<string, Batch>();
  for (const q of list) {
    let b = map.get(q.batch_id);
    if (!b) {
      b = { batch_id: q.batch_id, created_at: q.created_at, questions: [] };
      map.set(q.batch_id, b);
    }
    b.questions.push(q);
  }
  return [...map.values()];
}

function Badge({ children }: { children: string }) {
  return (
    <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600 dark:bg-gray-800 dark:text-gray-300">
      {children}
    </span>
  );
}

function QuizCard({ q }: { q: QuizItem }) {
  const word = q.keyword ?? q.verb ?? "";
  return (
    <div className="rounded-xl border border-gray-200 p-4 dark:border-gray-700">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <Badge>{q.category}</Badge>
        <Badge>{q.type}</Badge>
        <span className="ml-auto text-xs text-gray-400 dark:text-gray-500">
          #{q.id}
        </span>
      </div>

      <div className="mb-2 text-lg font-semibold">
        <span className="mr-1">{word}</span>
        {q.keywordFurigana ? (
          <span className="text-sm font-normal text-gray-500 dark:text-gray-400">
            {q.keywordFurigana}
          </span>
        ) : null}
      </div>

      <div className="mb-1 rounded-lg bg-gray-50 p-3 text-gray-800 dark:bg-gray-900 dark:text-gray-200">
        {q.sentenceQuiz}
      </div>
      {q.sentenceFurigana ? (
        <p className="mb-1 text-sm text-gray-500 dark:text-gray-400">
          {q.sentenceFurigana}
        </p>
      ) : null}
      {q.sentence && q.sentence !== q.sentenceQuiz ? (
        <p className="mb-1 text-sm text-gray-400 dark:text-gray-500">
          {q.sentence}
        </p>
      ) : null}
      <p className="text-sm text-gray-500 dark:text-gray-400">{q.translation}</p>

      {q.hintZh ? <p className="mt-2 text-xs text-amber-600 dark:text-amber-400">提示：{q.hintZh}</p> : null}
      {q.rightAnswer ? (
        <p className="mt-1 text-sm font-medium text-green-700 dark:text-green-400">
          参考答案：{q.rightAnswer}
        </p>
      ) : null}
    </div>
  );
}

function BatchCard({ batch }: { batch: Batch }) {
  return (
    <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-900">
      <header className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="font-semibold">Batch {batch.batch_id.slice(0, 8)}</h3>
          <p className="text-xs text-gray-400 dark:text-gray-500">
            共 {batch.questions.length} 题 · {batch.created_at}
          </p>
        </div>
      </header>
      <div className="flex w-full flex-col gap-3">
        {batch.questions.map((q) => (
          <QuizCard key={q.id} q={q} />
        ))}
      </div>
    </section>
  );
}

export function meta({}: Route.MetaArgs) {
  return [{ title: "题目记录" }];
}

export default function Quizzes() {
  const [languages, setLanguages] = useState<LanguageInfo[] | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [quizzes, setQuizzes] = useState<QuizItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getJSON<LanguageInfo[]>("/api/languages")
      .then((r) => {
        setLanguages(r);
        setSelected((prev) => prev ?? (r.length > 0 ? r[0].language_code : null));
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  useEffect(() => {
    if (!selected) return;
    setQuizzes(null);
    setError(null);
    getJSON<QuizItem[]>(`/api/${selected}/quiz/history?limit=200`)
      .then(setQuizzes)
      .catch((e: Error) => setError(e.message));
  }, [selected]);

  const batches = useMemo(() => (quizzes ? groupByBatch(quizzes) : []), [quizzes]);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold">题目记录</h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
          按 Batch 分组浏览各语言的已生成题目。
        </p>
      </header>

      <div className="flex w-full gap-8">
        <aside className="w-40 shrink-0">
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-gray-400">
            语言
          </p>
          {error && !languages ? (
            <p className="text-xs text-red-600 dark:text-red-400">加载失败</p>
          ) : !languages ? (
            <p className="text-xs text-gray-500">加载中…</p>
          ) : (
            <ul className="space-y-1">
              {languages.map((l) => {
                const isActive = l.language_code === selected;
                return (
                  <li key={l.language_code}>
                    <button
                      type="button"
                      onClick={() => setSelected(l.language_code)}
                      className={`block w-full text-left py-1.5 pl-3 text-sm transition ${
                        isActive
                          ? "border-l-2 border-blue-500 font-semibold text-blue-600 dark:text-blue-400"
                          : "border-l-2 border-transparent text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-gray-100"
                      }`}
                    >
                      <span className="opacity-60">{l.language_code}</span>{" "}
                      <span className="text-xs">{l.display_name}</span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
          </aside>

        <div className="w-full min-w-0 flex-1">
          {error ? (
            <p className="text-red-600 dark:text-red-400">加载失败：{error}</p>
          ) : !quizzes ? (
            <p className="text-gray-500">加载中…</p>
          ) : quizzes.length === 0 ? (
            <p className="text-sm text-gray-500">该语言当前没有题目记录。</p>
          ) : (
            <div className="flex w-full flex-col gap-5">
              {batches.map((b) => (
                <BatchCard key={b.batch_id} batch={b} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}