import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const distIndex = path.join(__dirname, "..", "..", "frontend", "dist", "index.html");

if (!fs.existsSync(distIndex)) {
  console.error("Missing frontend/dist/index.html — run: npm run build:frontend");
  process.exit(1);
}

const html = fs.readFileSync(distIndex, "utf8");
if (html.includes("/src/main.tsx") || html.includes('src="/src/')) {
  console.error(
    "frontend/dist/index.html still references dev sources (/src/main.tsx). " +
      "Run npm run build in frontend/ and deploy again — do not upload frontend/ source to Workers."
  );
  process.exit(1);
}

if (!html.includes("/assets/") && !html.includes("./assets/")) {
  console.error("frontend/dist/index.html has no bundled ./assets/ scripts — Vite build may have failed.");
  process.exit(1);
}

console.log("OK: production dist looks bundled.");
