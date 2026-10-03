import { execSync } from "node:child_process";

const port = process.argv[2] || "3000";
const out = execSync(`netstat -ano | findstr ":${port}" | findstr LISTENING`, {
  encoding: "utf8",
  stdio: ["pipe", "pipe", "ignore"],
}).trim();

if (!out) {
  console.log(`No process listening on port ${port}.`);
  process.exit(0);
}

const pids = new Set();
for (const line of out.split(/\r?\n/)) {
  const parts = line.trim().split(/\s+/);
  const pid = parts[parts.length - 1];
  if (pid && /^\d+$/.test(pid)) pids.add(pid);
}

for (const pid of pids) {
  try {
    execSync(`taskkill /PID ${pid} /F`, { stdio: "inherit" });
    console.log(`Stopped PID ${pid} (was using port ${port}).`);
  } catch {
    console.error(`Could not stop PID ${pid}. Run terminal as admin or close that window.`);
    process.exit(1);
  }
}
