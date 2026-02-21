/**
 * Shared HTTP client for calling the Agencity FastAPI backend.
 */

export type ApiOpts = {
  baseUrl: string;
  apiKey: string;
  timeoutMs: number;
};

export async function agencityFetch<T = unknown>(
  opts: ApiOpts,
  path: string,
  body: Record<string, unknown>,
): Promise<T> {
  const url = `${opts.baseUrl}${path}`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), opts.timeoutMs);

  try {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (opts.apiKey) {
      headers["Authorization"] = `Bearer ${opts.apiKey}`;
    }

    const res = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new Error(`Agencity API ${res.status}: ${text || res.statusText}`);
    }

    return (await res.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

export async function agencityGet<T = unknown>(
  opts: ApiOpts,
  path: string,
): Promise<T> {
  const url = `${opts.baseUrl}${path}`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), opts.timeoutMs);

  try {
    const headers: Record<string, string> = {};
    if (opts.apiKey) {
      headers["Authorization"] = `Bearer ${opts.apiKey}`;
    }

    const res = await fetch(url, {
      method: "GET",
      headers,
      signal: controller.signal,
    });

    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new Error(`Agencity API ${res.status}: ${text || res.statusText}`);
    }

    return (await res.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}
