import { buildGitHubAuthorizeUrl, getOAuthConfig } from "../_lib/auth.js";

const DEFAULT_RETURN =
  "https://sopermanspace.github.io/open-model-archive/";

export default function handler(req, res) {
  const { clientId } = getOAuthConfig();
  if (!clientId) {
    res.status(503).json({ error: "GitHub OAuth is not configured" });
    return;
  }

  const returnTo = req.query.return_to || DEFAULT_RETURN;
  res.redirect(302, buildGitHubAuthorizeUrl(returnTo));
}