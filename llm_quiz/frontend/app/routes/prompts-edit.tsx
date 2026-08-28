import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";

import { getJSON, postJSON, putJSON } from "../lib/api";

import type { Route } from "./+types/prompts-edit";

type PromptTemplateInfo = {
  language_code: string;
  display_name: string;
  slug: string;
  title: string;
  system: string;
  user: string;
};

const inputCls =
  "w-full rounded-lg border border-gray-300 bg-white p-2.5 text-sm text-gray-900 focus:border-blue-400 focus:outline-none dark:border-gray-600 dark:bg-gray-950 dark:text-gray-100";
const labelCls = "mb-1 block text-sm font-medium text-gray-500 dark:text-gray-400";

export function meta({}: Route.MetaArgs) {
  return [{ title: "编辑模板" }];
}

export default function PromptsEdit() {
  const { language, slug } = useParams();
  const navigate = useNavigate();

  const [loaded, setLoaded] = useState(false);
  const [notFound, setNotFound] = useState(false);
  const [editingSlug, setEditingSlug] = useState("");
  const [title, setTitle] = useState("");
  const [system, setSystem] = useState("");
  const [user, setUser] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(
    null
  );

  useEffect(() => {
    getJSON<PromptTemplateInfo[]>("/api/prompts")
      .then((rows) => {
        const t = rows.find(
          (r) => r.language_code === language && r.slug === slug
        );
        if (!t) {
          setNotFound(true);
          return;
        }
        setEditingSlug(t.slug);
        setTitle(t.title);
        setSystem(t.system);
        setUser(t.user);
        setLoaded(true);
      })
      .catch((e: Error) =>
        setMessage({ ok: false, text: e instanceof Error ? e.message : String(e) })
      );
  }, [language, slug]);

  const save = useCallback(async () => {
    setSaving(true);
    setMessage(null);
    try {
      const updated = await putJSON<PromptTemplateInfo>(
        `/api/prompts/${language}/${slug}`,
        { slug: editingSlug, title, system, user }
      );
      if (updated.slug !== slug) {
        navigate(`/prompts/${updated.language_code}/${updated.slug}/edit`);
      } else {
        navigate("/prompts");
      }
    } catch (e: unknown) {
      setMessage({ ok: false, text: e instanceof Error ? e.message : String(e) });
    } finally {
      setSaving(false);
    }
  }, [language, slug, editingSlug, title, system, user, navigate]);

  const reset = useCallback(async () => {
    setSaving(true);
    setMessage(null);
    try {
      const updated = await postJSON<PromptTemplateInfo>(
        `/api/prompts/${language}/${slug}/reset`
      );
      setEditingSlug(updated.slug);
      setTitle(updated.title);
      setSystem(updated.system);
      setUser(updated.user);
      setMessage({ ok: true, text: "已重置为默认" });
    } catch (e: unknown) {
      setMessage({ ok: false, text: e instanceof Error ? e.message : String(e) });
    } finally {
      setSaving(false);
    }
  }, [language, slug]);

  if (notFound) {
    return (
      <div className="space-y-4">
        <p className="text-red-600 dark:text-red-400">模板不存在。</p>
        <Link to="/prompts" className="text-sm text-blue-600 hover:underline">
          ← 返回模板列表
        </Link>
      </div>
    );
  }
  if (!loaded) {
    return <p className="text-gray-500">加载中…</p>;
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <header>
        <h1 className="text-2xl font-bold">编辑模板</h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
          语言 <code className="text-blue-600 dark:text-blue-400">{language}</code> · 修改
          slug、title 或 prompt 后保存。
        </p>
      </header>

      {message && (
        <p
          className={`rounded-lg p-3 text-sm ${
            message.ok
              ? "bg-green-50 text-green-600 dark:bg-green-950 dark:text-green-400"
              : "bg-red-50 text-red-600 dark:bg-red-950 dark:text-red-400"
          }`}
        >
          {message.text}
        </p>
      )}

      <div className="space-y-4 rounded-2xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
        <div>
          <label className={labelCls}>slug（唯一标识，用于 URL）</label>
          <input
            value={editingSlug}
            onChange={(e) => setEditingSlug(e.target.value)}
            className={inputCls}
            spellCheck={false}
          />
        </div>
        <div>
          <label className={labelCls}>title（显示名）</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} className={inputCls} />
        </div>
        <div>
          <label className={labelCls}>system prompt</label>
          <textarea
            value={system}
            onChange={(e) => setSystem(e.target.value)}
            rows={6}
            className={`${inputCls} resize-y font-mono`}
            spellCheck={false}
          />
        </div>
        <div>
          <label className={labelCls}>user prompt</label>
          <textarea
            value={user}
            onChange={(e) => setUser(e.target.value)}
            rows={8}
            className={`${inputCls} resize-y font-mono`}
            spellCheck={false}
          />
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={save}
          disabled={saving || !editingSlug.trim() || !title.trim()}
          className="rounded-lg bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          保存
        </button>
        <button
          type="button"
          onClick={reset}
          disabled={saving}
          className="rounded-lg border border-gray-300 px-4 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
        >
          重置为默认
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