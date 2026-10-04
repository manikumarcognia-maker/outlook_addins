import { Hono } from "hono";
import type { WorkerEnv } from "./env";
import { proxyToPythonBackend } from "./apiProxy";
import { handleOptions, outlookResponseHeaders } from "./outlookHeaders";

const app = new Hono<{ Bindings: WorkerEnv }>();

app.use("*", outlookResponseHeaders);
app.options("*", handleOptions);

app.get("/health", async (c) => {
  const origin = c.env.PYTHON_BACKEND_URL?.trim();
  if (!origin) {
    return c.json({
      ok: true,
      service: c.env.SERVICE_NAME,
      database: "unknown",
      api: "worker-only",
    });
  }

  try {
    const res = await fetch(new URL("/health", origin));
    const body = (await res.json()) as Record<string, unknown>;
    const payload = { ...body, edge: c.env.SERVICE_NAME };
    if (!res.ok) {
      return c.json(payload, 502);
    }
    return c.json(payload);
  } catch {
    return c.json(
      {
        ok: false,
        service: c.env.SERVICE_NAME,
        database: "unavailable",
        api: "python-backend-unreachable",
      },
      502
    );
  }
});

app.all("/api/*", proxyToPythonBackend);

/** Worker runs first; non-API traffic is served from the Vite build (see wrangler.toml assets). */
async function serveStatic(request: Request, env: WorkerEnv): Promise<Response> {
  return env.ASSETS.fetch(request);
}

export default {
  async fetch(request: Request, env: WorkerEnv, _ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname === "/health" || url.pathname.startsWith("/api/")) {
      return app.fetch(request, env, _ctx);
    }
    const assetResponse = await serveStatic(request, env);
    const headers = new Headers(assetResponse.headers);
    headers.set("Access-Control-Allow-Origin", "*");
    headers.set("Content-Security-Policy", "frame-ancestors *");
    headers.delete("x-frame-options");
    return new Response(assetResponse.body, {
      status: assetResponse.status,
      statusText: assetResponse.statusText,
      headers,
    });
  },
};
