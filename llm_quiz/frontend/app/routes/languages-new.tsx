import { useCallback, useState } from "react";
import { Link, useNavigate } from "react-router";

import { postJSON } from "../lib/api";

import type { Route } from "./+types/languages-new";

type LanguageInfo = {
  id: number;
  language_code: string;
  display_name: string;
};

const inputCls =
  "w-full rounded-lg border border-gray-300 bg-white p-2.5 text-sm text-gray-900 focus:border-blue-400 focus:outline-none dark:border-gray-600 dark:bg-gray-950 dark:text-gray-100";
const labelCls = "mb-1 block text-sm font-medium text-gray-500 dark:text-gray-400";

export function meta({}: Route.MetaArgs) {
  return [{ title: "新建语言" }];
}

export default function LanguagesNew() {
  const navigate = useNavigate();
  const [code, setCode] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const save = useCallback(async () => {
    setSaving(true);
    setError(null);
    try {
      await postJSON<LanguageInfo>("/api/languages", {
        language_code: code,
        display_name: displayName,
      });
      navigate("/languages");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }, [code, displayName, navigate]);

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <header>
        <h1 className="text-2xl font-bold">新建语言</h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
          创建新语言（language_code 无需对应引擎；生成需有对应引擎）。
        </p>
      </header>

      {error && (
        <p className="rounded-lg bg-red-50 p-3 text-sm text-red-600 dark:bg-red-950 dark:text-red-400">
          {error}
        </p>
      )}

      <div className="space-y-4 rounded-2xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
        <div>
          <label className={labelCls}>language_code（唯一标识，如 es）</label>
          <input
            value={code}
            onChange={(e) => setCode(e.target.value)}
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
          disabled={saving || !code.trim() || !displayName.trim()}
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