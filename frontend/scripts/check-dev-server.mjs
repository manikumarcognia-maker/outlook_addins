import https from "node:https";

const url = "https://localhost:3000/assets/icon-32.png";

https
  .get(url, { rejectUnauthorized: false }, (res) => {
    if (res.statusCode === 200) {
      console.log("OK — dev server is up (icon-32.png returned 200).");
      process.exit(0);
    }
    console.error(`FAIL — ${url} returned HTTP ${res.statusCode}. Is npm run dev running?`);
    process.exit(1);
  })
  .on("error", (err) => {
    console.error("FAIL — cannot reach https://localhost:3000");
    console.error(err.message);
    console.error("Start: cd frontend && npm run dev");
    process.exit(1);
  });
