const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";
const UPLOAD_TIMEOUT_MS = 5 * 60 * 1000;
const DEFAULT_POST_TIMEOUT_MS = 3 * 60 * 1000;

type ValidationError = { msg: string; loc?: (string | number)[] };

function parseErrorDetail(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        const err = item as ValidationError;
        return err.msg ?? JSON.stringify(item);
      })
      .join("; ");
  }
  if (detail && typeof detail === "object" && "message" in detail) {
    return String((detail as { message: unknown }).message);
  }
  return "Request failed.";
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (response.ok) {
    if (response.status === 204) return undefined as T;
    return response.json() as Promise<T>;
  }

  let detail: unknown;
  try {
    const body = await response.json();
    detail = body.detail ?? body.message ?? response.statusText;
  } catch {
    detail = response.statusText;
  }
  throw new Error(parseErrorDetail(detail));
}

async function fetchWithTimeout(
  url: string,
  init: RequestInit,
  timeoutMs: number
): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error(`Request timed out after ${Math.round(timeoutMs / 1000)}s. Check backend logs.`);
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  return handleResponse<T>(response);
}

export async function apiPost<T>(
  path: string,
  body?: unknown,
  timeoutMs = DEFAULT_POST_TIMEOUT_MS
): Promise<T> {
  const url = `${API_BASE}${path}`;
  console.info("[api] POST start", { url, timeoutMs, bodyChars: body ? JSON.stringify(body).length : 0 });

  const started = performance.now();
  try {
    const response = await fetchWithTimeout(
      url,
      {
        method: "POST",
        headers: body ? { "Content-Type": "application/json" } : undefined,
        body: body ? JSON.stringify(body) : undefined,
      },
      timeoutMs
    );
    const result = await handleResponse<T>(response);
    console.info("[api] POST success", { url, elapsedMs: Math.round(performance.now() - started) });
    return result;
  } catch (err) {
    console.error("[api] POST failed", {
      url,
      elapsedMs: Math.round(performance.now() - started),
      error: err instanceof Error ? err.message : String(err),
    });
    throw err;
  }
}

export async function apiUpload<T>(path: string, formData: FormData): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), UPLOAD_TIMEOUT_MS);

  try {
    const response = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      body: formData,
      signal: controller.signal,
    });
    return handleResponse<T>(response);
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error("Upload timed out. The document may still be indexing — check the library.");
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}
