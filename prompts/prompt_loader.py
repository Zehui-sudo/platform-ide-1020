#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Lightweight prompt loader for Markdown catalogs.

Convention:
- File: prompts/prompt_catalog.md
- Each prompt is defined under an H3 header line: `### <key>`
- Immediately followed by a fenced code block (``` ... ```). The code block
  content is the prompt text. The info string after ``` is ignored.

Example:
  ### reconstruct.classify_subject
  ```text
  ... prompt content ...
  ```

Usage:
  from prompts.prompt_loader import get_prompt
  text = get_prompt('reconstruct.classify_subject', default_text)

Notes:
- The loader is resilient: if the catalog is missing or the key is not found,
  it will return the provided default value.
- The catalog is cached in-process after the first load.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Optional


def _find_repo_root() -> Path:
    p = Path(__file__).resolve()
    for parent in [p] + list(p.parents):
        if (parent / "config.json").exists():
            return parent
    return Path(__file__).resolve().parents[-1]


BASE_DIR = _find_repo_root()
CATALOG_PATH = BASE_DIR / "prompts" / "prompt_catalog.md"

_CACHE: Optional[Dict[str, str]] = None


def _ensure_base_on_path() -> None:
    try:
        if str(BASE_DIR) not in sys.path:
            sys.path.insert(0, str(BASE_DIR))
    except Exception:
        pass


def _parse_catalog(text: str) -> Dict[str, str]:
    lines = text.splitlines()
    out: Dict[str, str] = {}
    current_key: Optional[str] = None
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        # Match H3 headers: ### key
        if line.startswith("### "):
            key = line[4:].strip()
            current_key = key if key else None
            i += 1
            # Seek the next fenced block
            while i < n and not lines[i].lstrip().startswith("```"):
                # Skip non-fence lines between header and fence
                i += 1
            if i >= n or not lines[i].lstrip().startswith("```"):
                # No fence found for this header; reset and continue
                current_key = None
                continue
            # Consume opening fence
            fence_line = lines[i]
            fence_indent = len(fence_line) - len(fence_line.lstrip())
            i += 1
            block: list[str] = []
            # Collect until closing fence at the same indent level
            while i < n:
                l = lines[i]
                if l.startswith(" " * fence_indent + "```"):
                    i += 1
                    break
                block.append(l)
                i += 1
            if current_key:
                out[current_key] = "\n".join(block).rstrip("\n")
                current_key = None
            continue
        i += 1
    return out


def _load_catalog(path: Optional[Path] = None) -> Dict[str, str]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    p = Path(path) if path else CATALOG_PATH
    try:
        text = p.read_text(encoding="utf-8")
    except Exception:
        _CACHE = {}
        return _CACHE
    _CACHE = _parse_catalog(text)
    return _CACHE


def get_prompt(key: str, default: Optional[str] = None, *, path: Optional[str] = None) -> str:
    """Return prompt text by key from the Markdown catalog.

    If not found or the file is missing, returns `default` (or empty string).
    """
    _ensure_base_on_path()
    try:
        catalog = _load_catalog(Path(path) if path else None)
    except Exception:
        catalog = {}
    if not isinstance(catalog, dict):
        return default or ""
    val = catalog.get(key)
    if isinstance(val, str) and val.strip():
        return val
    return default or ""


__all__ = ["get_prompt"]

