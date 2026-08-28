import { useEffect, useState } from "react";
import { Link } from "react-router";

import { getJSON } from "../lib/api";

import type { Route } from "./+types/prompts";

type PromptTemplateInfo = {
  language_code: string;
  display_name: string;
  slug: string;
  title: string;
  system: string;
  user: string;
};

type LanguageGroup = {
  language_code: string;
  display_name: string;
  templates: PromptTemplateInfo[];
};

function groupByLanguage(list: PromptTemplateInfo[]): LanguageGroup[] {
  const map = new Map<string, LanguageGroup>();
  for (const t of list) {
    let g = map.get(t.language_code);
    if (!g) {
      g = {
        language_code: t.language_code,
        display_name: t.display_name,
        templates: [],
      };
      map.set(t.language_code, g);
    }
    g.templates.push(t);
  }
  return [...map.values()];
}

function ReadonlyBlock({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <h4 className="mb-1 text-xs font-medium text-gray-400 dark:text-gray-500">
        {label}
      </h4>
      <pre className="max-h-80 overflow-auto whitespace-pre-wrap rounded-lg bg-white p-3 font-mono text-xs leading-relaxed text-gray-800 shadow-inner dark:bg-gray-950 dark:text-gray-200">
        {value}
      </pre>
    </div>
  );
}

function TemplateRow({
  template,
}: {
  template: PromptTemplateInfo;
}) {
  return (
    <div className="flex flex-col gap-3 rounded-xl border border-gray-200 p-4 shadow-sm dark:border-gray-700">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="font-semibold">{template.title}</h3>
          <code className="text-xs text-gray-400 dark:text-gray-500">
            {template.slug}
          </code>
        </div>
        <Link
          to={`/prompts/${template.language_code}/${template.slug}/edit`}
          className="rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-blue-700"
        >
          编辑
        </Link>
      </div>
      <ReadonlyBlock label="system" value={template.system} />
      <ReadonlyBlock label="user" value={template.user} />
    </div>
  );
}

export function meta({}: Route.MetaArgs) {
  return [{ title: "Prompt 模板" }];
}

export default function Prompts() {
  const [rows, setRows] = useState<PromptTemplateInfo[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    getJSON<PromptTemplateInfo[]>("/api/prompts")
      .then((r) => {
        setRows(r);
        const groups = groupByLanguage(r);
        if (groups.length > 0) {
          setSelected((prev) => prev ?? groups[0].language_code);
        }
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  if (error) {
    return <p className="text-red-600 dark:text-red-400">加载失败：{error}</p>;
  }
  if (!rows) {
    return <p className="text-gray-500">加载中…</p>;
  }

  const groups = groupByLanguage(rows);
  if (groups.length === 0) {
    return <p className="text-gray-500">暂无注册语言。</p>;
  }

  const active = groups.find((g) => g.language_code === selected) ?? groups[0];

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold">Prompt 模板</h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
          按语言管理出题 prompt 模板；点击卡片编辑进入编辑页。
        </p>
      </header>

      <div className="flex w-full gap-8">
        <aside className="w-40 shrink-0">
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-gray-400">
            语言
          </p>
          <ul className="space-y-1">
            {groups.map((g) => {
              const isActive = g.language_code === active.language_code;
              return (
                <li key={g.language_code}>
                  <button
                    type="button"
                    onClick={() => setSelected(g.language_code)}
                    className={`block w-full text-left py-1.5 pl-3 text-sm transition ${
                      isActive
                        ? "border-l-2 border-blue-500 font-semibold text-blue-600 dark:text-blue-400"
                        : "border-l-2 border-transparent text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-gray-100"
                    }`}
                  >
                    <span className="opacity-60">
                      {g.language_code}
                    </span>{" "}
                    <span className="text-xs">{g.display_name}</span>
                  </button>
                </li>
              );
            })}
          </ul>
        </aside>

        <div className="w-full min-w-0 flex-1">
          <div className="mb-4 flex justify-end">
            <Link
              to="/prompts/new"
              className="rounded-lg bg-blue-600 px-4 py-1.5 text-sm font-medium text-white transition hover:bg-blue-700"
            >
              ＋ 新建模板
            </Link>
          </div>

          <section className="w-full">
            <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold">
              <code className="rounded bg-gray-100 px-2 py-0.5 text-sm text-blue-600 dark:bg-gray-800 dark:text-blue-400">
                {active.language_code}
              </code>
              {active.display_name}
            </h2>
            {active.templates.length === 0 ? (
              <p className="text-sm text-gray-500">该语言暂无模板。</p>
            ) : (
              <div className="flex w-full flex-col gap-4">
                {active.templates.map((t) => (
                  <TemplateRow key={t.slug} template={t} />
                ))}
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}