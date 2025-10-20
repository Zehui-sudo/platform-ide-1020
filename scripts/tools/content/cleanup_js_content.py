#!/usr/bin/env python3
"""
Clean up JS knowledge content files based on output/index.md.

Deletes web-learner/public/content/js-sec-*.md files whose js-sec-<d>-<d>-<d>
ID is not present in output/index.md, and also deletes files that do not have
three numeric segments at all.

Usage:
  python scripts/cleanup_js_content.py \
    --content web-learner/public/content \
    --index output/index.md
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ID_3_RE = re.compile(r"js-sec-(\d+)-(\d+)-(\d+)")
ID_IN_INDEX = re.compile(r"\[(js-sec-\d+-\d+-\d+)\]")


def load_allowed_ids(index_path: Path) -> set[str]:
    text = index_path.read_text(encoding="utf-8")
    return set(ID_IN_INDEX.findall(text))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--content", default="web-learner/public/content", help="Directory of JS content files")
    ap.add_argument("--index", default="output/index.md", help="Path to index.md with allowed IDs")
    args = ap.parse_args()

    content_dir = Path(args.content)
    index_path = Path(args.index)

    if not index_path.exists():
        raise SystemExit(f"Index file not found: {index_path}")

    allowed = load_allowed_ids(index_path)
    to_delete: list[Path] = []

    for md in sorted(content_dir.glob("js-sec-*.md")):
        m = ID_3_RE.search(md.name)
        if not m:
            to_delete.append(md)
            continue
        _id = m.group(0)
        if _id not in allowed:
            to_delete.append(md)

    for path in to_delete:
        path.unlink(missing_ok=True)

    print(f"Allowed IDs loaded: {len(allowed)}")
    print(f"Deleted files: {len(to_delete)}")
    for p in to_delete[:20]:
        print(f" - {p}")


if __name__ == "__main__":
    main()
