import {
  getBearerToken,
  getSessionSecret,
  verifyJwt,
} from "../_lib/auth.js";
import { applyCors, handleOptions } from "../_lib/cors.js";
import { aggregateVotes, loadVotes, saveVote } from "../_lib/storage.js";

export default async function handler(req, res) {
  if (handleOptions(req, res)) return;
  applyCors(req, res);

  try {
    if (req.method === "GET") {
      const { votes } = await loadVotes();
      const category = req.query.category || null;
      const stats = aggregateVotes(votes, category);

      const secret = getSessionSecret();
      const token = getBearerToken(req);
      const payload = verifyJwt(token, secret);
      let userVote = null;
      if (payload && category) {
        userVote =
          votes.find(
            (vote) =>
              String(vote.github_user_id) === payload.sub &&
              vote.category === category,
          ) || null;
      }

      res.status(200).json({ ...stats, user_vote: userVote });
      return;
    }

    if (req.method === "POST") {
      const secret = getSessionSecret();
      const token = getBearerToken(req);
      const payload = verifyJwt(token, secret);
      if (!payload) {
        res.status(401).json({ error: "Sign in with GitHub to vote" });
        return;
      }

      const body =
        typeof req.body === "string" ? JSON.parse(req.body) : req.body;
      const { category, task_slug, model_id, reaction } = body || {};

      if (!category || !task_slug || !model_id) {
        res.status(400).json({ error: "Missing vote fields" });
        return;
      }
      if (reaction !== "like" && reaction !== "dislike") {
        res.status(400).json({ error: "Reaction must be like or dislike" });
        return;
      }

      const nextVotes = await saveVote({
        githubUserId: payload.sub,
        githubLogin: payload.login,
        category,
        taskSlug: task_slug,
        modelId: model_id,
        reaction,
      });

      const stats = aggregateVotes(nextVotes, category);
      const userVote =
        nextVotes.find(
          (vote) =>
            String(vote.github_user_id) === payload.sub &&
            vote.category === category,
        ) || null;

      res.status(200).json({ ...stats, user_vote: userVote });
      return;
    }

    res.status(405).json({ error: "Method not allowed" });
  } catch (err) {
    res.status(500).json({ error: "Vote service unavailable" });
  }
}