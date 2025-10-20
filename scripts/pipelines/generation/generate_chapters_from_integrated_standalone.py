#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
章节级生成脚本（独立节点版）

功能：与 scripts/generate_chapters_from_integrated.py 相同，但不复用 run_full 中的节点，
而是将相关节点与依赖逻辑复制到本脚本中使用。

流程：从“选择章节”开始 → 结构感知生成 → 审查 →（可选）修复提案与自动应用 → 发布 → 汇总

输入：包含 reconstructed_outline 的集成 JSON（如 llm-integrated-20251013-125553.json）

用法示例：
  python scripts/pipelines/generation/generate_chapters_from_integrated_standalone.py \
    --input output/integrated_pipeline/quantum-mechanics-integrated-20251016-164313.json \
    --selected-chapters 1,2,3 \
    --config config.json \
    --skip-content-review \
    --debug

调试模式：
- --debug 开启后，输出详细日志，包含：所用模型信息、每个 LLM 调用的完整 Prompt；
- 日志会写入 output/<output_subdir>/log.txt。

新增选项：
- --subject-type tool|theory 手动指定主题类型；未指定时自动分类。
- --classify-llm-key <key> 指定分类所用 LLM 键名（覆盖 node_llm/classify_subject/default）。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TypedDict

def _find_repo_root() -> Path:
    p = Path(__file__).resolve()
    for parent in [p] + list(p.parents):
        if (parent / "config.json").exists():
            return parent
    return Path(__file__).resolve().parents[-1]

BASE_DIR = _find_repo_root()
PUBLIC_DIR = BASE_DIR / "web-learner" / "public"
CONTENT_ROOT = PUBLIC_DIR / "content"

# 加入父目录搜索路径（导入 mermaid 工具和可选 LLM 工具）
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from mermaid_sanitizer import sanitize_mermaid_in_markdown


# ----------------------------
# 基础工具
# ----------------------------

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def slugify(text: str) -> str:
    s = (text or "").strip().lower()
    s = re.sub(r"[\s/]+", "-", s)
    s = re.sub(r"[^a-z0-9\-_.]+", "", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "topic"


def load_config(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"配置文件不存在: {path}")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        raise RuntimeError(f"解析配置文件失败: {e}")


def try_parse_json_array(text: str) -> List[Dict[str, Any]]:
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


# ----------------------------
# 数据结构
# ----------------------------

@dataclass
class Point:
    id: str
    title: str
    chapter: str
    section: str


class WorkState(TypedDict, total=False):
    topic: str
    topic_meta: Dict[str, Any]
    topic_slug: str
    config: Dict[str, Any]
    outline_final_md: str
    outline_struct: Dict[str, Any]
    points: List[Point]
    drafts: List[Dict[str, str]]
    reviews: List[Dict[str, Any]]
    publish_paths: List[str]
    failures: List[Dict[str, Any]]
    report_md: str
    fix_proposals: List[Dict[str, Any]]
    fix_applied: List[str]
    fix_skipped: List[str]
    fix_iterations: List[Dict[str, Any]]
    output_subdir: str
    selected_chapters: List[str]
    auto_apply_stats: Dict[str, Any]


# ----------------------------
# LLM 客户端与模型选择（完全去耦）
# ----------------------------

class _AsyncLLM:
    async def ainvoke(self, prompt: str) -> str:
        raise NotImplementedError


class OpenAICompatClient(_AsyncLLM):
    def __init__(self, api_key: str, base_url: str, model: str, temperature: float, max_tokens: int) -> None:
        self._ok = False
        try:
            from openai import AsyncOpenAI  # type: ignore
        except Exception:
            logging.getLogger(__name__).error("缺少 openai 库，请安装: pip install openai")
            self._client = None
            self._ok = False
            return
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._ok = True

    async def ainvoke(self, prompt: str) -> str:
        if not self._ok:
            raise RuntimeError("OpenAI 兼容客户端未正确初始化")
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": "你是一位严谨的技术写作与编辑助手。"},
                {"role": "user", "content": prompt},
            ],
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        return (resp.choices[0].message.content or "") if (resp and resp.choices) else ""


class GeminiClient(_AsyncLLM):
    def __init__(self, api_key: str, model: str) -> None:
        self._ok = False
        try:
            import google.generativeai as genai  # type: ignore
        except Exception:
            logging.getLogger(__name__).error("缺少 google-generativeai，请安装: pip install -U google-generativeai")
            self._model = None
            return
        if not api_key:
            logging.getLogger(__name__).error("缺少 GOOGLE_API_KEY / gemini_api_key 配置")
            return
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model)
        self._ok = True

    async def ainvoke(self, prompt: str) -> str:
        if not self._ok:
            raise RuntimeError("Gemini 客户端未正确初始化")
        def _sync_call() -> str:
            resp = self._model.generate_content(prompt)
            txt = getattr(resp, "text", "")
            if txt:
                return txt
            try:
                cands = getattr(resp, "candidates", [])
                if cands:
                    parts = getattr(getattr(cands[0], "content", None), "parts", [])
                    if parts and hasattr(parts[0], "text"):
                        return parts[0].text or ""
            except Exception:
                pass
            return ""
        return await asyncio.to_thread(_sync_call)


def init_llm(cfg: Dict[str, Any]) -> _AsyncLLM:
    provider = str(cfg.get("api_provider", "openai_compat")).lower()
    model = cfg.get("model", "gpt-4o-mini")
    temperature = float(cfg.get("temperature", 0.6))
    max_tokens = int(cfg.get("max_tokens", 8192))
    if provider in {"openai_compat", "deepseek", "openai"}:
        api_key = cfg.get("openai_api_key") or cfg.get("deepseek_api_key") or os.environ.get("OPENAI_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
        base_url = cfg.get("openai_base_url") or cfg.get("deepseek_base_url") or os.environ.get("OPENAI_BASE_URL") or os.environ.get("DEEPSEEK_BASE_URL") or "https://api.openai.com/v1"
        return OpenAICompatClient(api_key=api_key or "", base_url=base_url, model=model, temperature=temperature, max_tokens=max_tokens)
    elif provider in {"gemini", "google"}:
        api_key = cfg.get("gemini_api_key") or os.environ.get("GOOGLE_API_KEY") or ""
        return GeminiClient(api_key=api_key, model=model)
    else:
        raise SystemExit(f"未知的 api_provider: {provider}")


def _resolve_provider(entry: Dict[str, Any], fallback: Dict[str, Any]) -> str:
    p = entry.get("provider") or entry.get("api_provider") or fallback.get("api_provider") or "openai_compat"
    return str(p).lower()


def _make_llm_from_entry(entry: Dict[str, Any], fallback: Dict[str, Any]) -> _AsyncLLM:
    provider = _resolve_provider(entry, fallback)
    model = entry.get("model") or fallback.get("model", "gpt-4o-mini")
    temperature = float(entry.get("temperature", fallback.get("temperature", 0.6)))
    max_tokens = int(entry.get("max_tokens", fallback.get("max_tokens", 8192)))
    if provider in {"openai_compat", "deepseek", "openai"}:
        api_key = (
            entry.get("api_key")
            or entry.get("openai_api_key")
            or entry.get("deepseek_api_key")
            or fallback.get("openai_api_key")
            or fallback.get("deepseek_api_key")
            or os.environ.get("OPENAI_API_KEY")
            or os.environ.get("DEEPSEEK_API_KEY")
            or ""
        )
        base_url = (
            entry.get("base_url")
            or entry.get("openai_base_url")
            or entry.get("deepseek_base_url")
            or fallback.get("openai_base_url")
            or fallback.get("deepseek_base_url")
            or os.environ.get("OPENAI_BASE_URL")
            or os.environ.get("DEEPSEEK_BASE_URL")
            or "https://api.openai.com/v1"
        )
        return OpenAICompatClient(api_key=api_key, base_url=base_url, model=model, temperature=temperature, max_tokens=max_tokens)
    elif provider in {"gemini", "google"}:
        api_key = entry.get("api_key") or entry.get("gemini_api_key") or fallback.get("gemini_api_key") or os.environ.get("GOOGLE_API_KEY") or ""
        return GeminiClient(api_key=api_key, model=str(model))
    else:
        raise SystemExit(f"未知的 api_provider: {provider}")


def build_llm_registry(cfg: Dict[str, Any]) -> Dict[str, _AsyncLLM]:
    reg: Dict[str, _AsyncLLM] = {}
    reg["default"] = init_llm(cfg)
    entries = cfg.get("llms", {}) or {}
    if isinstance(entries, dict):
        for name, entry in entries.items():
            try:
                if not isinstance(entry, dict):
                    continue
                reg[name] = _make_llm_from_entry(entry, cfg)
            except Exception as e:
                logging.getLogger(__name__).warning(f"LLM 注册失败: {name}: {e}")
    return reg


def select_llm_for_node(cfg: Dict[str, Any], registry: Dict[str, _AsyncLLM], node_key: str, subrole: Optional[str] = None) -> _AsyncLLM:
    mapping = cfg.get("node_llm", {}) or {}

    def _resolve_name(nk: str, sr: Optional[str]) -> Optional[str]:
        if sr:
            return mapping.get(f"{nk}.{sr}") or mapping.get(nk)
        return mapping.get(nk)

    name: Optional[str] = _resolve_name(node_key, subrole)
    if not name and node_key == "generate_and_review_by_chapter":
        name = _resolve_name("generate_and_review_parallel", subrole)
    if name and name in registry:
        return registry[name]
    map_default = mapping.get("default")
    if map_default and map_default in registry:
        return registry[map_default]
    return registry.get("default")  # type: ignore


# ----------------------------
# 节点依赖函数（复制自 run_full）
# ----------------------------

def _parse_indices_from_id(pid: str) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    try:
        m = re.match(r"^.*?-sec-(\d+)-(\d+)-(\d+)-.*$", pid)
        if not m:
            return None, None, None
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    except Exception:
        return None, None, None


def _make_filename(pid: str, title: str, style: str = "id") -> str:
    if style == "id":
        return f"{pid}.md"
    ci, gi, si = _parse_indices_from_id(pid)
    title_slug = slugify(title)
    if style == "structured":
        if ci and gi and si:
            base = f"sec-{ci}-{gi}-{si}-{title_slug or 'section'}"
        else:
            base = title_slug or pid
        return f"{base}.md"
    return f"{pid}.md"


def _clean_title_for_filename(title: str) -> str:
    """清理标题用于文件名后缀：
    - 去掉前导序号（如 "1.2 "、"1.2.3 "、"1) ", "1." 等常见格式）
    - 去掉结尾的英文括号注释（如 "(Dirac Notation)"）
    - 替换文件系统不友好的分隔符（/ 和 \）为 '-'
    - 保留中文及中文标点（如全角冒号 '：'）
    """
    t = str(title or "").strip()
    # 去掉前缀编号（如 1.2 、1.2.3 、1) 、1. 等）及其后常见分隔
    t = re.sub(r"^\s*(?:\d+(?:\.\d+)*|\d+[\.)])\s*[：:、.\-\s]*", "", t)
    # 去掉结尾括号内的英文注释（仅移除纯 ASCII 的括号内容）
    t = re.sub(r"\s*\([A-Za-z0-9 ,.'\-_/+&:#]+\)\s*$", "", t)
    # 替换不安全路径字符
    t = t.replace("/", "-").replace("\\", "-")
    return t.strip()


def _build_contextual_content_prompt(
    *,
    topic: str,
    language: str,
    path: str,
    section_title: str,
    primary_goal: str = "",
    suggested_modules: Optional[List[str]] = None,
    suggested_contents: Optional[List[str]] = None,
    structure_type: str = "pipeline",
    relation_to_previous: str = "",
    prior_context: str = "",
) -> str:
    lang = (language or "zh").strip().lower()
    role = "你是一位世界级的教育家与作家，以其能将复杂、抽象的理论知识变得浅显易懂、引人入胜而闻名。你的天赋在于不仅仅是解释，更是去启发，将错综复杂的概念编织成一个引人入胜的叙事，从而促进读者形成深刻且持久的理解。"
    head = f"# 课程内容生成任务\n\n{role}\n"
    if path:
        head += f"\n【定位】{path}\n"

    goal_part = f"\n【教学目标】{primary_goal}\n" if primary_goal else "\n【教学目标】围绕当前知识点展开，高质量解释并给出必要示例。\n"
    mods = suggested_modules or []
    if mods:
        mods_part = "\n【建议内容模块】" + ", ".join(mods) + "\n"
    else:
        mods_part = "\n【建议内容模块】summary, code_example（如适合）, common_mistake_warning（如有）, diagram（如有因果/流程）\n"

    conts = [c for c in (suggested_contents or []) if isinstance(c, str)]
    conts_part = "\n【核心内容】" + ", ".join(conts) + "\n" if conts else "\n"

    style_part = """
【写作风格与深度要求】
- **类比与具象化**：对于抽象的核心概念，请使用读者生活中可能熟悉的现象或经验进行类比，帮助他们建立直观感受。**重要：确保类比在简化概念的同时，不会牺牲关键的技术精确性。**
- **背景与叙事**：对于任何一个基础理论、原则或关键思想，请深入挖掘其提出的背景。解释它试图解决什么问题？在此之前的主流观点是什么？它的出现带来了哪些关键性的影响？**对于技术性强的学科，这意味着清晰地阐述其“问题-解决方案-影响”的逻辑链条，而非文学性描述。**
- **启发性结尾**：在文章末尾，除了总结要点，还应提出一些发人深省的问题，或一个能承上启下的前瞻性观点，以激发读者的好奇心和进一步探索的欲望。
- **篇幅指导**：为确保内容的深度，每一篇知识点都应被充分地探讨。请力求内容详尽，目标篇幅在 **2500-3500字** 左右。请优先考虑内容的深度与清晰度，而非简洁。
"""

    if structure_type == "pipeline":
        ctx_part = (f"\n【已完成的小节内容（Context）】\n> " + prior_context.replace("\n", "\n> ") + "\n") if prior_context else "\n"
        task = (
            f"\n【你的任务】请严格遵循【写作风格与深度要求】，紧接上述内容，围绕“{section_title}”自然过渡并续写下一段。请以【核心内容】为基础，进行详尽地展开与阐述，确保讲解不仅系统、逻辑清晰，而且内容丰富、细节饱满、富有启发性。\n"
        )
    else:
        dep = relation_to_previous.strip().lower()
        if prior_context and dep in {"builds_on", "deep_dive_into"}:
            ctx_part = f"\n【父级知识点（Parent Context）】\n> " + prior_context.replace("\n", "\n> ") + "\n"
        else:
            ctx_part = "\n"
        task = f"\n【你的任务】请严格遵循【写作风格与深度要求】，撰写一篇关于“{section_title}”的独立教学段落。请以【核心内容】为基础，进行详尽地展开与阐述，确保讲解不仅系统、逻辑清晰，而且内容丰富、细节饱满、富有启发性。\n"

    constraints = """
【输出约束】
- 使用 Markdown；结构清晰，标题层级合理；
- 叙事连贯：避免与已给上下文重复；必要时用一句话承接；
- 如引用数学/图表/流程，请使用适当的模块；
- 如 Markdown 中涉及代码示例，请用代码块进行声明包裹；
- 表格中不要出现代码格式的内容；
- 结尾含简短总结或要点回顾。
"""
    lang_line = f"\n【语言】{'中文' if lang.startswith('zh') else 'English'}\n"
    return head + goal_part + mods_part + conts_part + style_part + ctx_part + task + constraints + lang_line


def _build_theory_opening_prompt(
    *,
    topic: str,
    language: str,
    path: str,
    section_title: str,
    primary_goal: str = "",
    suggested_modules: Optional[List[str]] = None,
    suggested_contents: Optional[List[str]] = None,
    current_chapter_index: int,
    all_chapters_struct: List[Dict[str, Any]],
) -> str:
    lang = (language or "zh").strip().lower()
    role = "你是一位世界级的教育家与作家，以其能将复杂、抽象的理论知识变得浅显易懂、引人入胜而闻名。你的天赋在于不仅仅是解释，更是去启发，将错综复杂的概念编织成一个引人入胜的叙事，从而促进读者形成深刻且持久的理解。"
    head = f"# 课程内容生成任务\n\n{role}\n"
    if path:
        head += f"\n【定位】{path}\n"

    context_str = ""
    if current_chapter_index > 1 and all_chapters_struct:
        global_overview_lines = ["【全局目录概览】"]
        for i in range(current_chapter_index - 1):
            if i < len(all_chapters_struct):
                ch_title = all_chapters_struct[i].get("title", f"第{i+1}章")
                global_overview_lines.append(f"- {ch_title}")

        prev_chapter_detail_lines = ["\n【前文章节详解】"]
        prev_ch_idx = current_chapter_index - 2
        if prev_ch_idx < len(all_chapters_struct):
            prev_ch = all_chapters_struct[prev_ch_idx]
            prev_ch_title = prev_ch.get("title", f"第{current_chapter_index-1}章")
            prev_chapter_detail_lines.append(prev_ch_title)
            for gr in prev_ch.get("groups", []):
                for sec in gr.get("sections", []):
                    sec_title = sec.get("title", "")
                    if sec_title:
                        prev_chapter_detail_lines.append(f"- {sec_title}")
        context_str = "\n".join(global_overview_lines) + "\n" + "\n".join(prev_chapter_detail_lines)

    goal_part = f"\n【教学目标】{primary_goal}\n" if primary_goal else "\n【教学目标】围绕当前知识点展开，高质量解释并给出必要示例。\n"
    mods = suggested_modules or []
    if mods:
        mods_part = "\n【建议内容模块】" + ", ".join(mods) + "\n"
    else:
        mods_part = "\n【建议内容模块】summary, code_example（如适合）, common_mistake_warning（如有）, diagram（如有因果/流程）\n"

    conts = [c for c in (suggested_contents or []) if isinstance(c, str)]
    conts_part = "\n【核心内容】" + ", ".join(conts) + "\n" if conts else "\n"

    style_part = """
【写作风格与深度要求】
- **类比与具象化**：对于抽象的核心概念，请使用读者生活中可能熟悉的现象或经验进行类比，帮助他们建立直观感受。**重要：确保类比在简化概念的同时，不会牺牲关键的技术精确性。**
- **背景与叙事**：对于任何一个基础理论、原则或关键思想，请深入挖掘其提出的背景。解释它试图解决什么问题？在此之前的主流观点是什么？它的出现带来了哪些关键性的影响？**对于技术性强的学科，这意味着清晰地阐述其“问题-解决方案-影响”的逻辑链条，而非文学性描述。**
- **启发性结尾**：在文章末尾，除了总结要点，还应提出一些发人深省的问题，或一个能承上启下的前瞻性观点，以激发读者的好奇心和进一步探索的欲望。
- **篇幅指导**：为确保内容的深度，每一篇知识点都应被充分地探讨。请力求内容详尽，目标篇幅在 **2500-3500字** 左右。请优先考虑内容的深度与清晰度，而非简洁。
"""

    if current_chapter_index == 1:
        task = (
            f"\n【你的任务】请严格遵循【写作风格与深度要求】，作为一名该领域的专家，围绕“{section_title}”这个主题，撰写整个课程的开篇内容。"
            f"请以【核心内容】为基础，进行详尽地展开与阐述，确保讲解不仅系统、逻辑清晰，而且内容丰富、细节饱满、富有启发性，并为后续所有章节的学习做好铺垫。\n"
        )
    else:
        task = (
            f"\n【你的任务】请严格遵循【写作风格与深度要求】，作为一名该领域的专家，参考【全局目录概览】和【前文章节详解】。现在，请开启一个全新的章节，围绕“{section_title}”这一主题撰写开篇内容。"
            f"请以【核心内容】为基础，进行详尽地展开与阐述，确保讲解不仅系统、逻辑清晰，而且内容丰富、细节饱满、富有启发性，并为本章后续内容的学习做好铺垫。\n"
        )

    constraints = """
【输出约束】
- 使用 Markdown；结构清晰，标题层级合理；
- 叙事连贯：避免与已给上下文重复；必要时用一句话承接；
- 如引用数学/图表/流程，请使用适当的模块；
- 如 Markdown 中涉及代码示例，请用代码块进行声明包裹；
- 表格中不要出现代码格式的内容；
- 结尾含简短总结或要点回顾。
"""
    lang_line = f"\n【语言】{'中文' if lang.startswith('zh') else 'English'}\n"
    return head + (context_str + "\n" if context_str else "") + goal_part + mods_part + conts_part + style_part + task + constraints + lang_line



# ----------------------------
# 工具型主题 Prompt（Prompt 2）
# ----------------------------

PROMPT_CLASSIFY_SUBJECT = r"""
You are a curriculum designer's assistant. Your task is to classify a given subject into one of two categories: "theory" or "tool".

Category Definitions:
* Theory: a field of knowledge, a discipline, or a conceptual framework focused on principles and the "why".
* Tool: a specific language, library, framework, or technology focused on the "how-to".

Task: Classify the following subject. Respond with a single word: theory or tool.

Subject: "[subject]"
"""


def _build_tool_content_prompt(
    *,
    topic: str,
    language: str,
    path: str,
    section_title: str,
    primary_goal: str = "",
    suggested_modules: Optional[List[str]] = None,
    suggested_contents: Optional[List[str]] = None,
    structure_type: str = "pipeline",
    relation_to_previous: str = "",
    prior_context: str = "",
) -> str:
    lang = (language or "zh").strip().lower()
    mods = [m for m in (suggested_modules or []) if isinstance(m, str)]
    conts = [c for c in (suggested_contents or []) if isinstance(c, str)]
    role = f"你是一位世界级的技术教育者和 {topic} 专家。"
    header = [
        role,
        "你的任务是接收一份由“总建筑师”设计的“教学设计图”（一个JSON对象），并依据这份设计图，将其中描述的知识点，转化为一篇高质量、多层次、结构清晰的Markdown教程。",
    ]
    if path:
        header.append(f"【定位】{path}")
    design_obj = {
        "title": section_title,
        "id": "point",
        "primary_goal": primary_goal or "",
        "suggested_modules": mods,
        "suggested_contents": conts,
    }
    ctx = ""
    if structure_type == "pipeline":
        if prior_context:
            ctx = "\n".join([
                "【已完成的小节内容】",
                "> " + (prior_context or "").replace("\n", "\n> "),
                "",
                "请在不重复以上内容的前提下，自然过渡并续写本节。",
            ])
    else:
        dep = (relation_to_previous or "").strip().lower()
        if prior_context and dep in {"builds_on", "deep_dive_into"}:
            ctx = "\n".join([
                "【父级知识点（Parent Context）】",
                "> " + (prior_context or "").replace("\n", "\n> "),
                "",
                ("请在父级基础上深入讲解当前知识点，突出内在联系与扩展。" if dep == "deep_dive_into" else "请在父级基础上推进当前知识点，说明改进或新增能力。"),
            ])
    sections = [
"""
### 🎯 核心概念
用一句话说明这个知识点解决什么问题，为什么需要它。语言要精炼，直击要害。

### 💡 使用方式
介绍这个知识点的具体使用方式

### 📚 Level 1: 基础认知（30秒理解）
提供一个最简单、最直观的代码示例，让初学者一眼就能明白基本用法。代码必须完整可运行，并以注释的形式包含预期输出结果。
```python
# 示例代码
```

### 📈 Level 2: 核心特性（深入理解）
展示2-3个该知识点的关键特性或高级用法，每个特性配一个完整的代码示例和简要说明。

#### 特性1: [特性名称]
(简要说明)
```python
# 示例代码
```

#### 特性2: [特性名称]
(简要说明)
```python
# 示例代码
```

### 🔍 Level 3: 对比学习（避免陷阱）
通过对比“错误用法”和“正确用法”来展示常见的陷阱或易混淆的概念。每个用法都必须有完整的代码示例和清晰的解释。

```python
# === 错误用法 ===
# ❌ 展示常见错误
# 解释为什么是错的

# === 正确用法 ===
# ✅ 展示正确做法
# 解释为什么这样是对的
```

### 🚀 Level 4: 实战应用（真实场景）
设计一个生动有趣的实战场景来综合运用该知识点。场景要富有创意，例如游戏、科幻、生活趣事等，避免枯燥的纯理论或商业案例。代码需完整，并有清晰的输出结果。

**场景：** [选择一个有趣的场景，如：🎮 游戏角色属性计算器, 🚀 星际飞船导航系统, 🍕 披萨订单处理器, 🐾 虚拟宠物互动等]

```python
# 实战场景的完整代码
```

### 💡 记忆要点
- **要点1**: [总结第一个关键记忆点]
- **要点2**: [总结第二个关键记忆点]
- **要点3**: [总结第三个关键记忆点]
"""
    ]
    constraints = [
        "【输出要求】",
        "- **循序渐进**: 从最简单的概念到复杂的应用。"
        "- **重点突出**: 使用加粗、列表等方式突出核心知识。"
        "- **生动有趣**: Level 4的实战场景要富有想象力，使用Emoji增加趣味性。"
        "- **代码可运行**: 所有代码块都必须是独立的、完整的、可以直接复制运行的。"
        "- **中文讲解**: 所有解释和注释都使用中文。"
    ]
    prompt = []
    prompt.extend(header)
    prompt.append("\n【教学设计图】\n" + json.dumps(design_obj, ensure_ascii=False, indent=2))
    if ctx:
        prompt.append("\n" + ctx)
    prompt.append("\n【请严格按照以下Markdown结构生成内容，确保每个代码块都是完整、可独立运行的】\n" + "\n".join(sections))
    prompt.append("\n" + "\n".join(constraints))
    return "\n\n".join(prompt)


async def _classify_subject_async(llm, subject: str) -> str:
    prompt = PROMPT_CLASSIFY_SUBJECT.replace("[subject]", subject)
    try:
        text = await llm.ainvoke(prompt)
        t = (text or "").strip().lower()
        m = re.search(r"\b(theory|tool)\b", t)
        if m:
            return m.group(1)
    except Exception:
        pass
    return "theory"


async def _gen_one_point(llm, prompt: str, retries: int, delay: int, debug: bool = False, tag: str = "generate") -> str:
    last = ""
    for _ in range(max(1, retries)):
        try:
            if debug:
                logging.getLogger(__name__).debug("\n==== LLM Prompt [%s] BEGIN ====\n%s\n==== LLM Prompt [%s] END ====\n", tag, prompt, tag)
            last = await llm.ainvoke(prompt)
            if last:
                return last
        except Exception as e:
            logging.getLogger(__name__).error(f"生成调用失败: {e}")
        await asyncio.sleep(max(1, delay))
    return last


async def _review_one_point_with_context(llm, point_id: str, content_md: str, peer_points: List[Dict[str, str]], debug: bool = False) -> Dict[str, Any]:
    review_prompt_template = '''你是资深的技术编辑，你的任务是审查下面的草稿，并以JSON格式提供具体的、可操作的反馈。

【审查维度】
1. 准确性: 内容与代码是否技术上准确？
2. 清晰度: 解释是否易懂？示例是否清晰？
3. 完整性: 是否遗漏关键概念或步骤？
4. 一致性: 是否与标题及其在课程大纲中的定位相符？

【分类要求（非常重要）】
对每个问题进行分类，并估计信心度(confidence: 0~1)。分类category仅能取以下值之一：
- formatting, typo, heading, link_fix, reference, style, redundancy, minor_clarity, minor_structure, example_polish,
- factual_error, code_bug, algorithm_logic, security, api_breaking_change

【输出格式（仅输出一个JSON对象，无任何额外文本）】
顶层键：
- is_perfect: 布尔；若无需任何修改则为 true。
- issues: 数组；若 is_perfect=true 则为空数组。

每个 issue 必须包含：
- severity: 'major' | 'minor'
- category: 上述分类之一
- confidence: 0~1 之间的小数
- description: 字符串，问题描述
- suggestion: 字符串，具体且可执行的修复建议

【上下文】
[文件ID] {point_id}
[同章节其他知识点]
{peers_lines}

【当前内容】
{content_md}

【你的JSON输出】
'''
    peers_lines = "\n".join([f"- {p.get('id', '')}: {p.get('title', '')}" for p in peer_points])
    prompt = review_prompt_template.format(point_id=point_id, peers_lines=peers_lines if peers_lines else '(无)', content_md=content_md)
    if debug:
        logging.getLogger(__name__).debug("\n==== LLM Prompt [review] BEGIN ====\n%s\n==== LLM Prompt [review] END ====\n", prompt)
    try:
        text = await llm.ainvoke(prompt)
        obj = try_parse_json_object(text)
        if obj:
            obj.setdefault("file_id", point_id)
            return obj
    except Exception as e:
        logging.getLogger(__name__).error(f"带上下文审查失败: {e}")
    return {
        "file_id": point_id,
        "is_perfect": False,
        "issues": [{
            "severity": "major",
            "description": "审查节点执行或JSON解析失败。",
            "suggestion": "请检查上游内容或审查模型的输出是否稳定。"
        }]
    }


def _severity_score(item: Dict[str, Any]) -> int:
    if item.get("is_perfect", False):
        return 0
    score = 0
    for issue in item.get("issues", []) or []:
        if issue.get("severity") == "major":
            score += 2
        else:
            score += 1
    return score


def _has_non_ok(item: Dict[str, Any]) -> bool:
    if item.get("is_perfect", False):
        return False
    return bool(item.get("issues"))


AUTO_APPLY_DEFAULTS = {
    "auto_apply_mode": "off",  # off | safe | aggressive | all
    "auto_apply_threshold_major": 0.8,
}


def _should_auto_apply_by_review(cfg: Dict[str, Any], review_obj: Dict[str, Any]) -> Tuple[bool, str]:
    mode = str(cfg.get("auto_apply_mode") or AUTO_APPLY_DEFAULTS["auto_apply_mode"]).strip().lower()
    if mode == "off":
        return False, "off"
    if mode == "all":
        return True, "all"
    issues = review_obj.get("issues") if isinstance(review_obj.get("issues"), list) else []
    if review_obj.get("is_perfect", False) and not issues:
        return False, "is_perfect"
    majors_conf: List[float] = []
    for it in issues:
        if isinstance(it, dict) and str(it.get("severity", "")).lower() == "major":
            try:
                majors_conf.append(float(it.get("confidence", 1)))
            except Exception:
                majors_conf.append(0.0)
    if mode == "safe":
        ok = len(majors_conf) == 0
        return ok, "safe: all minor" if ok else "safe: has major"
    if mode == "aggressive":
        if not majors_conf:
            return True, "aggressive: all minor"
        thr = float(cfg.get("auto_apply_threshold_major", AUTO_APPLY_DEFAULTS["auto_apply_threshold_major"]))
        ok = min(majors_conf) >= thr
        return ok, (f"aggressive: majors_conf>={thr}" if ok else f"aggressive: majors_conf<{thr}")
    return False, f"unknown_mode:{mode}"


def _render_unified_diff(old: str, new: str, context_lines: int = 3, max_output_lines: int = 120) -> str:
    import difflib
    old_lines = (old or "").splitlines()
    new_lines = (new or "").splitlines()
    diff = list(difflib.unified_diff(old_lines, new_lines, fromfile="原稿", tofile="修订", lineterm="", n=context_lines))
    if len(diff) > max_output_lines:
        head = diff[: max_output_lines // 2]
        tail = diff[-max_output_lines // 2 :]
        diff = head + ["...（diff 省略）..."] + tail
    return "\n".join(diff)


async def _propose_fix(
    llm,
    point_id: str,
    point_title: str,
    topic: str,
    outline_md: str,
    current_md: str,
    review: Dict[str, Any],
    prior_proposal: Optional[Dict[str, Any]] = None,
    user_feedback: str = "",
    debug: bool = False,
) -> Dict[str, Any]:
    constraints = (
        "请仅输出一个 JSON 对象，不要任何额外文字；键：\n"
        "- summary: 对需要修改点与改动的简要说明（中文，100-200字）；\n"
        "- revised_content: 修订后的完整 Markdown 内容（必须是完整替换稿而非片段）；\n"
        "- risk (可选): 'low'|'medium'|'high'；\n"
        "- change_categories (可选): 数组，参考审查分类；\n"
        "- notes (可选): 对修复范围的简短说明。"
    )
    feedback_part = f"\n[用户反馈]\n{user_feedback}\n" if user_feedback else ""
    prior_part = f"\n[上一版修复方案]\n{json.dumps(prior_proposal, ensure_ascii=False)}\n" if prior_proposal else ""
    prompt = (
        "你是严谨的技术编辑与作者。基于以下上下文，提出修复提案并给出修订后完整内容。\n\n"
        f"[主题]\n{topic}\n\n"
        f"[知识点]\n{point_title} (ID: {point_id})\n\n"
        f"[大纲]\n{outline_md}\n\n"
        f"[当前内容]\n{current_md}\n\n"
        f"[审查结果]\n{json.dumps(review, ensure_ascii=False)}\n"
        f"{prior_part}{feedback_part}\n"
        f"{constraints}\n"
    )
    if debug:
        logging.getLogger(__name__).debug("\n==== LLM Prompt [propose_fix] BEGIN ====\n%s\n==== LLM Prompt [propose_fix] END ====\n", prompt)
    try:
        text = await llm.ainvoke(prompt)
        obj = try_parse_json_object(text)
        if isinstance(obj, dict) and obj.get("revised_content"):
            return obj
    except Exception as e:
        logging.getLogger(__name__).error(f"生成修复方案失败: {e}")
    return {
        "summary": "自动生成修复方案失败，建议人工检查并完善。",
        "revised_content": current_md or "",
    }


# ----------------------------
# 节点（复制版）
# ----------------------------

async def generate_and_review_by_chapter_node(state: WorkState, llm_generate, llm_review) -> WorkState:
    cfg = state.get("config", {})
    max_parallel = int(cfg.get("max_parallel_requests", 8))
    retries = int(cfg.get("retry_times", 3))
    delay = int(cfg.get("retry_delay", 10))
    sem = asyncio.Semaphore(max_parallel)

    outline = state.get("outline_struct", {}) or {}
    topic = state.get("topic", "")
    language = str((state.get("topic_meta", {}) or {}).get("lang", "zh"))

    # path 映射 id -> 可读路径
    path_by_id: Dict[str, str] = {}
    chapters_struct = outline.get("chapters") or []
    for ci, ch in enumerate(chapters_struct, start=1):
        ch_title = ch.get("title", f"第{ci}章")
        for gi, gr in enumerate(ch.get("groups") or [], start=1):
            gr_title = gr.get("title", f"{ci}.{gi} 小节")
            for si, sec in enumerate(gr.get("sections") or [], start=1):
                sid = sec.get("id") or ""
                stitle = sec.get("title") or f"{ci}.{gi}.{si}"
                if sid:
                    path_by_id[sid] = f"{topic} / {gr_title} / {stitle}"

    chapters_ordered = chapters_struct
    selected_titles = state.get("selected_chapters") or [c.get("title", "") for c in chapters_ordered]

    # autosave 目录
    topic_slug = state.get("topic_slug", "topic")
    out_dir = BASE_DIR / "output" / topic_slug
    drafts_dir = out_dir / "drafts"
    reviews_dir = out_dir / "reviews"
    ensure_dir(drafts_dir)
    ensure_dir(reviews_dir)

    drafts_all: List[Dict[str, str]] = []
    reviews_all: List[Dict[str, Any]] = []
    failures_all: List[Dict[str, Any]] = []

    async def _process_one_group(ci: int, gi: int, ch: Dict[str, Any], gr: Dict[str, Any]) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        ch_title = ch.get("title", f"第{ci}章")
        # 按用户选择的章节进行过滤
        if selected_titles and ch_title not in selected_titles:
            return [], [], []
        gr_title = gr.get("title", f"{ci}.{gi} 小节")
        stype = str(gr.get("structure_type", "toolbox")).strip().lower()
        sections = gr.get("sections") or []
        if not sections:
            return [], [], []

        logging.getLogger(__name__).info(f"  └─ 小节：{gr_title} 结构={stype}，知识点={len(sections)}")

        group_drafts: Dict[str, str] = {}
        # Generation
        if stype == "pipeline":
            group_context = ""
            for si, sec in enumerate(sections, start=1):
                sid = sec.get("id") or ""
                stitle = sec.get("title") or f"{ci}.{gi}.{si}"
                primary_goal = sec.get("primary_goal") or sec.get("goal") or ""
                mods = sec.get("suggested_modules") if isinstance(sec.get("suggested_modules"), list) else []
                conts = sec.get("suggested_contents") if isinstance(sec.get("suggested_contents"), list) else []
                if si == 1:
                    prompt = _build_theory_opening_prompt(
                        topic=topic,
                        language=language,
                        path=path_by_id.get(sid, ""),
                        section_title=stitle,
                        primary_goal=str(primary_goal),
                        suggested_modules=mods if isinstance(mods, list) else [],
                        suggested_contents=conts,
                        current_chapter_index=ci,
                        all_chapters_struct=chapters_struct,
                    )
                else:
                    prompt = _build_contextual_content_prompt(
                        topic=topic,
                        language=language,
                        path=path_by_id.get(sid, ""),
                        section_title=stitle,
                        primary_goal=str(primary_goal),
                        suggested_modules=mods if isinstance(mods, list) else [],
                        suggested_contents=conts,
                        structure_type="pipeline",
                        relation_to_previous=str(sec.get("relation_to_previous") or ""),
                        prior_context=group_context,
                    )
                async with sem:
                    txt = await _gen_one_point(llm_generate, prompt, retries, delay, debug=bool(cfg.get("debug")), tag="generate")
                if cfg.get("sanitize_mermaid", True):
                    txt_s, _issues = sanitize_mermaid_in_markdown(txt or "")
                else:
                    txt_s = txt or ""
                group_drafts[sid] = txt_s
                if txt_s:
                    group_context = (group_context + "\n\n" + txt_s).strip()
                try:
                    (drafts_dir / f"{sid}.md").write_text(txt_s, encoding="utf-8")
                except Exception:
                    pass
        else:
            indices = list(range(len(sections)))
            def _rel(i: int) -> str:
                return str((sections[i] or {}).get("relation_to_previous", "")).strip().lower()

            roots = [i for i in indices if _rel(i) in {"first_in_sequence", "tool_in_toolbox", "alternative_to", ""}]
            pending = [i for i in indices if i not in roots]

            async def _gen_root(i: int):
                sec = sections[i]
                sid = sec.get("id") or ""
                stitle = sec.get("title") or ""
                primary_goal = sec.get("primary_goal") or sec.get("goal") or ""
                mods = sec.get("suggested_modules") if isinstance(sec.get("suggested_modules"), list) else []
                conts = sec.get("suggested_contents") if isinstance(sec.get("suggested_contents"), list) else []
                base = _build_contextual_content_prompt(
                    topic=topic,
                    language=language,
                    path=path_by_id.get(sid, ""),
                    section_title=stitle,
                    primary_goal=str(primary_goal),
                    suggested_modules=mods,
                    suggested_contents=conts,
                    structure_type="toolbox",
                    prior_context="",
                )
                async with sem:
                    txt = await _gen_one_point(llm_generate, base, retries, delay, debug=bool(cfg.get("debug")), tag="generate")
                if cfg.get("sanitize_mermaid", True):
                    txt_s, _issues = sanitize_mermaid_in_markdown(txt or "")
                else:
                    txt_s = txt or ""
                group_drafts[sid] = txt_s
                try:
                    (drafts_dir / f"{sid}.md").write_text(txt_s, encoding="utf-8")
                except Exception:
                    pass

            if roots:
                await asyncio.gather(*[_gen_root(i) for i in roots])

            produced_set = set([sections[i].get("id") for i in roots])
            loop_guard = 0
            while pending and loop_guard < len(sections) * 2:
                ready: List[int] = []
                for i in list(pending):
                    dep = _rel(i)
                    if dep not in {"builds_on", "deep_dive_into"}:
                        ready.append(i)
                        continue
                    parent_idx = i - 1
                    if parent_idx >= 0:
                        parent_id = sections[parent_idx].get("id")
                        if parent_id in produced_set:
                            ready.append(i)
                if not ready:
                    ready = pending[:]

                async def _gen_dep(i: int):
                    sec = sections[i]
                    sid = sec.get("id") or ""
                    stitle = sec.get("title") or ""
                    primary_goal = sec.get("primary_goal") or sec.get("goal") or ""
                    mods = sec.get("suggested_modules") if isinstance(sec.get("suggested_modules"), list) else []
                    conts = sec.get("suggested_contents") if isinstance(sec.get("suggested_contents"), list) else []
                    base = _build_contextual_content_prompt(
                        topic=topic,
                        language=language,
                        path=path_by_id.get(sid, ""),
                        section_title=stitle,
                        primary_goal=str(primary_goal),
                        suggested_modules=mods,
                        suggested_contents=conts,
                        structure_type="toolbox",
                        prior_context=group_drafts.get(sections[i-1].get("id"), "") if i > 0 else "",
                    )
                    async with sem:
                        txt = await _gen_one_point(llm_generate, base, retries, delay, debug=bool(cfg.get("debug")), tag="generate")
                    if cfg.get("sanitize_mermaid", True):
                        txt_s, _issues = sanitize_mermaid_in_markdown(txt or "")
                    else:
                        txt_s = txt or ""
                    group_drafts[sid] = txt_s
                    try:
                        (drafts_dir / f"{sid}.md").write_text(txt_s, encoding="utf-8")
                    except Exception:
                        pass

                await asyncio.gather(*[_gen_dep(i) for i in ready])
                for i in ready:
                    produced_set.add(sections[i].get("id"))
                    if i in pending:
                        pending.remove(i)
                loop_guard += 1

        # Reviews for this group (optional)
        group_reviews: List[Dict[str, Any]] = []
        if not cfg.get("skip_content_review", False):
            peer_meta = [{"id": sec.get("id"), "title": sec.get("title")} for sec in sections if sec.get("id")]
            async def _review_one_for_group(sec: Dict[str, Any]) -> Dict[str, Any]:
                pid = sec.get("id") or ""
                peers = [pm for pm in peer_meta if (pm.get("id") or "") != pid]
                content = group_drafts.get(pid, "")
                async with sem:
                    rv = await _review_one_point_with_context(llm_review, pid, content, peers, debug=bool(cfg.get("debug")))
                try:
                    (reviews_dir / f"{pid}.json").write_text(json.dumps(rv, ensure_ascii=False, indent=2), encoding="utf-8")
                except Exception:
                    pass
                return rv

            group_reviews = await asyncio.gather(*[_review_one_for_group(sec) for sec in sections if sec.get("id")])
        # Collect for this group
        drafts_list = []
        for sec in sections:
            sid = sec.get("id") or ""
            if sid:
                drafts_list.append({"id": sid, "content": group_drafts.get(sid, "")})
        failures_list = []
        for rv in group_reviews:
            if _severity_score(rv) >= 3:
                failures_list.append({"id": rv.get("file_id"), "review": rv})
        return drafts_list, group_reviews, failures_list

    async def _process_one_chapter(ci: int, ch: Dict[str, Any]) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        ch_title = ch.get("title", f"第{ci}章")
        if selected_titles and ch_title not in selected_titles:
            return [], [], []
        logging.getLogger(__name__).info(f"[结构感知] 处理章节：《{ch_title}》 …")
        groups = ch.get("groups") or []
        tasks = [
            _process_one_group(ci, gi, ch, gr)
            for gi, gr in enumerate(groups, start=1)
            if (gr.get("sections") or [])
        ]
        if not tasks:
            return [], [], []
        results = await asyncio.gather(*tasks)
        drafts_list: List[Dict[str, str]] = []
        reviews_list: List[Dict[str, Any]] = []
        failures_list: List[Dict[str, Any]] = []
        for d, r, f in results:
            drafts_list.extend(d)
            reviews_list.extend(r)
            failures_list.extend(f)
        return drafts_list, reviews_list, failures_list

    chapter_tasks = [
        _process_one_chapter(ci, ch)
        for ci, ch in enumerate(chapters_struct, start=1)
    ]
    if chapter_tasks:
        chapter_results = await asyncio.gather(*chapter_tasks)
        for d, r, f in chapter_results:
            drafts_all.extend(d)
            reviews_all.extend(r)
            failures_all.extend(f)

    return {**state, "drafts": drafts_all, "reviews": reviews_all, "failures": failures_all}


async def generate_and_review_by_chapter_node_tool(state: WorkState, llm_generate, llm_review) -> WorkState:
    """工具型主题版本：提示词采用 Prompt 2（工具类），并保持并发与上下文策略一致。"""
    cfg = state.get("config", {})
    max_parallel = int(cfg.get("max_parallel_requests", 8))
    retries = int(cfg.get("retry_times", 3))
    delay = int(cfg.get("retry_delay", 10))
    sem = asyncio.Semaphore(max_parallel)

    outline = state.get("outline_struct", {}) or {}
    topic = state.get("topic", "")
    language = str((state.get("topic_meta", {}) or {}).get("lang", "zh"))

    path_by_id: Dict[str, str] = {}
    chapters_struct = outline.get("chapters") or []
    for ci, ch in enumerate(chapters_struct, start=1):
        ch_title = ch.get("title", f"第{ci}章")
        for gi, gr in enumerate(ch.get("groups") or [], start=1):
            gr_title = gr.get("title", f"{ci}.{gi} 小节")
            for si, sec in enumerate(gr.get("sections") or [], start=1):
                sid = sec.get("id") or ""
                stitle = sec.get("title") or f"{ci}.{gi}.{si}"
                if sid:
                    path_by_id[sid] = f"{topic} / 第{ci}章：{ch_title} / {gr_title} / {stitle}"

    chapters_ordered = chapters_struct
    selected_titles = state.get("selected_chapters") or [c.get("title", "") for c in chapters_ordered]

    topic_slug = state.get("topic_slug", "topic")
    out_dir = BASE_DIR / "output" / topic_slug
    drafts_dir = out_dir / "drafts"
    reviews_dir = out_dir / "reviews"
    ensure_dir(drafts_dir)
    ensure_dir(reviews_dir)

    drafts_all: List[Dict[str, str]] = []
    reviews_all: List[Dict[str, Any]] = []
    failures_all: List[Dict[str, Any]] = []

    async def _process_one_group(ci: int, gi: int, ch: Dict[str, Any], gr: Dict[str, Any]) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        ch_title = ch.get("title", f"第{ci}章")
        # 按用户选择的章节进行过滤
        if selected_titles and ch_title not in selected_titles:
            return [], [], []
        gr_title = gr.get("title", f"{ci}.{gi} 小节")
        stype = str(gr.get("structure_type", "toolbox")).strip().lower()
        sections = gr.get("sections") or []
        if not sections:
            return [], [], []

        logging.getLogger(__name__).info(f"  └─ 小节：{gr_title} 结构={stype}，知识点={len(sections)} [tool-mode]")

        group_drafts: Dict[str, str] = {}
        if stype == "pipeline":
            group_context = ""
            for si, sec in enumerate(sections, start=1):
                sid = sec.get("id") or ""
                stitle = sec.get("title") or f"{ci}.{gi}.{si}"
                primary_goal = sec.get("primary_goal") or sec.get("goal") or ""
                mods = sec.get("suggested_modules") if isinstance(sec.get("suggested_modules"), list) else []
                conts = sec.get("suggested_contents") if isinstance(sec.get("suggested_contents"), list) else []
                prompt = _build_tool_content_prompt(
                    topic=topic,
                    language=language,
                    path=path_by_id.get(sid, ""),
                    section_title=stitle,
                    primary_goal=str(primary_goal),
                    suggested_modules=mods,
                    suggested_contents=conts,
                    structure_type="pipeline",
                    relation_to_previous=str(sec.get("relation_to_previous") or ""),
                    prior_context=group_context,
                )
                async with sem:
                    txt = await _gen_one_point(llm_generate, prompt, retries, delay, debug=bool(cfg.get("debug")), tag="generate")
                if cfg.get("sanitize_mermaid", True):
                    txt_s, _issues = sanitize_mermaid_in_markdown(txt or "")
                else:
                    txt_s = txt or ""
                group_drafts[sid] = txt_s
                if txt_s:
                    group_context = (group_context + "\n\n" + txt_s).strip()
                try:
                    (drafts_dir / f"{sid}.md").write_text(txt_s, encoding="utf-8")
                except Exception:
                    pass
        else:
            indices = list(range(len(sections)))
            def _rel(i: int) -> str:
                return str((sections[i] or {}).get("relation_to_previous", "")).strip().lower()

            roots = [i for i in indices if _rel(i) in {"first_in_sequence", "tool_in_toolbox", "alternative_to", ""}]
            pending = [i for i in indices if i not in roots]

            async def _gen_root(i: int):
                sec = sections[i]
                sid = sec.get("id") or ""
                stitle = sec.get("title") or ""
                primary_goal = sec.get("primary_goal") or sec.get("goal") or ""
                mods = sec.get("suggested_modules") if isinstance(sec.get("suggested_modules"), list) else []
                conts = sec.get("suggested_contents") if isinstance(sec.get("suggested_contents"), list) else []
                base = _build_tool_content_prompt(
                    topic=topic,
                    language=language,
                    path=path_by_id.get(sid, ""),
                    section_title=stitle,
                    primary_goal=str(primary_goal),
                    suggested_modules=mods,
                    suggested_contents=conts,
                    structure_type="toolbox",
                    prior_context="",
                )
                async with sem:
                    txt = await _gen_one_point(llm_generate, base, retries, delay, debug=bool(cfg.get("debug")), tag="generate")
                if cfg.get("sanitize_mermaid", True):
                    txt_s, _issues = sanitize_mermaid_in_markdown(txt or "")
                else:
                    txt_s = txt or ""
                group_drafts[sid] = txt_s
                try:
                    (drafts_dir / f"{sid}.md").write_text(txt_s, encoding="utf-8")
                except Exception:
                    pass

            if roots:
                await asyncio.gather(*[_gen_root(i) for i in roots])

            produced_set = set([sections[i].get("id") for i in roots])
            loop_guard = 0
            while pending and loop_guard < len(sections) * 2:
                ready: List[int] = []
                for i in list(pending):
                    dep = _rel(i)
                    if dep not in {"builds_on", "deep_dive_into"}:
                        ready.append(i)
                        continue
                    parent_idx = i - 1
                    if parent_idx >= 0:
                        parent_id = sections[parent_idx].get("id")
                        if parent_id in produced_set:
                            ready.append(i)
                if not ready:
                    ready = pending[:]

                async def _gen_dep(i: int):
                    sec = sections[i]
                    sid = sec.get("id") or ""
                    stitle = sec.get("title") or ""
                    primary_goal = sec.get("primary_goal") or sec.get("goal") or ""
                    mods = sec.get("suggested_modules") if isinstance(sec.get("suggested_modules"), list) else []
                    conts = sec.get("suggested_contents") if isinstance(sec.get("suggested_contents"), list) else []
                    parent_txt = ""
                    if i - 1 >= 0:
                        parent_id = sections[i-1].get("id") or ""
                        parent_txt = group_drafts.get(parent_id, "")
                    prompt = _build_tool_content_prompt(
                        topic=topic,
                        language=language,
                        path=path_by_id.get(sid, ""),
                        section_title=stitle,
                        primary_goal=str(primary_goal),
                        suggested_modules=mods,
                        suggested_contents=conts,
                        structure_type="toolbox",
                        relation_to_previous=_rel(i),
                        prior_context=parent_txt,
                    )
                    async with sem:
                        txt = await _gen_one_point(llm_generate, prompt, retries, delay, debug=bool(cfg.get("debug")), tag="generate")
                    if cfg.get("sanitize_mermaid", True):
                        txt_s, _issues = sanitize_mermaid_in_markdown(txt or "")
                    else:
                        txt_s = txt or ""
                    group_drafts[sid] = txt_s
                    try:
                        (drafts_dir / f"{sid}.md").write_text(txt_s, encoding="utf-8")
                    except Exception:
                        pass

                await asyncio.gather(*[_gen_dep(i) for i in ready])
                for i in ready:
                    produced_set.add(sections[i].get("id"))
                    if i in pending:
                        pending.remove(i)
                loop_guard += 1

        group_reviews: List[Dict[str, Any]] = []
        if not cfg.get("skip_content_review", False):
            peer_meta = [{"id": sec.get("id"), "title": sec.get("title")} for sec in sections if sec.get("id")]
            async def _review_one_for_group(sec: Dict[str, Any]) -> Dict[str, Any]:
                pid = sec.get("id") or ""
                peers = [pm for pm in peer_meta if (pm.get("id") or "") != pid]
                content = group_drafts.get(pid, "")
                async with sem:
                    rv = await _review_one_point_with_context(llm_review, pid, content, peers, debug=bool(cfg.get("debug")))
                try:
                    (reviews_dir / f"{pid}.json").write_text(json.dumps(rv, ensure_ascii=False, indent=2), encoding="utf-8")
                except Exception:
                    pass
                return rv
            group_reviews = await asyncio.gather(*[_review_one_for_group(sec) for sec in sections if sec.get("id")])

        drafts_list = []
        for sec in sections:
            sid = sec.get("id") or ""
            if sid:
                drafts_list.append({"id": sid, "content": group_drafts.get(sid, "")})
        failures_list = []
        for rv in group_reviews:
            if _severity_score(rv) >= 3:
                failures_list.append({"id": rv.get("file_id"), "review": rv})
        return drafts_list, group_reviews, failures_list

    async def _process_one_chapter(ci: int, ch: Dict[str, Any]) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        ch_title = ch.get("title", f"第{ci}章")
        if selected_titles and ch_title not in selected_titles:
            return [], [], []
        logging.getLogger(__name__).info(f"[结构感知] 处理章节：《{ch_title}》 [tool-mode] …")
        groups = ch.get("groups") or []
        tasks = [
            _process_one_group(ci, gi, ch, gr)
            for gi, gr in enumerate(groups, start=1)
            if (gr.get("sections") or [])
        ]
        if not tasks:
            return [], [], []
        results = await asyncio.gather(*tasks)
        drafts_list: List[Dict[str, str]] = []
        reviews_list: List[Dict[str, Any]] = []
        failures_list: List[Dict[str, Any]] = []
        for d, r, f in results:
            drafts_list.extend(d)
            reviews_list.extend(r)
            failures_list.extend(f)
        return drafts_list, reviews_list, failures_list

    chapter_tasks = [
        _process_one_chapter(ci, ch)
        for ci, ch in enumerate(chapters_struct, start=1)
    ]
    if chapter_tasks:
        chapter_results = await asyncio.gather(*chapter_tasks)
        for d, r, f in chapter_results:
            drafts_all.extend(d)
            reviews_all.extend(r)
            failures_all.extend(f)

    return {**state, "drafts": drafts_all, "reviews": reviews_all, "failures": failures_all}


async def propose_and_apply_fixes_node(state: WorkState, llm) -> WorkState:
    cfg_in = state.get("config", {}) or {}
    if cfg_in.get("skip_fixes", False):
        logging.getLogger(__name__).info("已跳过修复提案与自动应用（--skip-fixes）")
        return {**state, "fix_proposals": [], "fix_applied": [], "fix_skipped": [], "fix_iterations": []}
    cfg: Dict[str, Any] = {**AUTO_APPLY_DEFAULTS, **cfg_in}
    max_rounds = int(cfg.get("max_fix_rounds", 3))

    topic = state.get("topic", "")
    outline_md = state.get("outline_final_md", "")

    draft_by_id: Dict[str, str] = {d.get("id", ""): d.get("content", "") for d in (state.get("drafts") or [])}
    reviews_in = state.get("reviews", []) or []
    reviews_by_id: Dict[str, Dict[str, Any]] = {}
    for rv in reviews_in:
        rid = str(rv.get("file_id") or rv.get("id") or "").strip()
        if not rid:
            continue
        reviews_by_id[rid] = rv

    title_by_id: Dict[str, str] = {p.id: p.title for p in (state.get("points") or [])}

    fix_proposals: List[Dict[str, Any]] = []
    fix_applied: List[str] = []
    fix_skipped: List[str] = []
    fix_iterations: List[Dict[str, Any]] = []
    auto_stats = {
        "mode": cfg.get("auto_apply_mode"),
        "applied": 0,
        "skipped": 0,
        "reasons": [],
    }

    target_ids = [pid for pid, rv in reviews_by_id.items() if _has_non_ok(rv)]
    if not target_ids:
        logging.getLogger(__name__).info("所有知识点审查均为 OK，无需修复。")
        return {**state, "fix_proposals": [], "fix_applied": [], "fix_skipped": [], "fix_iterations": []}
    logging.getLogger(__name__).info(f"发现 {len(target_ids)} 个需要修复的知识点（任一维度非 OK）。")

    auto_ids: List[str] = []
    auto_reasons: Dict[str, str] = {}
    if (cfg.get("auto_apply_mode") or "off") != "off":
        for pid in target_ids:
            rv = reviews_by_id.get(pid, {})
            ok, why = _should_auto_apply_by_review(cfg, rv)
            if ok:
                auto_ids.append(pid)
                auto_reasons[pid] = why
            else:
                auto_stats["reasons"].append(f"skip {pid}: {why}")
        logging.getLogger(__name__).info(
            f"自动应用策略开启: mode={cfg.get('auto_apply_mode')} | major_threshold={cfg.get('auto_apply_threshold_major', 0.8)}"
        )

    applied_set = set()

    sem_apply = asyncio.Semaphore(int(cfg.get("max_parallel_requests", 8)))

    async def _gen_and_apply(pid: str, auto_flag: bool, reason: str = ""):
        nonlocal fix_proposals, fix_applied, fix_iterations
        title = title_by_id.get(pid, pid)
        current = draft_by_id.get(pid, "")
        review = reviews_by_id.get(pid, {})
        async with sem_apply:
            proposal = await _propose_fix(llm, pid, title, topic, outline_md, current, review, debug=bool(cfg.get("debug")))
        revised = proposal.get("revised_content") or current
        if cfg.get("sanitize_mermaid", True):
            revised, _issues = sanitize_mermaid_in_markdown(revised)
        draft_by_id[pid] = revised
        fix_applied.append(pid)
        fix_iterations.append({"id": pid, "iterations": 1})
        applied_set.add(pid)
        fix_proposals.append({"id": pid, "title": title, **proposal, "applied": True, "iterations": 1, "auto_applied": auto_flag, **({"auto_reason": reason} if auto_flag else {})})

    if auto_ids:
        await asyncio.gather(*[_gen_and_apply(pid, True, auto_reasons.get(pid, "")) for pid in auto_ids])

    pending_ids = [pid for pid in target_ids if pid not in applied_set]
    if pending_ids:
        # 非交互环境：默认跳过，只记录（与 run_full 行为一致）
        fix_skipped.extend(pending_ids)

    out_drafts = []
    for d in (state.get("drafts") or []):
        pid = d.get("id", "")
        if pid in draft_by_id:
            out_drafts.append({"id": pid, "content": draft_by_id[pid]})
        else:
            out_drafts.append(d)

    return {
        **state,
        "drafts": out_drafts,
        "fix_proposals": fix_proposals,
        "fix_applied": fix_applied,
        "fix_skipped": fix_skipped,
        "fix_iterations": fix_iterations,
        "auto_apply_stats": auto_stats,
    }


def save_and_publish_node(state: WorkState) -> WorkState:
    topic_slug = state.get("topic_slug", "topic")
    out_dir = CONTENT_ROOT / topic_slug
    ensure_dir(out_dir)
    publish_paths: List[str] = []
    cfg = state.get("config", {}) or {}
    fname_style = str(cfg.get("filename_style", "id")).strip().lower()
    title_by_id: Dict[str, str] = {p.id: p.title for p in (state.get("points") or [])}
    for item in state.get("drafts", []) or []:
        pid = item.get("id", "")
        content = item.get("content", "")
        if cfg.get("sanitize_mermaid", True):
            content, _issues = sanitize_mermaid_in_markdown(content)
        # 文件命名规则：
        # - 若配置为 structured，沿用原结构化命名
        # - 否则（默认）：使用 id + 清理后的标题（去掉前缀编号与尾部英文括注）
        if fname_style == "structured":
            name = _make_filename(pid, title_by_id.get(pid, ""), fname_style)
        else:
            title_clean = _clean_title_for_filename(title_by_id.get(pid, ""))
            name = f"{pid}-{title_clean}.md" if title_clean else f"{pid}.md"
        p = out_dir / name
        try:
            p.write_text(content, encoding="utf-8")
            publish_paths.append(str(p.relative_to(BASE_DIR)))
            logging.getLogger(__name__).info(f"已保存: {p}")
        except Exception as e:
            logging.getLogger(__name__).error(f"保存失败 {p}: {e}")
    outline_md = state.get("outline_final_md", "")
    if outline_md:
        outline_dir = CONTENT_ROOT / topic_slug
        ensure_dir(outline_dir)
        outline_path = outline_dir / f"{topic_slug}-learning-path.md"
        try:
            outline_path.write_text(outline_md, encoding="utf-8")
            publish_paths.append(str(outline_path.relative_to(BASE_DIR)))
            logging.getLogger(__name__).info(f"大纲已保存: {outline_path}")
        except Exception as e:
            logging.getLogger(__name__).error(f"保存大纲失败 {outline_path}: {e}")
    return {**state, "publish_paths": publish_paths}


def gather_and_report_node(state: WorkState) -> WorkState:
    reviews_in = state.get("reviews", []) or []
    reviews_by_id: Dict[str, Dict[str, Any]] = {}
    for rv in reviews_in:
        rid = str(rv.get("file_id") or rv.get("id") or "").strip()
        if not rid:
            continue
        reviews_by_id[rid] = rv

    failures_unique: List[Dict[str, Any]] = []
    non_ok_ids: List[str] = []
    for rid, rv in reviews_by_id.items():
        if _severity_score(rv) >= 3:
            failures_unique.append({"id": rid, "review": rv})
        if _has_non_ok(rv):
            non_ok_ids.append(rid)

    ok_cnt = len(reviews_by_id) - len(non_ok_ids)
    topic_slug = state.get("topic_slug", "topic")

    fix_proposals = state.get("fix_proposals", []) or []
    fix_applied = set(state.get("fix_applied", []) or [])
    fix_skipped = set(state.get("fix_skipped", []) or [])
    title_by_id: Dict[str, str] = {p.id: p.title for p in (state.get("points") or [])}

    report = [
        f"# 生成与审查报告（{topic_slug}）",
        "",
        f"- 总计生成: {len(reviews_by_id)}",
        f"- 通过（全OK）: {ok_cnt}",
        f"- 需修复（任一维度非OK）: {len(non_ok_ids)}",
        "",
        "## 失败项（旧阈值，供参考）",
    ]
    for f in failures_unique:
        rid = f.get("id")
        rv = f.get("review", {})
        report.append(f"- {rid}: {json.dumps(rv, ensure_ascii=False)}")

    if fix_proposals:
        report.append("")
        report.append("## 修复与处理情况")
        for fp in fix_proposals:
            rid = fp.get("id", "")
            title = fp.get("title", "")
            applied = fp.get("applied", False)
            iterations = fp.get("iterations", 1)
            summary = fp.get("summary", "")
            status = "已应用" if applied else ("已跳过" if rid in fix_skipped else "未应用")
            auto_flag = "(自动)" if fp.get("auto_applied") else ""
            report.append(f"- {rid} | {title} | {status}{auto_flag} | 轮次: {iterations} | 摘要: {summary}")

    if state.get("fix_skipped"):
        proposed_ids = {fp.get("id", "") for fp in fix_proposals}
        skipped_only = [rid for rid in state.get("fix_skipped") if rid not in proposed_ids]
        if skipped_only:
            report.append("")
            report.append("## 待处理项（未应用）")
            for rid in skipped_only:
                title = title_by_id.get(rid, rid)
                report.append(f"- {rid} | {title}")

    auto_stats = state.get("auto_apply_stats", {}) or {}
    if auto_stats:
        report.append("")
        report.append("## 自动应用统计")
        report.append(f"- 模式: {auto_stats.get('mode')}")
        report.append(f"- 自动应用: {auto_stats.get('applied', 0)}")
        report.append(f"- 自动跳过: {auto_stats.get('skipped', 0)}")
        reasons = auto_stats.get("reasons") or []
        if reasons:
            report.append("")
            report.append("<details><summary>调试原因（前10条）</summary>")
            for r in reasons[:10]:
                report.append(f"- {r}")
            report.append("</details>")

    report_md = "\n".join(report)
    out = BASE_DIR / f"pipeline_report_{topic_slug}.md"
    try:
        out.write_text(report_md, encoding="utf-8")
        logging.getLogger(__name__).info(f"报告已写出: {out}")
    except Exception:
        pass
    return {**state, "report_md": report_md}


# ----------------------------
# reconstructed_outline → outline_struct 映射
# ----------------------------

def _convert_reconstructed_to_outline_struct(subject: str, reconstructed: Dict[str, Any], topic_slug_hint: Optional[str] = None) -> Dict[str, Any]:
    topic = subject or reconstructed.get("title") or "主题"
    # 优先使用上游产出的 slug（reconstructed.meta.topic_slug → 传入 hint → 本地回退）
    topic_slug_meta = None
    try:
        meta_obj = reconstructed.get("meta") if isinstance(reconstructed, dict) else None
        if isinstance(meta_obj, dict):
            tsm = meta_obj.get("topic_slug")
            if isinstance(tsm, str) and tsm.strip():
                topic_slug_meta = tsm.strip()
    except Exception:
        topic_slug_meta = None
    topic_slug = topic_slug_meta or (topic_slug_hint or slugify(topic))
    groups_in: List[Dict[str, Any]] = reconstructed.get("groups") or []
    chapters: List[Dict[str, Any]] = []
    for ci, ch in enumerate(groups_in, start=1):
        ch_title = ch.get("title") or f"第{ci}章"
        ch_id = ch.get("id") or f"outline-ch-{ci}"
        stype = (ch.get("structure_type") or "toolbox").strip().lower()
        secs = ch.get("sections") or []
        group = {
            "title": ch_title,
            "id": f"{ch_id}-gr-1",
            "structure_type": stype,
            "sections": [],
        }
        for si, sec in enumerate(secs, start=1):
            group["sections"].append({
                "id": sec.get("id") or f"{topic_slug}-sec-{ci}-1-{si}",
                "title": sec.get("title") or f"{ci}.1.{si}",
                "relation_to_previous": sec.get("relation_to_previous") or "",
                "primary_goal": sec.get("primary_goal") or sec.get("goal") or "",
                "suggested_modules": sec.get("suggested_modules") if isinstance(sec.get("suggested_modules"), list) else [],
                "suggested_contents": sec.get("suggested_contents") if isinstance(sec.get("suggested_contents"), list) else [],
            })
        chapters.append({"title": ch_title, "id": ch_id, "groups": [group]})
    return {"meta": {"topic": topic, "topic_slug": topic_slug}, "chapters": chapters}


def _points_from_struct(data: Dict[str, Any]) -> List[Point]:
    pts: List[Point] = []
    for ch in (data.get("chapters") or []):
        ch_title = ch.get("title", "")
        for gr in (ch.get("groups") or []):
            gr_title = gr.get("title", "")
            for sec in (gr.get("sections") or []):
                pid = sec.get("id") or ""
                ptitle = sec.get("title") or ""
                if pid and ptitle:
                    pts.append(Point(id=str(pid), title=str(ptitle), chapter=str(ch_title), section=str(gr_title)))
    return pts


def _parse_selected(spec: Optional[str], total: int) -> List[int]:
    if not spec:
        return list(range(1, total + 1))
    out: List[int] = []
    for part in spec.split(','):
        p = (part or '').strip()
        if not p:
            continue
        if '-' in p:
            a, b = p.split('-', 1)
            if a.strip().isdigit() and b.strip().isdigit():
                lo, hi = int(a), int(b)
                if lo <= hi:
                    out.extend(list(range(lo, hi + 1)))
        elif p.isdigit():
            out.append(int(p))
    uniq = sorted({i for i in out if 1 <= i <= total})
    return uniq or list(range(1, total + 1))


# ----------------------------
# 主流程
# ----------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Generate chapters (standalone nodes) from integrated reconstructed_outline")
    ap.add_argument("--input", required=True, help="包含 reconstructed_outline 的 JSON 文件路径")
    ap.add_argument("--config", default=str(BASE_DIR / "config.json"), help="配置文件路径（默认 config.json）")
    ap.add_argument("--selected-chapters", default=None, help="选择的章节编号（如 1,3-4；留空为全部）")
    ap.add_argument("--max-parallel", type=int, default=None, help="并行上限（覆盖配置）")
    ap.add_argument("--skip-content-review", action="store_true", help="跳过知识点审查（更快）")
    ap.add_argument("--skip-fixes", action="store_true", help="跳过修复提案与自动应用")
    ap.add_argument("--auto-apply-mode", type=str, choices=["off", "safe", "aggressive", "all"], default=None, help="自动应用模式")
    ap.add_argument("--auto-apply-threshold-major", type=float, default=None, help="aggressive 模式下对 major 的最低信心阈值（默认 0.8）")
    ap.add_argument("--no-sanitize-mermaid", action="store_true", help="禁用 Mermaid 语法规范化修复（默认开启）")
    ap.add_argument("--output-subdir", type=str, default=None, help="输出子目录（默认 topic slug）")
    ap.add_argument("--debug", action="store_true", help="开启调试日志，输出模型与所有 LLM Prompt，并写入 output/<subdir>/log.txt")
    ap.add_argument("--subject-type", type=str, choices=["tool", "theory"], default=None, help="主题类型（覆盖自动分类）")
    ap.add_argument("--classify-llm-key", type=str, default=None, help="分类用 LLM 键名（覆盖 node_llm/classify_subject/default）")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )
    logger = logging.getLogger(__name__)

    # 读取输入
    p = Path(args.input)
    if not p.exists():
        logger.error(f"未找到输入文件: {p}")
        return 1
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"解析输入 JSON 失败: {e}")
        return 1

    reconstructed = data.get("reconstructed_outline") or {}
    if not reconstructed:
        logger.error("输入 JSON 缺少 reconstructed_outline 字段")
        return 1
    subject = data.get("subject") or reconstructed.get("title") or "主题"

    # 加载配置
    try:
        cfg = load_config(args.config)
    except Exception as e:
        logger.error(str(e))
        return 1
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        cfg["debug"] = True
    if args.max_parallel:
        cfg["max_parallel_requests"] = int(args.max_parallel)
    if args.skip_content_review:
        cfg["skip_content_review"] = True
    if args.skip_fixes:
        cfg["skip_fixes"] = True
    if args.auto_apply_mode is not None:
        cfg["auto_apply_mode"] = args.auto_apply_mode
    if args.auto_apply_threshold_major is not None:
        cfg["auto_apply_threshold_major"] = float(args.auto_apply_threshold_major)
    if args.no_sanitize_mermaid:
        cfg["sanitize_mermaid"] = False

    # 构造 outline_struct 与 points
    # 统一确定 topic_slug：优先 reconstructed.meta.topic_slug → 顶层 subject_slug → 回退 slugify(subject)
    topic_slug_hint = None
    try:
        meta_top = reconstructed.get("meta") if isinstance(reconstructed, dict) else None
        if isinstance(meta_top, dict):
            tsm = meta_top.get("topic_slug")
            if isinstance(tsm, str) and tsm.strip():
                topic_slug_hint = tsm.strip()
        if not topic_slug_hint:
            tsm2 = data.get("subject_slug") if isinstance(data, dict) else None
            if isinstance(tsm2, str) and tsm2.strip():
                topic_slug_hint = tsm2.strip()
    except Exception:
        topic_slug_hint = None

    outline_struct = _convert_reconstructed_to_outline_struct(subject, reconstructed, topic_slug_hint)
    points = _points_from_struct(outline_struct)

    topic_slug = outline_struct.get("meta", {}).get("topic_slug") or slugify(subject)
    output_subdir = args.output_subdir or topic_slug

    # Debug 文件输出
    if args.debug:
        try:
            dbg_dir = BASE_DIR / "output" / output_subdir
            ensure_dir(dbg_dir)
            dbg_path = dbg_dir / "log.txt"
            fh = logging.FileHandler(dbg_path, encoding="utf-8")
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            logging.getLogger().addHandler(fh)
            logger.debug(f"调试日志文件: {dbg_path}")
        except Exception as e:
            logger.warning(f"创建调试日志文件失败: {e}")

    # 记录模型路由
    def _resolve_llm_key_for_node(cfg: Dict[str, Any], node_key: str, subrole: Optional[str]) -> Optional[str]:
        mapping = cfg.get("node_llm", {}) or {}
        def _get(nk: str, sr: Optional[str]) -> Optional[str]:
            if sr:
                return mapping.get(f"{nk}.{sr}") or mapping.get(nk)
            return mapping.get(nk)
        name = _get(node_key, subrole)
        if not name and node_key == "generate_and_review_by_chapter":
            name = _get("generate_and_review_parallel", subrole)
        if not name:
            name = mapping.get("default")
        return name
    if args.debug:
        llms = cfg.get("llms", {}) or {}
        def _fmt_llm(k: str) -> str:
            ent = llms.get(k) if isinstance(llms, dict) else None
            if isinstance(ent, dict):
                prov = ent.get("provider") or ent.get("api_provider") or cfg.get("api_provider")
                model = ent.get("model") or cfg.get("model")
                return f"{k} (provider={prov}, model={model})"
            return f"{k} (provider={cfg.get('api_provider')}, model={cfg.get('model')})"
        logger.debug(f"使用生成模型: {_fmt_llm(_resolve_llm_key_for_node(cfg, 'generate_and_review_by_chapter', 'generate') or '<registry.default>')}")
        logger.debug(f"使用审查模型: {_fmt_llm(_resolve_llm_key_for_node(cfg, 'generate_and_review_by_chapter', 'review') or '<registry.default>')}")
        logger.debug(f"使用修复模型: {_fmt_llm(_resolve_llm_key_for_node(cfg, 'propose_and_apply_fixes', 'propose') or '<registry.default>')}")

    # 渲染大纲 Markdown（供修复提示使用）
    try:
        # 复用 generator 脚本的渲染逻辑会引入更多依赖；故这里直接生成简要大纲 Markdown
        lines: List[str] = []
        lines.append(f"# {outline_struct.get('meta', {}).get('topic', subject)} (id: {topic_slug})")
        chs = outline_struct.get("chapters") or []
        for ci, ch in enumerate(chs, start=1):
            lines.append("")
            lines.append(f"## 第{ci}章：{ch.get('title','')} (id: {ch.get('id')})")
            for gi, gr in enumerate(ch.get("groups") or [], start=1):
                lines.append(f"### {gr.get('title','')} (id: {gr.get('id')})")
                for si, sec in enumerate((gr.get("sections") or []), start=1):
                    lines.append(f"#### {sec.get('title','')} (id: {sec.get('id')})")
        outline_md = "\n".join(lines) + "\n"
    except Exception:
        outline_md = ""

    # 章节选择
    chapters = outline_struct.get("chapters") or []
    total = len(chapters)
    if total == 0:
        logger.error("未找到任何章节")
        return 1
    indices = _parse_selected(args.selected_chapters, total)
    selected_titles = [chapters[i-1].get("title", "") for i in indices]
    logger.info(f"选择章节: {indices} -> {[t or '未命名' for t in selected_titles]}")

    # 分类（优先 JSON -> CLI -> AI 分类）
    subject_type = (args.subject_type or "").strip().lower()
    if not subject_type:
        # 1) 优先从输入 JSON 中读取（reconstructed_outline.meta.subject_type 或 顶层 meta.subject_type）
        subject_type_json = None
        try:
            if isinstance(reconstructed, dict):
                meta_rec = reconstructed.get("meta")
                if isinstance(meta_rec, dict):
                    st = meta_rec.get("subject_type")
                    if isinstance(st, str):
                        subject_type_json = st.strip().lower()
            meta_top = data.get("meta") if isinstance(data, dict) else None
            if not subject_type_json and isinstance(meta_top, dict):
                st = meta_top.get("subject_type")
                if isinstance(st, str):
                    subject_type_json = st.strip().lower()
        except Exception:
            subject_type_json = None

        if subject_type_json in {"tool", "theory"}:
            subject_type = subject_type_json
            logger.info(f"主题分类（来自输入 JSON）：{subject} => {subject_type}")

    if not subject_type:
        # 2) AI 分类
        try:
            registry = build_llm_registry(cfg)
            llm_for_cls = None
            if args.classify_llm_key and args.classify_llm_key in registry:
                llm_for_cls = registry[args.classify_llm_key]
            else:
                llm_for_cls = select_llm_for_node(cfg, registry, "classify_subject")
            subject_type = asyncio.run(_classify_subject_async(llm_for_cls, subject))  # type: ignore
            if subject_type not in {"tool", "theory"}:
                subject_type = "theory"
            logger.info(f"主题分类：{subject} => {subject_type}")
        except Exception as e:
            logger.warning(f"主题分类失败，默认按 theory 处理：{e}")
            subject_type = "theory"

    # 初始状态
    state: WorkState = {
        "topic": subject,
        "topic_meta": {"lang": "zh"},
        "topic_slug": topic_slug,
        "config": cfg,
        "output_subdir": output_subdir,
        "outline_struct": outline_struct,
        "outline_final_md": outline_md,
        "points": points,
        "selected_chapters": selected_titles,
        "subject_type": subject_type,
    }

    # 构建 LLM 实例（生成、审查、修复）
    default_llm = init_llm(cfg)
    registry = build_llm_registry(cfg)
    def _pick(node: str, subrole: Optional[str] = None):
        return select_llm_for_node(cfg, registry, node, subrole) or default_llm

    gen_llm = _pick("generate_and_review_by_chapter", "generate")
    rev_llm = _pick("generate_and_review_by_chapter", "review")
    prop_llm = _pick("propose_and_apply_fixes", "propose")

    # 运行
    try:
        if subject_type == "tool":
            s1 = asyncio.run(generate_and_review_by_chapter_node_tool(state, gen_llm, rev_llm))
        else:
            s1 = asyncio.run(generate_and_review_by_chapter_node(state, gen_llm, rev_llm))
    except Exception as e:
        logger.error(f"生成/审查阶段失败: {e}")
        return 1

    try:
        s2 = asyncio.run(propose_and_apply_fixes_node(s1, prop_llm)) if not cfg.get("skip_fixes", False) else s1
    except Exception as e:
        logger.error(f"修复提案阶段失败: {e}")
        return 1

    s3 = save_and_publish_node(s2)
    s4 = gather_and_report_node(s3)

    report_md = s4.get("report_md", "")
    if report_md:
        print("\n✅ 完成。报告如下：\n")
        print(report_md)
    else:
        print("\n✅ 完成。无报告可显示。\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
