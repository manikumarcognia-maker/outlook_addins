import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import fs from "node:fs";
import path from "node:path";

const certDir = path.join(process.env.USERPROFILE || process.env.HOME || "", ".office-addin-dev-certs");
const certPath = path.join(certDir, "localhost.crt");
const keyPath = path.join(certDir, "localhost.key");
const caPath = path.join(certDir, "ca.crt");
const hasCerts = fs.existsSync(certPath) && fs.existsSync(keyPath);

/** Outlook on the web must access https://localhost (Private Network Access). */
function privateNetworkAccess(): Plugin {
  return {
    name: "private-network-access",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        res.setHeader("Access-Control-Allow-Private-Network", "true");
        if (req.method === "OPTIONS") {
          res.setHeader("Access-Control-Allow-Origin", "*");
          res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
          res.setHeader("Access-Control-Allow-Headers", "*");
          res.statusCode = 204;
          res.end();
          return;
        }
        next();
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), privateNetworkAccess()],
  base: "./",
  build: {
    outDir: "dist",
    emptyOutDir: true,
    rollupOptions: {
      input: {
        taskpane: path.resolve(__dirname, "index.html"),
        commands: path.resolve(__dirname, "commands.html"),
        admin: path.resolve(__dirname, "admin.html"),
      },
    },
  },
  server: {
    // Bind IPv4 + IPv6 — Vite default [::1]-only breaks clients that use 127.0.0.1.
    host: true,
    port: 3000,
    strictPort: true,
    https: hasCerts
      ? {
          cert: fs.readFileSync(certPath),
          key: fs.readFileSync(keyPath),
          ...(fs.existsSync(caPath) ? { ca: fs.readFileSync(caPath) } : {}),
        }
      : undefined,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Private-Network": "true",
    },
    proxy: {
      "/api": {
        target: "http://localhost:4000",
        changeOrigin: true,
      },
      "/health": {
        target: "http://localhost:4000",
        changeOrigin: true,
      },
    },
  },
});
