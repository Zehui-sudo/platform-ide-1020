#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Prompt loader backed by the static prompt_catalog_data module."""

from typing import Dict, Optional

try:
    from .prompt_catalog_data import PROMPTS as _PROMPT_TABLE
except ImportError as exc:  # pragma: no cover - should never happen in runtime
    raise RuntimeError("无法导入 prompts.prompt_catalog_data 中的 PROMPTS 定义。") from exc

# Cache to avoid copying the dictionary multiple times
_cache: Optional[Dict[str, str]] = None


def _load_prompts_from_catalog() -> Dict[str, str]:
    """
    Returns a dictionary of prompt templates indexed by their dot-separated keys.
    Data is sourced from prompt_catalog_data.PROMPTS.
    """
    global _cache
    if _cache is None:
        # copy to avoid accidental mutation of the source dictionary
        _cache = dict(_PROMPT_TABLE)
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
