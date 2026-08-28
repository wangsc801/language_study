import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router";

import { getJSON, postJSON } from "../lib/api";

import type { Route } from "./+types/prompts-new";

type PromptTemplateInfo = {
  language_code: string;
  display_name: string;
  slug: string;
  title: string;
  system: string;
  user: string;
};

type LanguageInfo = { language_code: string; display_name: string };

const inputCls =
  "w-full rounded-lg border border-gray-300 bg-white p-2.5 text-sm text-gray-900 focus:border-blue-400 focus:outline-none dark:border-gray-600 dark:bg-gray-950 dark:text-gray-100";
const labelCls = "mb-1 block text-sm font-medium text-gray-500 dark:text-gray-400";

export function meta({}: Route.MetaArgs) {
  return [{ title: "新建模板" }];
}

export default function PromptsNew() {
  const navigate = useNavigate();
  const [languages, setLanguages] = useState<LanguageInfo[] | null>(null);
  const [language, setLanguage] = useState("");
  const [slug, setSlug] = useState("");
  const [title, setTitle] = useState("");
  const [system, setSystem] = useState("");
  const [user, setUser] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getJSON<LanguageInfo[]>("/api/languages")
      .then((langs) => {
        setLanguages(langs);
        if (langs.length > 0) setLanguage((prev) => prev || langs[0].language_code);
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  const save = useCallback(async () => {
    setSaving(true);
    setError(null);
    try {
      await postJSON<PromptTemplateInfo>("/api/prompts", {
        language_code: language,
        slug,
        title,
        system,
        user,
      });
      navigate("/prompts");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }, [language, slug, title, system, user, navigate]);

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <header>
        <h1 className="text-2xl font-bold">新建模板</h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
          为新语言（或该语言的新题型）创建模板。
        </p>
      </header>

      {error && (
        <p className="rounded-lg bg-red-50 p-3 text-sm text-red-600 dark:bg-red-950 dark:text-red-400">
          {error}
        </p>
      )}

      <div className="space-y-4 rounded-2xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
        <div>
          <label className={labelCls}>语言</label>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className={inputCls}
          >
            {(languages ?? []).map((l) => (
              <option key={l.language_code} value={l.language_code}>
                {l.language_code} — {l.display_name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className={labelCls}>slug（唯一标识，用于 URL，如 verb-conjugation）</label>
          <input value={slug} onChange={(e) => setSlug(e.target.value)} className={inputCls} spellCheck={false} />
        </div>
        <div>
          <label className={labelCls}>title（显示名）</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} className={inputCls} />
        </div>
        <div>
          <label className={labelCls}>system prompt</label>
          <textarea value={system} onChange={(e) => setSystem(e.target.value)} rows={6} className={`${inputCls} resize-y font-mono`} spellCheck={false} />
        </div>
        <div>
          <label className={labelCls}>user prompt</label>
          <textarea value={user} onChange={(e) => setUser(e.target.value)} rows={8} className={`${inputCls} resize-y font-mono`} spellCheck={false} />
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={save}
          disabled={saving || !language || !slug.trim() || !title.trim()}
          className="rounded-lg bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          保存
        </button>
        <Link
          to="/prompts"
          className="rounded-lg border border-gray-300 px-4 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
        >
          取消
        </Link>
      </div>
    </div>
  );
}