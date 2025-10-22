#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


def repo_root(start: Optional[Path] = None) -> Path:
    """Walk up from start (__file__ by default) to find the directory containing config.json."""
    p = (start or Path(__file__)).resolve()
    for parent in [p] + list(p.parents):
        if (parent / "config.json").exists():
            return parent
    return p.parents[-1]


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    cfg_path = Path(path) if path else (repo_root() / "config.json")
    if not cfg_path.exists():
        raise SystemExit(f"[错误] 未找到配置文件: {cfg_path}")
    try:
        return json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise SystemExit(f"[错误] 解析配置文件失败: {e}")


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def slugify(text: str, fallback: str = "subject") -> str:
    """Simple ASCII-friendly kebab-case slugify.

    - Normalize some common CJK punctuation.
    - Keep [0-9A-Za-z\-_. ] then collapse spaces to '-'.
    - Lowercase and trim separators.
    """
    t = (text or "").replace("（", "(").replace("）", ")").replace("—", "-")
    t = t.strip()
    t = re.sub(r"[^0-9A-Za-z\-_.\s]", "", t)
    t = re.sub(r"\s+", "-", t)
    t = t.strip("-_.").lower()
    return t or fallback


def try_parse_json_array(text: str) -> List[Any]:
    t = (text or "").strip()
    if not t:
        return []
    if "```" in t:
        parts = t.split("```")
        for part in parts:
            s = part.strip()
            if s.startswith("[") and s.endswith("]"):
                try:
                    return json.loads(s)
                except Exception:
                    pass
    try:
        i = t.index("[")
        j = t.rindex("]")
        return json.loads(t[i : j + 1])
    except Exception:
        return []


def try_parse_json_object(text: str) -> Dict[str, Any]:
    t = (text or "").strip()
    if not t:
        return {}
    if "```" in t:
        parts = t.split("```")
        for part in parts:
            s = part.strip()
            if s.startswith("{") and s.endswith("}"):
                try:
                    return json.loads(s)
                except Exception:
                    pass
    try:
        i = t.index("{")
        j = t.rindex("}")
        return json.loads(t[i : j + 1])
    except Exception:
        return {}


def parse_json(text: str) -> Any:
    """Parse any JSON value; supports code fence fallback."""
    t = (text or "").strip()
    if not t:
        raise ValueError("空响应：未包含任何文本。")
    try:
        return json.loads(t)
    except Exception:
        pass
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", t, re.IGNORECASE)
    if m:
        frag = (m.group(1) or "").strip()
        return json.loads(frag)
    # array or object slice
    i, j = t.find("{"), t.rfind("}")
    if i != -1 and j != -1 and j > i:
        return json.loads(t[i : j + 1])
    i, j = t.find("["), t.rfind("]")
    if i != -1 and j != -1 and j > i:
        return json.loads(t[i : j + 1])
    raise ValueError("无法从文本中解析 JSON。")


def extract_json_object(text: str) -> Dict[str, Any]:
    """Robustly extract a JSON object or raise with reasons; used for strict outputs."""
    reasons: List[str] = []
    s = (text or "").strip()
    if not s:
        raise ValueError("空响应：模型未返回任何文本。")

    def _snippet(text: str, pos: Optional[int] = None, radius: int = 80) -> str:
        if not text:
            return ""
        if pos is None or pos < 0 or pos >= len(text):
            head = text[:200]
            tail = text[-200:] if len(text) > 400 else ""
            mid = " … " if tail else ""
            return f"head='{head}'{mid}{(' tail=' + tail) if tail else ''}"
        start = max(0, pos - radius)
        end = min(len(text), pos + radius)
        return f"near[{pos}]: '{text[start:end]}'"

    # 1) direct
    try:
        data = json.loads(s)
        if isinstance(data, dict):
            return data
        reasons.append(f"直接解析为 {type(data).__name__}（顶层需为对象）")
    except json.JSONDecodeError as e:  # type: ignore[attr-defined]
        reasons.append(f"直接解析失败: {e.msg} (line {e.lineno}, col {e.colno}) | {_snippet(s, e.pos)}")
    except Exception as e:
        reasons.append(f"直接解析异常: {e!r}")

    # 2) fenced
    m = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", s, re.IGNORECASE)
    if m:
        frag = (m.group(1) or "").strip()
        try:
            data = json.loads(frag)
            if isinstance(data, dict):
                return data
            reasons.append(f"```json 内为 {type(data).__name__}（顶层需为对象）")
        except json.JSONDecodeError as e:  # type: ignore[attr-defined]
            reasons.append(f"```json 解析失败: {e.msg} (line {e.lineno}, col {e.colno}) | {_snippet(frag, e.pos)}")
        except Exception as e:
            reasons.append(f"```json 解析异常: {e!r}")
    else:
        reasons.append("未发现 ```json 围栏")

    # 3) slice by braces
    i, j = s.find("{"), s.rfind("}")
    if i != -1 and j != -1 and j > i:
        frag2 = s[i : j + 1].strip()
        try:
            data = json.loads(frag2)
            if isinstance(data, dict):
                return data
            reasons.append(f"大括号截取为 {type(data).__name__}（顶层需为对象）")
        except json.JSONDecodeError as e:  # type: ignore[attr-defined]
            reasons.append(f"截取解析失败: {e.msg} (line {e.lineno}, col {e.colno}) | {_snippet(frag2, e.pos)}")
        except Exception as e:
            reasons.append(f"截取解析异常: {e!r}")
    else:
        reasons.append("未找到成对的大括号 { … }")

    reason_text = "; ".join(reasons) if reasons else "未知原因"
    raise ValueError(f"无法从模型输出中提取 JSON 对象：{reason_text}")

