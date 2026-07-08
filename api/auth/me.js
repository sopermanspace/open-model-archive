import {
  getBearerToken,
  getSessionSecret,
  verifyJwt,
} from "../_lib/auth.js";
import { applyCors, handleOptions } from "../_lib/cors.js";

export default function handler(req, res) {
  if (handleOptions(req, res)) return;
  applyCors(req, res);

  const secret = getSessionSecret();
  const token = getBearerToken(req);
  const payload = verifyJwt(token, secret);

  if (!payload) {
    res.status(401).json({ authenticated: false });
    return;
  }

  res.status(200).json({
    authenticated: true,
    user: {
      id: payload.sub,
      login: payload.login,
      avatar_url: payload.avatar_url,
    },
  });
}