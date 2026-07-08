import crypto from "crypto";

const TOKEN_TTL_SECONDS = 7 * 24 * 60 * 60;

function base64url(data) {
  return Buffer.from(data).toString("base64url");
}

export function signJwt(payload, secret, expiresIn = TOKEN_TTL_SECONDS) {
  const header = { alg: "HS256", typ: "JWT" };
  const now = Math.floor(Date.now() / 1000);
  const body = { ...payload, iat: now, exp: now + expiresIn };
  const encodedHeader = base64url(JSON.stringify(header));
  const encodedPayload = base64url(JSON.stringify(body));
  const signature = crypto
    .createHmac("sha256", secret)
    .update(`${encodedHeader}.${encodedPayload}`)
    .digest("base64url");
  return `${encodedHeader}.${encodedPayload}.${signature}`;
}

export function verifyJwt(token, secret) {
  if (!token || !secret) return null;
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  const [encodedHeader, encodedPayload, signature] = parts;
  const expected = crypto
    .createHmac("sha256", secret)
    .update(`${encodedHeader}.${encodedPayload}`)
    .digest("base64url");
  if (signature !== expected) return null;
  try {
    const payload = JSON.parse(
      Buffer.from(encodedPayload, "base64url").toString("utf8"),
    );
    if (!payload.exp || payload.exp < Math.floor(Date.now() / 1000)) {
      return null;
    }
    return payload;
  } catch {
    return null;
  }
}

export function getBearerToken(req) {
  const header = req.headers.authorization || req.headers.Authorization;
  if (!header || !header.startsWith("Bearer ")) return null;
  return header.slice(7).trim();
}

export function getSessionSecret() {
  return process.env.SESSION_SECRET || "";
}

export function getOAuthConfig() {
  return {
    clientId: process.env.GITHUB_OAUTH_CLIENT_ID || "",
    clientSecret: process.env.GITHUB_OAUTH_CLIENT_SECRET || "",
    callbackUrl:
      process.env.GITHUB_OAUTH_CALLBACK_URL ||
      "https://open-model-archive.vercel.app/api/auth/callback",
  };
}

export function encodeState(returnTo) {
  return base64url(JSON.stringify({ returnTo }));
}

export function decodeState(state) {
  if (!state) return null;
  try {
    return JSON.parse(Buffer.from(state, "base64url").toString("utf8"));
  } catch {
    return null;
  }
}

export function buildGitHubAuthorizeUrl(returnTo) {
  const { clientId, callbackUrl } = getOAuthConfig();
  const params = new URLSearchParams({
    client_id: clientId,
    redirect_uri: callbackUrl,
    scope: "read:user",
    state: encodeState(returnTo),
  });
  return `https://github.com/login/oauth/authorize?${params.toString()}`;
}

export async function exchangeGitHubCode(code) {
  const { clientId, clientSecret, callbackUrl } = getOAuthConfig();
  const tokenRes = await fetch(
    "https://github.com/login/oauth/access_token",
    {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        client_id: clientId,
        client_secret: clientSecret,
        code,
        redirect_uri: callbackUrl,
      }),
    },
  );
  if (!tokenRes.ok) {
    throw new Error("GitHub token exchange failed");
  }
  const tokenData = await tokenRes.json();
  if (!tokenData.access_token) {
    throw new Error(tokenData.error || "Missing access token");
  }

  const userRes = await fetch("https://api.github.com/user", {
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${tokenData.access_token}`,
      "User-Agent": "open-model-archive",
    },
  });
  if (!userRes.ok) {
    throw new Error("GitHub user fetch failed");
  }
  return userRes.json();
}