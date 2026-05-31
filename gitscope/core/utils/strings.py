"""String helpers."""

from __future__ import annotations

import re


def contributor_key(name: str, email: str) -> str:
    """Normalize contributor identity for aggregation."""

    return f"{name.strip().lower()}<{email.strip().lower()}>"


def file_extension(path: str) -> str | None:
    """Return the lowercase file extension without the leading dot."""

    if "." not in path.rsplit("/", maxsplit=1)[-1]:
        return None
    return path.rsplit(".", maxsplit=1)[-1].lower()


def slugify(value: str) -> str:
    """Build a stable identifier from display text."""

    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return slug.strip("-") or "item"
