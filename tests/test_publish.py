"""Unit tests for publish service — no external services required."""
import os
import pytest
from datetime import date

os.environ.setdefault("GITHUB_TOKEN", "test")
os.environ.setdefault("GITHUB_REPO_OWNER", "test")
os.environ.setdefault("GITHUB_REPO_NAME", "test")


class TestSlugify:
    def test_basic_ascii(self):
        from app.api.routes.publish import slugify
        assert slugify("Hello World") == "hello-world"

    def test_korean_stripped(self):
        from app.api.routes.publish import slugify
        result = slugify("한국어 테스트")
        assert result == "untitled"

    def test_special_chars_replaced(self):
        from app.api.routes.publish import slugify
        assert slugify("foo!@#bar") == "foo-bar"

    def test_leading_trailing_hyphens_stripped(self):
        from app.api.routes.publish import slugify
        assert slugify("  hello  ") == "hello"

    def test_empty_falls_back_to_untitled(self):
        from app.api.routes.publish import slugify
        assert slugify("") == "untitled"
        assert slugify("!!!") == "untitled"


class TestMakeMdxFrontmatter:
    def test_required_fields_present(self):
        from app.api.routes.publish import make_mdx_frontmatter
        result = make_mdx_frontmatter(
            title="Test Album",
            slug="test-album",
            description="",
            posted_date=date(2026, 5, 23),
            category="music",
            album_ids=["abc123"],
            artist_ids=["art1"],
            post_id="post-1",
        )
        assert "title: 'Test Album'" in result
        assert "slug: 'test-album'" in result
        assert "date: 2026-05-23" in result
        assert "category: 'music'" in result
        assert "draft: false" in result

    def test_rating_and_scale_included(self):
        from app.api.routes.publish import make_mdx_frontmatter
        result = make_mdx_frontmatter(
            title="Rated",
            slug="rated",
            description="",
            posted_date=date(2026, 5, 23),
            category=None,
            album_ids=[],
            artist_ids=[],
            post_id="p1",
            rating=4.5,
            rating_scale=5,
        )
        assert "rating: 4.5" in result
        assert "ratingScale: 5" in result

    def test_null_category_defaults_to_default(self):
        from app.api.routes.publish import make_mdx_frontmatter
        result = make_mdx_frontmatter(
            title="No Cat",
            slug="no-cat",
            description="",
            posted_date=date(2026, 5, 23),
            category=None,
            album_ids=[],
            artist_ids=[],
            post_id="p2",
        )
        assert "category: 'default'" in result

    def test_starts_and_ends_with_frontmatter_delimiter(self):
        from app.api.routes.publish import make_mdx_frontmatter
        result = make_mdx_frontmatter(
            title="T",
            slug="t",
            description="",
            posted_date=date(2026, 5, 23),
            category="x",
            album_ids=[],
            artist_ids=[],
            post_id="p3",
        )
        lines = result.strip().split("\n")
        assert lines[0] == "---"
        assert lines[-1] == "---"
