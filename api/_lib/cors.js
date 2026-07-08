const ALLOWED_ORIGINS = new Set([
  "https://sopermanspace.github.io",
  "http://localhost:3000",
  "http://127.0.0.1:3000",
  "http://localhost:4173",
  "http://127.0.0.1:4173",
]);

export function applyCors(req, res) {
  const origin = req.headers.origin;
  if (origin && ALLOWED_ORIGINS.has(origin)) {
    res.setHeader("Access-Control-Allow-Origin", origin);
    res.setHeader("Vary", "Origin");
  }
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader(
    "Access-Control-Allow-Headers",
    "Authorization, Content-Type",
  );
  res.setHeader("Access-Control-Max-Age", "86400");
}

export function handleOptions(req, res) {
  if (req.method === "OPTIONS") {
    applyCors(req, res);
    res.status(204).end();
    return true;
  }
  return false;
}