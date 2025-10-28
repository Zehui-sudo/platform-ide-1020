#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Robust prompt loader for parsing prompt_catalog.md.
"""

from pathlib import Path
from typing import Dict, Optional

# Cache to avoid reading the file multiple times
_cache: Optional[Dict[str, str]] = None

def _load_prompts_from_catalog() -> Dict[str, str]:
    """
    Parses the prompt_catalog.md file and returns a dictionary of prompts.
    This parser is designed to be robust against nested code blocks within a prompt.
    """
    global _cache
    if _cache is not None:
        return _cache

    prompts = {}
    try:
        # Assume this file is in prompts/, so catalog is in the same directory
        catalog_path = Path(__file__).parent / "prompt_catalog.md"
        content = catalog_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        _cache = {}
        return _cache

    lines = content.splitlines()
    current_key: Optional[str] = None
    current_lines: list[str] = []
    inside_block = False

    for raw_line in lines:
        line = raw_line.rstrip('\n')
        stripped = line.strip()

        if not inside_block and stripped.startswith('### '):
            current_key = stripped[4:].strip()
            current_lines = []
            continue

        if current_key is None:
            continue

        if not inside_block:
            if stripped.startswith('```'):
                # Start of the fenced prompt content (language marker optional).
                inside_block = True
            continue

        # We are inside a fenced code block for the current prompt key.
        if stripped.startswith('```') and stripped.strip('`').strip() == '':
            # Closing fence encountered; finalize prompt.
            prompts[current_key] = "\n".join(current_lines)
            current_key = None
            current_lines = []
            inside_block = False
            continue

        current_lines.append(raw_line)

    _cache = prompts
    return _cache

def get_prompt(key: str, default: Optional[str] = None) -> str:
    """
    Retrieves a prompt by its key from the loaded catalog.
    
    Args:
        key: The dot-separated key for the prompt (e.g., "reconstruct.classify_subject").
        default: An optional fallback value. If not provided, a KeyError is raised for missing keys.

    Returns:
        The prompt template string.

    Raises:
        KeyError: If the key is not found and no default is provided.
    """
    prompts = _load_prompts_from_catalog()
    result = prompts.get(key)
    
    if result is not None:
        return result
    
    if default is not None:
        return default
        
    raise KeyError(f"Prompt with key '{key}' not found in catalog and no default was provided.")
