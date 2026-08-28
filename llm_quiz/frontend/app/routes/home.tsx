import { useEffect, useState } from "react";
import { Link } from "react-router";

import { getJSON } from "../lib/api";

import type { Route } from "./+types/home";

type LanguageInfo = {
  language_code: string;
  display_name: string;
};

export function meta({}: Route.MetaArgs) {
  return [
    { title: "多语言选词填空出题服务" },
    { name: "description", content: "LLM 创作 + 引擎标注的选词填空出题服务" },
  ];
}

export default function Home() {
  const [languages, setLanguages] = useState<LanguageInfo[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getJSON<LanguageInfo[]>("/api/languages")
      .then(setLanguages)
      .catch((e: Error) => setError(e.message));
  }, []);

  return (
    <div className="space-y-8">
      <section className="rounded-2xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
        <h1 className="text-2xl font-bold">多语言选词填空出题服务</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-300">
          LLM 根据各语言引擎规则创作动词变位单选题，并自动标注假名、挖空、打乱选项。
        </p>
      </section>

      <section className="rounded-2xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
        <h2 className="mb-3 text-lg font-semibold">支持的语言</h2>
        {error ? (
          <p className="text-red-600 dark:text-red-400">加载失败：{error}</p>
        ) : !languages ? (
          <p className="text-gray-500">加载中…</p>
        ) : languages.length === 0 ? (
          <p className="text-gray-500">暂无注册语言。</p>
        ) : (
          <ul className="flex flex-wrap gap-2">
            {languages.map((l) => (
              <li
                key={l.language_code}
                className="rounded-lg bg-gray-100 px-3 py-1.5 text-sm dark:bg-gray-800"
              >
                <code className="mr-1 text-blue-600 dark:text-blue-400">
                  {l.language_code}
                </code>
                {l.display_name}
              </li>
            ))}
          </ul>
        )}
      </section>

      <nav className="grid gap-4 sm:grid-cols-2">
        <Link
          to="/settings"
          className="rounded-2xl border border-gray-200 bg-white p-5 transition hover:border-blue-400 dark:border-gray-800 dark:bg-gray-900 dark:hover:border-blue-500"
        >
          <h3 className="font-semibold">LLM 设置</h3>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
            配置 Base URL、模型、API Key 并测试连接。
          </p>
        </Link>
        <Link
          to="/prompts"
          className="rounded-2xl border border-gray-200 bg-white p-5 transition hover:border-blue-400 dark:border-gray-800 dark:bg-gray-900 dark:hover:border-blue-500"
        >
          <h3 className="font-semibold">Prompt 模板</h3>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
            按语言查看出题所用的 system / user 提示模板。
          </p>
        </Link>
      </nav>
    </div>
  );
}