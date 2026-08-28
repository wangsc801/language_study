import { useEffect, useState } from "react";
import { Link } from "react-router";

import { getJSON } from "../lib/api";

import type { Route } from "./+types/languages";

type LanguageInfo = {
  id: number;
  language_code: string;
  display_name: string;
};

export function meta({}: Route.MetaArgs) {
  return [{ title: "语言管理" }];
}

export default function Languages() {
  const [rows, setRows] = useState<LanguageInfo[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getJSON<LanguageInfo[]>("/api/languages")
      .then(setRows)
      .catch((e: Error) => setError(e.message));
  }, []);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold">语言管理</h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
          管理语言注册表（language_code 与显示名）；模板与生成均以此处为准。
        </p>
      </header>

      <div className="flex justify-end">
        <Link
          to="/languages/new"
          className="rounded-lg bg-blue-600 px-4 py-1.5 text-sm font-medium text-white transition hover:bg-blue-700"
        >
          ＋ 新建语言
        </Link>
      </div>

      {error ? (
        <p className="text-red-600 dark:text-red-400">加载失败：{error}</p>
      ) : !rows ? (
        <p className="text-gray-500">加载中…</p>
      ) : rows.length === 0 ? (
        <p className="text-gray-500">暂无语言。</p>
      ) : (
        <ul className="flex flex-col gap-3">
          {rows.map((l) => (
            <li
              key={l.id}
              className="flex items-center justify-between gap-2 rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-900"
            >
              <div>
                <code className="text-sm font-semibold text-blue-600 dark:text-blue-400">
                  {l.language_code}
                </code>
                <span className="ml-2 text-gray-700 dark:text-gray-300">
                  {l.display_name}
                </span>
              </div>
              <Link
                to={`/languages/${l.language_code}/edit`}
                className="shrink-0 rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-blue-700"
              >
                编辑
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}