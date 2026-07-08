import {
  decodeState,
  exchangeGitHubCode,
  getOAuthConfig,
  getSessionSecret,
  signJwt,
} from "../_lib/auth.js";

const DEFAULT_RETURN =
  "https://sopermanspace.github.io/open-model-archive/";

export default async function handler(req, res) {
  const { clientId, clientSecret } = getOAuthConfig();
  const secret = getSessionSecret();

  if (!clientId || !clientSecret || !secret) {
    res.status(503).send("OAuth is not configured");
    return;
  }

  const { code, state, error } = req.query;
  if (error) {
    res.status(400).send(`GitHub authorization failed: ${error}`);
    return;
  }
  if (!code) {
    res.status(400).send("Missing authorization code");
    return;
  }

  const parsed = decodeState(state);
  const returnTo = parsed?.returnTo || DEFAULT_RETURN;

  try {
    const user = await exchangeGitHubCode(code);
    const token = signJwt(
      {
        sub: String(user.id),
        login: user.login,
        avatar_url: user.avatar_url,
      },
      secret,
    );

    const redirectUrl = new URL(returnTo);
    redirectUrl.searchParams.set("oma_auth", "1");
    redirectUrl.hash = `oma_token=${encodeURIComponent(token)}`;
    res.redirect(302, redirectUrl.toString());
  } catch (err) {
    res.status(500).send("Authentication failed");
  }
}