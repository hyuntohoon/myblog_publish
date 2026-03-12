from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import date
import base64
import re
import os
import json
import requests

router = APIRouter()


class CreatePostReq(BaseModel):
    title: str = Field(min_length=1)
    body_mdx: str = Field(min_length=1)
    category: str | None = None
    description: str = ""
    posted_date: date

    slug: str | None = None
    post_id: str | None = None

    album_ids: list[str] = Field(default_factory=list)
    artist_ids: list[str] = Field(default_factory=list)

    # ✅ 단일 대표 커버
    album_cover_url: str | None = None

    # ✅ 평점
    rating: float | None = None


def slugify(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s or "untitled"


def make_mdx_frontmatter(
        title: str,
        slug: str,
        description: str,
        posted_date: date,
        category: str | None,
        album_ids: list[str],
        artist_ids: list[str],
        post_id: str,
        album_cover_url: str | None = None,
        rating: float | None = None,
) -> str:
    cat = (category or "default").strip() or "default"

    return "\n".join(
        [
            "---",
            f"title: {title!r}",
            f"slug: {slug!r}",
            f"description: {(description or '')!r}",
            f"date: {posted_date.isoformat()}",
            f"category: {cat!r}",
            "draft: false",
            f"albumIds: {json.dumps(album_ids or [], ensure_ascii=False)}",
            f"artistIds: {json.dumps(artist_ids or [], ensure_ascii=False)}",
            f"postId: {post_id!r}",
            f"albumCover: {json.dumps(album_cover_url or '', ensure_ascii=False)}",
            f"rating: {rating if rating is not None else 'null'}",
            "---",
            "",
        ]
    )


def github_put_file(owner: str, repo: str, branch: str, path: str, content_utf8: str, token: str):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "publisher-fastapi",
        "Content-Type": "application/json",
    }

    r_get = requests.get(url, headers=headers, params={"ref": branch})
    sha = r_get.json().get("sha") if r_get.status_code == 200 else None

    payload = {
        "message": f"chore(post): create or update '{os.path.basename(path)}'",
        "content": base64.b64encode(content_utf8.encode("utf-8")).decode("utf-8"),
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha

    return requests.put(url, headers=headers, data=json.dumps(payload))


@router.post("")
def create_post(req: CreatePostReq):
    slug = req.slug or slugify(req.title)
    base_dir = os.getenv("CONTENT_DIR", "content/blog")
    path = f"{base_dir}/{req.posted_date.isoformat()}--{slug}/index.mdx"

    mdx = (
            make_mdx_frontmatter(
                title=req.title,
                slug=slug,
                description=req.description,
                posted_date=req.posted_date,
                category=req.category,
                album_ids=req.album_ids,
                artist_ids=req.artist_ids,
                post_id=req.post_id or "",
                album_cover_url=req.album_cover_url,
                rating=req.rating,
            )
            + req.body_mdx.strip()
            + "\n"
    )

    owner = os.getenv("GITHUB_REPO_OWNER")
    repo = os.getenv("GITHUB_REPO_NAME")
    branch = os.getenv("GITHUB_REPO_BRANCH", "main")
    token = os.getenv("GITHUB_TOKEN")

    if not all([owner, repo, token]):
        raise HTTPException(
            500, detail="Missing GitHub environment variables (owner/repo/token)"
        )

    r = github_put_file(owner, repo, branch, path, mdx, token)
    if r.status_code not in (200, 201):
        raise HTTPException(
            r.status_code, detail=f"GitHub API error: {r.text[:500]}"
        )

    return {
        "ok": True,
        "slug": slug,
        "path": path,
        "github_url": f"https://github.com/{owner}/{repo}/blob/{branch}/{path}",
    }