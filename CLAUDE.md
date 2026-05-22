# myblog_publish

FastAPI publish service deployed as AWS Lambda via Mangum. Receives a post payload and writes MDX files directly to a GitHub repository via the GitHub Contents API.

## Stack

- **Runtime**: Python 3.12, FastAPI, Mangum (Lambda adapter)
- **No database** — stateless; reads `GITHUB_TOKEN` from env and calls GitHub API
- **Deploy**: `build_zip.sh` → zip

## Structure

```
app/
├── main.py                  ← FastAPI app, CORS, edge_guard middleware
└── api/routes/publish.py    ← POST /api/publish (CreatePostReq → GitHub)
```

## Route

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/publish` | Write MDX frontmatter + body to GitHub repo |
| GET | `/health` | Health check |

## Request Schema (`CreatePostReq`)

| Field | Type | Notes |
|-------|------|-------|
| `title` | `str` | required, min 1 char |
| `body_mdx` | `str \| None` | post body |
| `slug` | `str \| None` | auto-generated from title if omitted |
| `category` | `str \| None` | defaults to `"default"` |
| `description` | `str` | defaults to `""` |
| `posted_date` | `date` | ISO date |
| `album_ids` | `list[str]` | Spotify album IDs |
| `artist_ids` | `list[str]` | Spotify artist IDs |
| `post_id` | `str \| None` | DB post UUID for cross-referencing |
| `album_cover_url` | `str \| None` | |
| `rating` | `float \| None` | `0–5` |
| `rating_scale` | `int` | default `5` |

## MDX Frontmatter

Generated fields in output `.mdx` files:
```yaml
---
title: '...'
slug: '...'
description: '...'
date: YYYY-MM-DD
category: '...'
draft: false
albumIds: [...]
artistIds: [...]
postId: '...'
albumCover: '...'
rating: 4.5
ratingScale: 5
---
```

## Security

All requests to `/api/publish` must include `x-origin-verify: <EDGE_SECRET>`.  
`APP_ENV=dev` bypasses this guard.

`request.client` may be `None` in Lambda+API Gateway — always guard with:
```python
client_ip = request.client.host if request.client else "unknown"
```

## Config

```
APP_ENV=dev|prod
FRONT_ORIGIN=https://...
EDGE_SECRET=<shared secret with CloudFront>
GITHUB_TOKEN=ghp_...
GITHUB_OWNER=...
GITHUB_REPO=...
GITHUB_BRANCH=main
```

## Hard Rules

- **Never log `GITHUB_TOKEN`** — it grants write access to the content repo.
- **Never work directly on `main`** — branch from `main`, PR back.

## Running Locally

```bash
pip install -r requirements.txt
APP_ENV=dev uvicorn app.main:app --reload --port 9000
```

## Verification

```bash
python -c "from app.main import app; print('import ok')"
```
