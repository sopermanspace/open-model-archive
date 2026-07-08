# Deployment Guide

The site deploys to **GitHub Pages** from the `docs/` directory on `main`.

## Automatic deployment

1. Push to `main`
2. The `Deploy GitHub Pages` workflow builds the site and publishes `docs/`
3. Enable Pages in repository settings: **Source → GitHub Actions**

## Manual deployment

```bash
uv run oma build          # run models + generate site
git add runs/ docs/
git commit -m "Publish latest runs"
git push origin main
```

## Custom domain (optional)

Add a `CNAME` file in `docs/` and configure DNS with your registrar.

## CI without model execution

Pull request CI runs `oma build --skip-run` to validate schemas and regenerate the site from committed runs. Model execution happens locally or in a trusted environment with provider access.

## Community votes (GitHub OAuth)

The static site on GitHub Pages calls a small Vercel API for sign-in and vote storage.

### GitHub OAuth App

Create an OAuth App at [GitHub Developer Settings](https://github.com/settings/developers):

| Field | Value |
|-------|-------|
| **Authorization callback URL** | `https://open-model-archive.vercel.app/api/auth/callback` |
| Homepage URL | `https://sopermanspace.github.io/open-model-archive/` |

Copy the Client ID and generate a Client Secret — store both in Vercel environment variables only.

### Vercel environment variables

Set these in the Vercel project dashboard (never commit to Git):

| Variable | Purpose |
|----------|---------|
| `GITHUB_OAUTH_CLIENT_ID` | OAuth app client ID |
| `GITHUB_OAUTH_CLIENT_SECRET` | OAuth app client secret |
| `GITHUB_OAUTH_CALLBACK_URL` | `https://open-model-archive.vercel.app/api/auth/callback` |
| `SESSION_SECRET` | Random string for signing session tokens (32+ chars) |
| `GITHUB_TOKEN` | PAT or fine-grained token with `contents: write` on `data/votes.json` |
| `GITHUB_REPO` | `sopermanspace/open-model-archive` (optional, this is the default) |

Deploy the API with:

```bash
vercel --prod --yes
```

### How voting works

- Users sign in with GitHub on any comparison page.
- Small like/dislike icons appear at the bottom of each model column.
- **One vote per category per user** — liking a different model in the same category replaces the previous pick.
- Votes are stored in `data/votes.json` via the GitHub Contents API.
- Aggregated picks appear on the homepage under **Community picks**.