// app/util/api.ts
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

/**
 * postJSON
 * - body: payload
 * - opts.timeoutMs: number (0 means no timeout)
 * - opts.headers: custom headers
 * - opts.signal: optional external AbortSignal to integrate (so caller can abort)
 */
export async function postJSON<T = unknown>(
  path: string,
  body: unknown,
  opts?: {
    timeoutMs?: number;
    headers?: Record<string, string>;
    signal?: AbortSignal;
  }
): Promise<T> {
  const timeoutMs = opts?.timeoutMs ?? 0; // 0 = no timeout

  // internal controller we use for fetch. We wire up external signal to this controller
  const internalCtrl = new AbortController();

  // If caller passed an external signal, forward its abort to our internal controller
  let externalAbortListener: (() => void) | null = null;
  if (opts?.signal) {
    const ext = opts.signal;
    externalAbortListener = () => internalCtrl.abort();
    // If already aborted, abort immediately
    if (ext.aborted) internalCtrl.abort();
    else ext.addEventListener("abort", externalAbortListener);
  }

  const timer =
    timeoutMs > 0
      ? setTimeout(() => {
          internalCtrl.abort();
        }, timeoutMs)
      : null;

  try {
    const res = await fetch(api(path), {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(opts?.headers || {}) },
      body: JSON.stringify(body),
      signal: internalCtrl.signal,
    });

    if (!res.ok) {
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
    // Normalize abort -> TIMEOUT so existing code paths that look for TIMEOUT still work.
    if (e?.name === "AbortError") {
      const err = new ApiError("Request timed out or aborted");
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
    if (opts?.signal && externalAbortListener) {
      try {
        opts.signal.removeEventListener("abort", externalAbortListener);
      } catch {}
    }
  }
}
