import { useCallback, useEffect, useState } from "react";

import { getJSON, postJSON } from "../lib/api";

import type { Route } from "./+types/settings";

type SettingsView = {
  llm_base_url: string;
  llm_model: string;
  llm_timeout: number;
  llm_json_mode: boolean;
  llm_api_key_masked: string;
};

type Status = { kind: "ok" | "err" | "info"; text: string };

export function meta({}: Route.MetaArgs) {
  return [
    { title: "LLM 设置" },
    { name: "description", content: "配置出题服务使用的 LLM" },
  ];
}

export default function Settings() {
  const [baseUrl, setBaseUrl] = useState("");
  const [model, setModel] = useState("");
  const [timeout, setTimeout] = useState("60");
  const [jsonMode, setJsonMode] = useState(true);
  const [apiKey, setApiKey] = useState("");
  const [keyHint, setKeyHint] = useState("尚未配置 API Key");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<Status | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await getJSON<SettingsView>("/api/settings");
      setBaseUrl(data.llm_base_url || "");
      setModel(data.llm_model || "");
      setTimeout(String(data.llm_timeout ?? 60));
      setJsonMode(!!data.llm_json_mode);
      setApiKey("");
      setKeyHint(
        data.llm_api_key_masked
          ? `当前已设置，末 4 位：${data.llm_api_key_masked.slice(-4)}`
          : "尚未配置（也可通过环境变量 LLM_API_KEY 配置）"
      );
    } catch (e) {
      setStatus({ kind: "err", text: `加载失败：${(e as Error).message}` });
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const save = async () => {
    const payload: Record<string, unknown> = {
      llm_base_url: baseUrl.trim(),
      llm_model: model.trim(),
      llm_timeout: Number(timeout),
      llm_json_mode: jsonMode,
      save: true,
    };
    if (apiKey.trim()) payload.llm_api_key = apiKey.trim();
    setBusy(true);
    try {
      const data = await postJSON<SettingsView>("/api/settings", payload);
      setStatus({
        kind: "ok",
        text: `已保存。当前 Key：${data.llm_api_key_masked || "未设置"}`,
      });
      load();
    } catch (e) {
      setStatus({ kind: "err", text: `保存失败：${(e as Error).message}` });
    } finally {
      setBusy(false);
    }
  };

  const testConn = async () => {
    setBusy(true);
    setStatus({ kind: "info", text: "正在测试…" });
    try {
      const data = await postJSON<{ ok: boolean; error?: string }>(
        "/api/settings/test"
      );
      setStatus(
        data.ok
          ? { kind: "ok", text: "连接成功 ✔" }
          : { kind: "err", text: `连接失败：${data.error || "未知错误"}` }
      );
    } catch (e) {
      setStatus({ kind: "err", text: `测试调用失败：${(e as Error).message}` });
    } finally {
      setBusy(false);
    }
  };

  const reset = async () => {
    setBusy(true);
    try {
      await postJSON<SettingsView>("/api/settings/reset");
      setStatus({ kind: "ok", text: "已重置为环境变量默认值。" });
      load();
    } catch (e) {
      setStatus({ kind: "err", text: `重置失败：${(e as Error).message}` });
    } finally {
      setBusy(false);
    }
  };

  const inputCls =
    "w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500";
  const labelCls = "mt-4 mb-1 block text-sm text-gray-500 dark:text-gray-400";

  return (
    <div className="mx-auto max-w-md space-y-4">
      <div className="rounded-2xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
        <h1 className="text-xl font-bold">LLM 配置</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          密钥仅保存在本机
          <code className="mx-1 rounded bg-gray-100 px-1 dark:bg-gray-800">
            data/llm_settings.json
          </code>
          。
        </p>

        <label className={labelCls} htmlFor="baseUrl">
          Base URL（OpenAI 兼容端点）
        </label>
        <input
          id="baseUrl"
          type="text"
          className={inputCls}
          placeholder="https://api.openai.com/v1"
          value={baseUrl}
          onChange={(e) => setBaseUrl(e.target.value)}
        />

        <label className={labelCls} htmlFor="model">
          模型
        </label>
        <input
          id="model"
          type="text"
          className={inputCls}
          placeholder="gpt-4o-mini"
          value={model}
          onChange={(e) => setModel(e.target.value)}
        />

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelCls} htmlFor="timeout">
              超时（秒）
            </label>
            <input
              id="timeout"
              type="number"
              min={1}
              step={1}
              className={inputCls}
              value={timeout}
              onChange={(e) => setTimeout(e.target.value)}
            />
          </div>
          <div>
            <label className={labelCls}>响应格式</label>
            <label className="mt-[9px] flex items-center gap-2 text-sm text-gray-700 dark:text-gray-200">
              <input
                type="checkbox"
                checked={jsonMode}
                onChange={(e) => setJsonMode(e.target.checked)}
                className="h-4 w-4 accent-blue-600"
              />
              JSON 模式
            </label>
          </div>
        </div>

        <label className={labelCls} htmlFor="apiKey">
          LLM API Key（留空则保持不变）
        </label>
        <input
          id="apiKey"
          type="password"
          className={inputCls}
          placeholder="sk-..."
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
        />
        <p className="mt-1 text-xs text-gray-400">{keyHint}</p>

        <div className="mt-5 grid grid-cols-3 gap-2">
          <button
            type="button"
            onClick={save}
            disabled={busy}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white transition hover:bg-blue-700 disabled:opacity-60"
          >
            保存
          </button>
          <button
            type="button"
            onClick={testConn}
            disabled={busy}
            className="rounded-lg bg-gray-200 px-4 py-2 text-sm text-gray-700 transition hover:bg-gray-300 disabled:opacity-60 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
          >
            测试连接
          </button>
          <button
            type="button"
            onClick={reset}
            disabled={busy}
            className="rounded-lg bg-gray-200 px-4 py-2 text-sm text-gray-700 transition hover:bg-gray-300 disabled:opacity-60 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
          >
            重置
          </button>
        </div>

        {status && (
          <p
            className={
              status.kind === "ok"
                ? "mt-4 text-sm text-green-600 dark:text-green-400"
                : status.kind === "err"
                  ? "mt-4 text-sm text-red-600 dark:text-red-400"
                  : "mt-4 text-sm text-gray-500"
            }
          >
            {status.text}
          </p>
        )}
      </div>
    </div>
  );
}