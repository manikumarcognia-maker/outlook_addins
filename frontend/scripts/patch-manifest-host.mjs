import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");
const source = path.join(root, "manifest.xml");
const target = path.join(root, "manifest.owa-tunnel.xml");

const publicBase = process.argv[2]?.replace(/\/$/, "");
if (!publicBase || !/^https:\/\//.test(publicBase)) {
  console.error("Usage: node scripts/patch-manifest-host.mjs https://your-tunnel.trycloudflare.com");
  process.exit(1);
}

const local = "https://localhost:3000";
let xml = fs.readFileSync(source, "utf8");
if (!xml.includes(local)) {
  console.error(`Source manifest does not contain ${local}`);
  process.exit(1);
}

xml = xml.replaceAll(local, publicBase);
fs.writeFileSync(target, xml, "utf8");
console.log(`Wrote ${target}`);
console.log(`Sideload manifest.owa-tunnel.xml in https://aka.ms/olksideload`);
