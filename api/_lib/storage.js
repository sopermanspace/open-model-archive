import { get, head, put } from "@vercel/blob";

const DEFAULT_REPO = "sopermanspace/open-model-archive";
const VOTES_PATH = "data/votes.json";
const BLOB_KEY = "community/votes.json";

function getRepo() {
  return process.env.GITHUB_REPO || DEFAULT_REPO;
}

function getGitHubToken() {
  return process.env.GITHUB_TOKEN || "";
}

function githubHeaders() {
  const token = getGitHubToken();
  return {
    Accept: "application/vnd.github+json",
    "User-Agent": "open-model-archive",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

function hasBlobStorage() {
  return Boolean(
    process.env.BLOB_READ_WRITE_TOKEN ||
      (process.env.VERCEL_OIDC_TOKEN && process.env.BLOB_STORE_ID),
  );
}

async function readFromBlob() {
  try {
    const meta = await head(BLOB_KEY, { access: "private" });
    if (!meta) {
      return { votes: [] };
    }

    const blob = await get(meta.url, { access: "private" });
    if (!blob || !blob.stream) {
      return { votes: [] };
    }

    const text = await new Response(blob.stream).text();
    const content = JSON.parse(text);
    return { votes: content.votes || [] };
  } catch (err) {
    if (err instanceof Error && /not found/i.test(err.message)) {
      return { votes: [] };
    }
    throw err;
  }
}

async function writeToBlob(votes) {
  await put(BLOB_KEY, JSON.stringify({ votes }, null, 2), {
    access: "private",
    addRandomSuffix: false,
    allowOverwrite: true,
    contentType: "application/json",
  });
}

async function readFromGitHub() {
  const [owner, repo] = getRepo().split("/");
  const url = `https://api.github.com/repos/${owner}/${repo}/contents/${VOTES_PATH}`;
  const res = await fetch(url, { headers: githubHeaders() });
  if (res.status === 404) {
    return { votes: [], sha: null };
  }
  if (!res.ok) {
    throw new Error(`GitHub read failed (${res.status})`);
  }
  const data = await res.json();
  const content = JSON.parse(
    Buffer.from(data.content, "base64").toString("utf8"),
  );
  return { votes: content.votes || [], sha: data.sha };
}

async function writeToGitHub(votes, sha) {
  const token = getGitHubToken();
  if (!token) {
    throw new Error("GitHub vote storage is not configured");
  }
  const [owner, repo] = getRepo().split("/");
  const url = `https://api.github.com/repos/${owner}/${repo}/contents/${VOTES_PATH}`;
  const body = {
    message: "Update community votes",
    content: Buffer.from(JSON.stringify({ votes }, null, 2)).toString("base64"),
    ...(sha ? { sha } : {}),
  };
  const res = await fetch(url, {
    method: "PUT",
    headers: {
      ...githubHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`GitHub write failed (${res.status}): ${err}`);
  }
  return res.json();
}

export async function loadVotes() {
  if (hasBlobStorage()) {
    return readFromBlob();
  }
  return readFromGitHub();
}

async function persistVotes(votes) {
  if (hasBlobStorage()) {
    await writeToBlob(votes);
    return;
  }

  const maxAttempts = 3;
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const { sha } = await readFromGitHub();
    try {
      await writeToGitHub(votes, sha);
      return;
    } catch (err) {
      if (attempt === maxAttempts - 1) throw err;
    }
  }
}

export async function saveVote({
  githubUserId,
  githubLogin,
  category,
  taskSlug,
  modelId,
  reaction,
}) {
  if (!hasBlobStorage() && !getGitHubToken()) {
    throw new Error("Vote storage is not configured");
  }

  const { votes } = await loadVotes();
  const userId = String(githubUserId);
  const filtered = votes.filter(
    (vote) =>
      !(
        String(vote.github_user_id) === userId &&
        vote.category === category
      ),
  );

  const nextVote = {
    github_user_id: Number(githubUserId),
    github_login: githubLogin,
    category,
    task_slug: taskSlug,
    model_id: modelId,
    reaction,
    updated_at: new Date().toISOString(),
  };

  const existing = votes.find(
    (vote) =>
      String(vote.github_user_id) === userId &&
      vote.category === category &&
      vote.model_id === modelId &&
      vote.reaction === reaction,
  );

  const nextVotes = existing ? filtered : [...filtered, nextVote];
  await persistVotes(nextVotes);
  return nextVotes;
}

export function aggregateVotes(votes, category) {
  const scoped = category
    ? votes.filter((vote) => vote.category === category)
    : votes;

  const byModel = {};
  for (const vote of scoped) {
    const key = `${vote.category}::${vote.model_id}`;
    if (!byModel[key]) {
      byModel[key] = {
        category: vote.category,
        model_id: vote.model_id,
        likes: 0,
        dislikes: 0,
      };
    }
    if (vote.reaction === "like") byModel[key].likes += 1;
    if (vote.reaction === "dislike") byModel[key].dislikes += 1;
  }

  const byCategory = {};
  for (const vote of scoped) {
    if (!byCategory[vote.category]) {
      byCategory[vote.category] = { likes: {}, dislikes: {} };
    }
    const bucket = byCategory[vote.category];
    const modelId = vote.model_id;
    if (vote.reaction === "like") {
      bucket.likes[modelId] = (bucket.likes[modelId] || 0) + 1;
    }
    if (vote.reaction === "dislike") {
      bucket.dislikes[modelId] = (bucket.dislikes[modelId] || 0) + 1;
    }
  }

  const topByCategory = {};
  for (const [cat, counts] of Object.entries(byCategory)) {
    const topLike = Object.entries(counts.likes).sort((a, b) => b[1] - a[1])[0];
    const topDislike = Object.entries(counts.dislikes).sort(
      (a, b) => b[1] - a[1],
    )[0];
    topByCategory[cat] = {
      top_liked: topLike
        ? { model_id: topLike[0], count: topLike[1] }
        : null,
      top_disliked: topDislike
        ? { model_id: topDislike[0], count: topDislike[1] }
        : null,
      totals: counts,
    };
  }

  return {
    models: Object.values(byModel),
    categories: topByCategory,
    total_votes: scoped.length,
  };
}