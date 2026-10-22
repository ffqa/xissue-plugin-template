#!/usr/bin/env node
let raw = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => (raw += chunk));
process.stdin.on("end", () => {
  let payload;
  try {
    payload = JSON.parse(raw);
  } catch (error) {
    console.error(`invalid stdin JSON: ${error.message}`);
    process.exit(1);
  }
  const notification = payload.notification || {};
  const message = `[${payload.event}] ${notification.title || "notification"}`;
  process.stdout.write(JSON.stringify({ actions: [{ type: "notify", message }] }));
});
