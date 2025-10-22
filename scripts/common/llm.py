#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Minimal shared LLM client wrappers for the repo.

Supported providers (grouped):
- openai_compat (includes deepseek/openai-compatible endpoints)
- google (Gemini)

Interface:
- LLM.complete(prompt, max_tokens=None, temperature=None, system=None) -> str
- LLM.stream_complete(prompt, max_tokens=None, temperature=None, system=None) -> iterator[str]
- LLM.ainvoke(prompt) -> str  (async wrapper for compatibility with async code)

Helpers:
- build_llm_registry(cfg) -> Dict[str, LLM]
- pick_llm(cfg, registry, key) -> LLM
- select_llm_for_node(cfg, registry, node_key, subrole=None) -> LLM

Notes:
- Streaming yields a single chunk if SDK streaming is unavailable; callers should tolerate that.
- We do not enforce SDK installation; informative errors are raised at call time.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterator, Optional


@dataclass
class _LLMInit:
    provider: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.6
    max_tokens: int = 8192


class LLM:
    """Unified sync/async LLM client."""

    def __init__(self, init: _LLMInit) -> None:
        self._cfg = init
        self._provider = (init.provider or "openai_compat").lower()
        self._client = None  # Lazy
        self._gemini_model = None  # Lazy
        self.last_info: Dict[str, Any] = {}

    # ---- internal helpers ----
    def _ensure_openai(self):
        if self._client is not None:
            return
        try:
            from openai import OpenAI  # type: ignore
        except Exception as e:
            raise RuntimeError("缺少 openai 库，请先安装：pip install -U openai") from e
        api_key = self._cfg.api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError("未配置 OpenAI 兼容 API Key（OPENAI_API_KEY/DEEPSEEK_API_KEY 或 config.llms[].api_key）。")
        base_url = (
            self._cfg.base_url
            or os.environ.get("OPENAI_BASE_URL")
            or os.environ.get("DEEPSEEK_BASE_URL")
            or "https://api.openai.com/v1"
        )
        self._client = OpenAI(api_key=api_key, base_url=base_url)

    def _ensure_gemini(self):
        if self._gemini_model is not None:
            return
        try:
            import google.generativeai as genai  # type: ignore
        except Exception as e:
            raise RuntimeError("缺少 google-generativeai 库，请先安装：pip install -U google-generativeai") from e
        api_key = self._cfg.api_key or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("未配置 Gemini API Key（GOOGLE_API_KEY 或 config.llms[].api_key）。")
        genai.configure(api_key=api_key)
        self._gemini_model = genai.GenerativeModel(self._cfg.model)

    # ---- sync interface ----
    def complete(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        self.last_info = {}
        temp = float(self._cfg.temperature if temperature is None else temperature)
        max_tks = int(self._cfg.max_tokens if not max_tokens else max_tokens)

        if self._provider in ("openai_compat", "deepseek", "openai"):
            self._ensure_openai()
            messages: list[dict[str, str]] = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            resp = self._client.chat.completions.create(  # type: ignore[attr-defined]
                model=self._cfg.model,
                messages=messages,
                temperature=temp,
                max_tokens=max_tks,
            )
            try:
                ch0 = (getattr(resp, "choices", None) or [None])[0]
                fr = getattr(ch0, "finish_reason", None)
                self.last_info = {"finish_reason": str(fr) if fr is not None else None}
            except Exception:
                pass
            return (resp.choices[0].message.content or "") if (resp and getattr(resp, "choices", None)) else ""

        elif self._provider in ("gemini", "google"):
            self._ensure_gemini()
            text = self._gemini_model.generate_content(prompt)  # type: ignore[attr-defined]
            out = getattr(text, "text", "") or ""
            try:
                cands = getattr(text, "candidates", [])
                fins = []
                for c in cands:
                    fr = getattr(c, "finish_reason", None)
                    if fr:
                        fins.append(str(fr))
                if fins:
                    self.last_info = {"finish_reasons": fins}
            except Exception:
                pass
            if out:
                return out
            try:
                cands = getattr(text, "candidates", [])
                if cands:
                    parts = getattr(getattr(cands[0], "content", None), "parts", [])
                    if parts and hasattr(parts[0], "text"):
                        return parts[0].text or ""
            except Exception:
                pass
            return ""

        else:
            raise RuntimeError(f"未知的 provider: {self._provider}")

    def stream_complete(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Iterator[str]:
        """Yields response chunks as they are received from the provider."""
        self.last_info = {}
        temp = float(self._cfg.temperature if temperature is None else temperature)
        max_tks = int(self._cfg.max_tokens if not max_tokens else max_tokens)

        if self._provider in ("openai_compat", "deepseek", "openai"):
            self._ensure_openai()
            messages: list[dict[str, str]] = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            
            response_stream = self._client.chat.completions.create(  # type: ignore[attr-defined]
                model=self._cfg.model,
                messages=messages,
                temperature=temp,
                max_tokens=max_tks,
                stream=True,
            )
            for chunk in response_stream:
                content = (chunk.choices[0].delta.content or "") if chunk.choices else ""
                if content:
                    yield content

        elif self._provider in ("gemini", "google"):
            self._ensure_gemini()
            import google.generativeai as genai

            config = genai.types.GenerationConfig(
                candidate_count=1,
                max_output_tokens=max_tks,
                temperature=temp,
            )
            response_stream = self._gemini_model.generate_content(  # type: ignore[attr-defined]
                prompt,
                stream=True,
                generation_config=config,
            )
            def _collect_text_parts(ch) -> list[str]:
                texts: list[str] = []
                try:
                    candidates = getattr(ch, "candidates", []) or []
                except Exception:
                    candidates = []
                for cand in candidates:
                    content = getattr(cand, "content", None)
                    parts = getattr(content, "parts", None) if content is not None else None
                    if not parts:
                        continue
                    for part in parts:
                        txt = getattr(part, "text", None)
                        if txt:
                            texts.append(txt)
                return texts

            def _collect_finish_reasons(ch) -> list[Any]:
                reasons: list[Any] = []
                try:
                    candidates = getattr(ch, "candidates", []) or []
                except Exception:
                    candidates = []
                for cand in candidates:
                    fr = getattr(cand, "finish_reason", None)
                    if fr is not None:
                        reasons.append(fr)
                return reasons

            def _is_stop_reason(reason: Any) -> bool:
                if reason is None:
                    return False
                if isinstance(reason, (int, float)):
                    try:
                        return int(reason) == 1
                    except Exception:
                        return False
                text = str(reason).strip().lower()
                return text in {"1", "stop", "finishreason.stop"}

            for chunk in response_stream:
                texts = _collect_text_parts(chunk)
                if texts:
                    for piece in texts:
                        if piece:
                            yield piece
                else:
                    try:
                        text = chunk.text
                        if text:
                            yield text
                    except ValueError:
                        pass

                finish_reasons = _collect_finish_reasons(chunk)
                if finish_reasons:
                    try:
                        self.last_info = {"finish_reasons": [str(fr) for fr in finish_reasons]}
                    except Exception:
                        self.last_info = {"finish_reasons": finish_reasons}
                    if all(_is_stop_reason(fr) for fr in finish_reasons):
                        break
                    # finish_reason=0 (UNSPECIFIED) 表示继续等待后续 chunk，不应视为错误
                    normalized: list[int] = []
                    for fr in finish_reasons:
                        try:
                            normalized.append(int(fr))
                        except Exception:
                            normalized.append(-1)
                    if any(val not in (0, 1, -1) for val in normalized):
                        raise RuntimeError(f"Gemini 流式输出中断: finish_reason={finish_reasons}")

        else:
            raise RuntimeError(f"Unknown provider for streaming: {self._provider}")

    # ---- async compatibility ----
    async def ainvoke(self, prompt: str) -> str:
        return await asyncio.to_thread(self.complete, prompt)


def _resolve_provider(entry: Dict[str, Any], fallback: Dict[str, Any]) -> str:
    p = entry.get("provider") or entry.get("api_provider") or fallback.get("api_provider") or "openai_compat"
    return str(p).lower()


def _make_llm_from_entry(entry: Dict[str, Any], fallback: Dict[str, Any]) -> LLM:
    provider = _resolve_provider(entry, fallback)
    model = str(entry.get("model") or fallback.get("model", "gpt-4o-mini"))
    temperature = float(entry.get("temperature", fallback.get("temperature", 0.6)))
    max_tokens = int(entry.get("max_tokens", fallback.get("max_tokens", 8192)))
    api_key = (
        entry.get("api_key")
        or entry.get("openai_api_key")
        or entry.get("deepseek_api_key")
        or entry.get("gemini_api_key")
    )
    base_url = entry.get("base_url") or entry.get("openai_base_url") or entry.get("deepseek_base_url")
    return LLM(_LLMInit(provider=provider, model=model, api_key=api_key, base_url=base_url, temperature=temperature, max_tokens=max_tokens))


def build_llm_registry(cfg: Dict[str, Any]) -> Dict[str, LLM]:
    reg: Dict[str, LLM] = {}
    entries = cfg.get("llms", {}) or {}
    if isinstance(entries, dict):
        for name, entry in entries.items():
            try:
                if not isinstance(entry, dict):
                    continue
                reg[name] = _make_llm_from_entry(entry, cfg)
            except Exception:
                # Skip invalid entries quietly; callers may inspect config separately.
                pass
    # Default: prefer node_llm.default if present; otherwise pick an arbitrary entry.
    default_key = None
    try:
        node_llm = cfg.get("node_llm") or {}
        dk = node_llm.get("default")
        if isinstance(dk, str) and dk in reg:
            default_key = dk
    except Exception:
        pass
    if not default_key and reg:
        default_key = next(iter(reg.keys()))
    if default_key:
        reg["default"] = reg[default_key]
    return reg


def pick_llm(cfg: Dict[str, Any], registry: Dict[str, LLM], key: Optional[str]) -> LLM:
    if key and key in registry:
        return registry[key]
    # fallback to node_llm.default then 'default' in registry
    node_llm = cfg.get("node_llm") or {}
    dk = node_llm.get("default")
    if isinstance(dk, str) and dk in registry:
        return registry[dk]
    if "default" in registry:
        return registry["default"]
    # Last resort: arbitrary
    if registry:
        return registry[next(iter(registry.keys()))]
    raise RuntimeError("LLM 注册表为空。请在 config.json.llms 配置至少一个条目。")


def select_llm_for_node(
    cfg: Dict[str, Any],
    registry: Dict[str, LLM],
    node_key: str,
    subrole: Optional[str] = None,
) -> LLM:
    mapping = cfg.get("node_llm", {}) or {}

    def _resolve_name(nk: str, sr: Optional[str]) -> Optional[str]:
        if sr:
            name = mapping.get(f"{nk}.{sr}") or mapping.get(nk)
        else:
            name = mapping.get(nk)
        return name if isinstance(name, str) else None

    name = _resolve_name(node_key, subrole)
    if not name and node_key == "generate_and_review_by_chapter":
        name = _resolve_name("generate_and_review_parallel", subrole)
    if name and name in registry:
        return registry[name]
    # fallback: node_llm.default → registry.default
    return pick_llm(cfg, registry, None)


# Backward-compatible alias for async usage in code that expects 'ainvoke'.
AsyncLLM = LLM
