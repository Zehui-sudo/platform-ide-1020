#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Robust prompt loader for parsing prompt_catalog.md.
"""

import re
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

    # Split the file by '### ' headers, which denote the start of a new prompt key
    # The lookahead assertion `(?=
### )` keeps the delimiter.
    sections = re.split(r'\n(?=### )', content)
    
    for section in sections:
        section = section.strip()
        if not section.startswith('### '):
            continue

        lines = section.splitlines()
        key = lines[0].replace('### ', '').strip()
        
        # Find the start of the main code block
        code_block_start_index = -1
        for i, line in enumerate(lines):
            if line.strip().startswith('```'):
                code_block_start_index = i
                break
        
        if code_block_start_index != -1:
            # Find the end of the main code block by searching from the bottom up
            code_block_end_index = -1
            for i in range(len(lines) - 1, code_block_start_index, -1):
                if lines[i].strip() == '```':
                    code_block_end_index = i
                    break
            
            if code_block_end_index != -1:
                # Extract the content between the fences
                prompt_lines = lines[code_block_start_index + 1 : code_block_end_index]
                prompts[key] = "\n".join(prompt_lines)

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