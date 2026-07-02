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