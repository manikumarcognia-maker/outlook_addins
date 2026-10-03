import type { Context, Next } from "hono";

/** Outlook task pane runs in an iframe; allow framing and simple CORS for API. */
export async function outlookResponseHeaders(c: Context, next: Next) {
  await next();
  c.res.headers.set("Access-Control-Allow-Origin", "*");
  c.res.headers.set("Content-Security-Policy", "frame-ancestors *");
  c.res.headers.delete("x-frame-options");
}

export async function handleOptions(c: Context) {
  return new Response(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization",
      "Access-Control-Max-Age": "86400",
    },
  });
}
