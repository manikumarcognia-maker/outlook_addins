import type { Context } from "hono";
import type { WorkerEnv } from "./env";

const HOP_BY_HOP = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailers",
  "transfer-encoding",
  "upgrade",
]);

function buildProxyHeaders(request: Request): Headers {
  const headers = new Headers(request.headers);
  for (const name of HOP_BY_HOP) {
    headers.delete(name);
  }
  return headers;
}

export async function proxyToPythonBackend(
  c: Context<{ Bindings: WorkerEnv }>
): Promise<Response> {
  const origin = c.env.PYTHON_BACKEND_URL?.trim();
  if (!origin) {
    return c.json(
      {
        detail:
          "API is not available on this Worker yet. Set PYTHON_BACKEND_URL to your FastAPI origin, or port /api routes into this Worker.",
      },
      503
    );
  }

  const incoming = new URL(c.req.url);
  const target = new URL(incoming.pathname + incoming.search, origin);

  const proxied = await fetch(
    new Request(target.toString(), {
      method: c.req.method,
      headers: buildProxyHeaders(c.req.raw),
      body: c.req.raw.body,
      redirect: "manual",
    })
  );

  const headers = new Headers(proxied.headers);
  headers.set("Access-Control-Allow-Origin", "*");
  headers.set("Content-Security-Policy", "frame-ancestors *");
  headers.delete("x-frame-options");

  return new Response(proxied.body, {
    status: proxied.status,
    statusText: proxied.statusText,
    headers,
  });
}
