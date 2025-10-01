// app/util/api.ts
// Build-time configurable API base + POST helper with NO timeout by default.
// No timeout by default because LLMs can be slow sometimes.

export const API_BASE = (process.env.NEXT_PUBLIC_API_BASE ?? "").replace(
  /\/$/,
  ""
);

export function api(path: string) {
  return `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
}

export class ApiError extends Error {
  code?: "TIMEOUT" | "NETWORK" | `HTTP_${number}` | "PARSE";
  status?: number;
  detail?: string;
}

export async function postJSON<T = unknown>(
  path: string,
  body: unknown,
  opts?: { timeoutMs?: number; headers?: Record<string, string> }
): Promise<T> {
  const timeoutMs = opts?.timeoutMs ?? 0; // 0 = **no timeout**
  const ctrl = new AbortController();
  const timer =
    timeoutMs > 0 ? setTimeout(() => ctrl.abort(), timeoutMs) : null;

  try {
    const res = await fetch(api(path), {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(opts?.headers || {}) },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });

    if (!res.ok) {
      // Try to extract a useful error message
      let detail = "";
      try {
        const ct = res.headers.get("content-type") || "";
        if (ct.includes("application/json")) {
          const j = await res.json();
          detail =
            typeof j?.error === "string"
              ? j.error
              : JSON.stringify(j).slice(0, 300);
        } else {
          detail = (await res.text()).slice(0, 300);
        }
      } catch {
        /* ignore */
      }

      const err = new ApiError(
        `HTTP ${res.status}${detail ? `: ${detail}` : ""}`
      );
      err.code = `HTTP_${res.status}` as const;
      err.status = res.status;
      err.detail = detail;
      throw err;
    }

    try {
      return (await res.json()) as T;
    } catch {
      const err = new ApiError("Invalid JSON from server");
      err.code = "PARSE";
      throw err;
    }
  } catch (e: any) {
    if (e?.name === "AbortError") {
      const err = new ApiError("Request timed out");
      err.code = "TIMEOUT";
      throw err;
    }
    if (e instanceof ApiError) throw e;
    const err = new ApiError(
      navigator.onLine
        ? "Network error or CORS blocked"
        : "You appear to be offline"
    );
    err.code = "NETWORK";
    throw err;
  } finally {
    if (timer) clearTimeout(timer);
  }
}
