import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";

import { getJSON, putJSON } from "../lib/api";

import type { Route } from "./+types/languages-edit";

type LanguageInfo = {
  id: number;
  language_code: string;
  display_name: string;
};

const inputCls =
  "w-full rounded-lg border border-gray-300 bg-white p-2.5 text-sm text-gray-900 focus:border-blue-400 focus:outline-none dark:border-gray-600 dark:bg-gray-950 dark:text-gray-100";
const labelCls = "mb-1 block text-sm font-medium text-gray-500 dark:text-gray-400";

export function meta({}: Route.MetaArgs) {
  return [{ title: "编辑语言" }];
}

export default function LanguagesEdit() {
  const { code } = useParams();
  const navigate = useNavigate();

  const [loaded, setLoaded] = useState(false);
  const [notFound, setNotFound] = useState(false);
  const [editingCode, setEditingCode] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(
    null
  );

  useEffect(() => {
    getJSON<LanguageInfo[]>("/api/languages")
      .then((rows) => {
        const l = rows.find((r) => r.language_code === code);
        if (!l) {
          setNotFound(true);
          return;
        }
        setEditingCode(l.language_code);
        setDisplayName(l.display_name);
        setLoaded(true);
      })
      .catch((e: Error) =>
        setMessage({ ok: false, text: e instanceof Error ? e.message : String(e) })
      );
  }, [code]);

  const save = useCallback(async () => {
    setSaving(true);
    setMessage(null);
    try {
      const updated = await putJSON<LanguageInfo>(`/api/languages/${code}`, {
        language_code: editingCode,
        display_name: displayName,
      });
      if (updated.language_code !== code) {
        navigate(`/languages/${updated.language_code}/edit`);
      } else {
        navigate("/languages");
      }
    } catch (e: unknown) {
      setMessage({ ok: false, text: e instanceof Error ? e.message : String(e) });
    } finally {
      setSaving(false);
    }
  }, [code, editingCode, displayName, navigate]);

  if (notFound) {
    return (
      <div className="space-y-4">
        <p className="text-red-600 dark:text-red-400">语言不存在。</p>
        <Link to="/languages" className="text-sm text-blue-600 hover:underline">
          ← 返回语言列表
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
        <h1 className="text-2xl font-bold">编辑语言</h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
          修改 language_code（唯一性查重）或 display_name 后保存。
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
          <label className={labelCls}>language_code（唯一标识）</label>
          <input
            value={editingCode}
            onChange={(e) => setEditingCode(e.target.value)}
            className={inputCls}
            spellCheck={false}
          />
        </div>
        <div>
          <label className={labelCls}>display_name（显示名）</label>
          <input
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            className={inputCls}
          />
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={save}
          disabled={saving || !editingCode.trim() || !displayName.trim()}
          className="rounded-lg bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          保存
        </button>
        <Link
          to="/languages"
          className="rounded-lg border border-gray-300 px-4 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
        >
          取消
        </Link>
      </div>
    </div>
  );
}