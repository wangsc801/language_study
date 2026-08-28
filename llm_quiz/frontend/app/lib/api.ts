export async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(path, { headers: { Accept: "application/json" } });
  if (!res.ok) {
    throw new Error(await readError(res));
  }
  return res.json() as Promise<T>;
}

export async function postJSON<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(path, {
    method: "POST",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    throw new Error(await readError(res));
  }
  return res.json() as Promise<T>;
}

export async function putJSON<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(path, {
    method: "PUT",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    throw new Error(await readError(res));
  }
  return res.json() as Promise<T>;
}

async function readError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    return data?.detail || res.statusText || String(res.status);
  } catch {
    return res.statusText || String(res.status);
  }
}