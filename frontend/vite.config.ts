import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import fs from "node:fs";
import path from "node:path";

const certDir = path.join(process.env.USERPROFILE || process.env.HOME || "", ".office-addin-dev-certs");
const certPath = path.join(certDir, "localhost.crt");
const keyPath = path.join(certDir, "localhost.key");
const caPath = path.join(certDir, "ca.crt");
const hasCerts = fs.existsSync(certPath) && fs.existsSync(keyPath);

export default defineConfig({
  plugins: [react()],
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
