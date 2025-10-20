#!/usr/bin/env python3
"""
Extract code examples from knowledge Markdown files into JSONL.

Scans `web-learner/public/content` for Markdown files, extracts fenced code
blocks (```lang or ```lang:interactive), and writes one JSON object per block
with: id, title, code, lang, source, blockIndex.

Usage:
  python scripts/extract_code_examples.py \
    --input web-learner/public/content \
    --output code-examples.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable, Optional, Tuple


FENCE_RE = re.compile(
    r"```([A-Za-z0-9_+\-]+)(?::interactive)?\n([\s\S]*?)\n```",
    re.MULTILINE,
)

# Extracts first occurrence of js-sec-<d>-<d>-<d> anywhere in filename
ID_ANYWHERE_RE = re.compile(r"js-sec-(\d+)-(\d+)-(\d+)")
ID_TWO_DIGITS_RE = re.compile(r"js-sec-(\d+)-(\d+)\b")

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def extract_title(md: str) -> Optional[str]:
    # Prefer first level-2 heading `## Title`, fall back to first `# Title`
    for pat in (r"^##\s+(.+)$", r"^#\s+(.+)$"):
        m = re.search(pat, md, flags=re.MULTILINE)
        if m:
            return m.group(1).strip()
    return None


def extract_id_from_filename(name: str) -> Optional[str]:
    # Normalize to js-sec-x-x-x by taking the first 3 numeric segments present
    m = ID_ANYWHERE_RE.search(name)
    if m:
        a, b, c = m.groups()
        return f"js-sec-{a}-{b}-{c}"
    # If only two digits exist, coerce to -0 as the third segment
    m2 = ID_TWO_DIGITS_RE.search(name)
    if m2:
        a, b = m2.groups()
        return f"js-sec-{a}-{b}-0"
    return None


def iter_code_blocks(md: str) -> Iterable[Tuple[str, str]]:
    """Yield (lang, code) for each fenced code block."""
    for m in FENCE_RE.finditer(md):
        lang = m.group(1).lower()
        code = m.group(2)
        yield (lang, code)


def load_allowed_ids(index_path: Path) -> Optional[set[str]]:
    """Load allowed js-sec-*-*-* IDs from an index.md if it exists."""
    if not index_path.exists():
        return None
    text = index_path.read_text(encoding="utf-8")
    ids = set(re.findall(r"\[(js-sec-\d+-\d+-\d+)\]", text))
    return ids if ids else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="web-learner/public/content", help="Input directory to scan")
    ap.add_argument("--output", default="code-examples.jsonl", help="Output JSONL file path")
    ap.add_argument("--index", default="output/index.md", help="Optional index.md to filter allowed IDs")
    args = ap.parse_args()

    in_dir = Path(args.input)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    count_files = 0
    count_blocks = 0

    allowed = load_allowed_ids(Path(args.index))

    with out_path.open("w", encoding="utf-8") as out:
        # Only process JavaScript knowledge files
        for md_path in sorted(in_dir.glob("js-sec-*.md")):
            count_files += 1
            md_text = read_text(md_path)
            title = extract_title(md_text) or md_path.stem
            _id = extract_id_from_filename(md_path.name) or md_path.stem

            if allowed is not None and _id not in allowed:
                continue

            block_index = 0
            for lang, code in iter_code_blocks(md_text):
                obj = {
                    "id": _id,
                    "title": title,
                    "code": code,
                    "lang": lang,
                    "source": str(md_path.as_posix()),
                    "blockIndex": block_index,
                }
                out.write(json.dumps(obj, ensure_ascii=False) + "\n")
                block_index += 1
                count_blocks += 1

    print(f"Processed files: {count_files}")
    print(f"Extracted code blocks: {count_blocks}")
    print(f"Output written to: {out_path}")


if __name__ == "__main__":
    main()
