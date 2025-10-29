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
    --input output/integrated_pipeline/command-line-operations-reconstructed-20251029-175456.json \
    --config config.json \
    --skip-content-review \
    --debug

  python scripts/pipelines/generation/generate_chapters_from_integrated_standalone.py \
    --input output/reconstructed_outline/command-line-operations-reconstructed-20251029-175456.json \
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


from scripts.common.llm import build_llm_registry, select_llm_for_node, pick_llm, AsyncLLM as _AsyncLLM


def _prompt_from_catalog(key: str) -> str:
    try:
        from prompts.prompt_loader import get_prompt
    except Exception as exc:
        raise RuntimeError("无法导入 prompts.prompt_loader，请确认 prompts 目录可用。") from exc

    try:
        return get_prompt(key)
    except Exception as exc:
        raise RuntimeError(f"无法从 prompts/prompt_catalog_data.py 加载 Prompt '{key}': {exc}") from exc


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
    template = _prompt_from_catalog("gen.theory_content")
    path_block = f"【定位】{path}\n\n" if path else ""
    goal_text = primary_goal if primary_goal else "围绕当前知识点展开，高质量解释并给出必要示例。"
    goal_block = f"【教学目标】{goal_text}\n\n"
    mods = [m for m in (suggested_modules or []) if isinstance(m, str)]
    if mods:
        modules_block = f"【建议内容模块】{', '.join(mods)}\n\n"
    else:
        modules_block = "【建议内容模块】summary, code_example（如适合）, common_mistake_warning（如有）, diagram（如有因果/流程）\n\n"
    conts = [c for c in (suggested_contents or []) if isinstance(c, str)]
    contents_block = f"【核心内容】{', '.join(conts)}\n\n" if conts else ""

    if structure_type == "pipeline":
        if prior_context:
            quoted = prior_context.replace("\n", "\n> ")
            context_block = f"【已完成的小节内容（Context）】\n> {quoted}\n\n"
        else:
            context_block = ""
        task_block = (
            f"【你的任务】请严格遵循【写作风格与深度要求】，紧接上述内容，围绕“{section_title}”自然过渡并续写下一段。请以【核心内容】为基础，进行详尽地展开与阐述，确保讲解不仅系统、逻辑清晰，而且内容丰富、细节饱满、富有启发性。\n\n"
        )
    else:
        dep = (relation_to_previous or "").strip().lower()
        if prior_context and dep in {"builds_on", "deep_dive_into"}:
            quoted = prior_context.replace("\n", "\n> ")
            instruction = (
                "请在父级基础上深入讲解当前知识点，突出内在联系与扩展。"
                if dep == "deep_dive_into"
                else "请在父级基础上推进当前知识点，说明改进或新增能力。"
            )
            context_block = f"【父级知识点（Parent Context）】\n> {quoted}\n\n{instruction}\n\n"
        else:
            context_block = ""
        task_block = (
            f"【你的任务】请严格遵循【写作风格与深度要求】，撰写一篇关于“{section_title}”的独立教学段落。请以【核心内容】为基础，进行详尽地展开与阐述，确保讲解不仅系统、逻辑清晰，而且内容丰富、细节饱满、富有启发性。\n\n"
        )

    prompt = template.format(
        path_block=path_block,
        goal_block=goal_block,
        modules_block=modules_block,
        contents_block=contents_block,
        context_block=context_block,
        task_block=task_block,
    )
    return prompt.strip() + "\n"


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
    template = _prompt_from_catalog("gen.theory_content")
    path_block = f"【定位】{path}\n\n" if path else ""

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

    context_block = f"{context_str}\n\n" if context_str else ""
    goal_text = primary_goal if primary_goal else "围绕当前知识点展开，高质量解释并给出必要示例。"
    goal_block = f"【教学目标】{goal_text}\n\n"
    mods = [m for m in (suggested_modules or []) if isinstance(m, str)]
    if mods:
        modules_block = f"【建议内容模块】{', '.join(mods)}\n\n"
    else:
        modules_block = "【建议内容模块】summary, code_example（如适合）, common_mistake_warning（如有）, diagram（如有因果/流程）\n\n"

    conts = [c for c in (suggested_contents or []) if isinstance(c, str)]
    contents_block = f"【核心内容】{', '.join(conts)}\n\n" if conts else ""

    if current_chapter_index == 1:
        task_block = (
            f"【你的任务】请严格遵循【写作风格与深度要求】，作为一名该领域的专家，围绕“{section_title}”这个主题，撰写整个课程的开篇内容。"
            f"请以【核心内容】为基础，进行详尽地展开与阐述，确保讲解不仅系统、逻辑清晰，而且内容丰富、细节饱满、富有启发性，并为后续所有章节的学习做好铺垫。\n\n"
        )
    else:
        task_block = (
            f"【你的任务】请严格遵循【写作风格与深度要求】，作为一名该领域的专家，参考【全局目录概览】和【前文章节详解】。现在，请开启一个全新的章节，围绕“{section_title}”这一主题撰写开篇内容。"
            f"请以【核心内容】为基础，进行详尽地展开与阐述，确保讲解不仅系统、逻辑清晰，而且内容丰富、细节饱满、富有启发性，并为本章后续内容的学习做好铺垫。\n\n"
        )


    prompt = template.format(
        path_block=path_block,
        context_block=context_block,
        goal_block=goal_block,
        modules_block=modules_block,
        contents_block=contents_block,
        task_block=task_block
    )
    return prompt.strip() + "\n"




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
    template = _prompt_from_catalog("gen.tool_content")
    if lang.startswith("zh"):
        language_line = "【语言】中文"
    elif lang.startswith("en"):
        language_line = "【语言】English"
    else:
        language_line = f"【语言】{language}"
    mods = [m for m in (suggested_modules or []) if isinstance(m, str)]
    conts = [c for c in (suggested_contents or []) if isinstance(c, str)]
    design_obj = {
        "title": section_title,
        "id": "point",
        "primary_goal": primary_goal or "",
        "suggested_modules": mods,
        "suggested_contents": conts,
    }
    path_block = f"【定位】{path}\n\n" if path else ""

    if structure_type == "pipeline":
        if prior_context:
            quoted = (prior_context or "").replace("\n", "\n> ")
            context_block = (
                "【已完成的小节内容】\n"
                f"> {quoted}\n\n"
                "请在不重复以上内容的前提下，自然过渡并续写本节。\n\n"
            )
        else:
            context_block = ""
    else:
        dep = (relation_to_previous or "").strip().lower()
        if prior_context and dep in {"builds_on", "deep_dive_into"}:
            quoted = (prior_context or "").replace("\n", "\n> ")
            instruction = (
                "请在父级基础上深入讲解当前知识点，突出内在联系与扩展。"
                if dep == "deep_dive_into"
                else "请在父级基础上推进当前知识点，说明改进或新增能力。"
            )
            context_block = (
                "【父级知识点（Parent Context）】\n"
                f"> {quoted}\n\n"
                f"{instruction}\n\n"
            )
        else:
            context_block = ""

    prompt = template.format(
        topic=topic,
        path_block=path_block,
        design_json=json.dumps(design_obj, ensure_ascii=False, indent=2),
        context_block=context_block,
        language_line=language_line,
    )
    return prompt.strip() + "\n"


async def _classify_subject_async(llm, subject: str) -> str:
    template = _prompt_from_catalog("gen.classify_subject")
    prompt = template.format(subject=str(subject or ""))
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
    review_prompt_template = _prompt_from_catalog('review.default')
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
    template = _prompt_from_catalog("gen.fix_proposal")
    prior_block = ""
    if prior_proposal:
        prior_block = f"[上一版修复方案]\n{json.dumps(prior_proposal, ensure_ascii=False)}\n\n"
    feedback_block = f"[用户反馈]\n{user_feedback}\n\n" if user_feedback else ""
    prompt = template.format(
        topic=topic,
        point_title=point_title,
        point_id=point_id,
        outline_md=outline_md,
        current_md=current_md,
        review_json=json.dumps(review, ensure_ascii=False),
        extras_block=f"{prior_block}{feedback_block}",
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
                    draft_path = (drafts_dir / f"{sid}.md")
                    draft_path.write_text(txt_s, encoding="utf-8")
                    logging.getLogger(__name__).info(f"[已保存初稿] {draft_path}")
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
                    draft_path = (drafts_dir / f"{sid}.md")
                    draft_path.write_text(txt_s, encoding="utf-8")
                    logging.getLogger(__name__).info(f"[已保存初稿] {draft_path}")
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
                        draft_path = (drafts_dir / f"{sid}.md")
                        draft_path.write_text(txt_s, encoding="utf-8")
                        logging.getLogger(__name__).info(f"[已保存初稿] {draft_path}")
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
                    draft_path = drafts_dir / f"{sid}.md"
                    draft_path.write_text(txt_s, encoding="utf-8")
                    logging.getLogger(__name__).info(f"[已保存初稿] {draft_path}")
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
                    draft_path = drafts_dir / f"{sid}.md"
                    draft_path.write_text(txt_s, encoding="utf-8")
                    logging.getLogger(__name__).info(f"[已保存初稿] {draft_path}")
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
                        draft_path = drafts_dir / f"{sid}.md"
                        draft_path.write_text(txt_s, encoding="utf-8")
                        logging.getLogger(__name__).info(f"[已保存初稿] {draft_path}")
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
        ch_title = (
            ch.get("title")
            or ch.get("group_title")
            or f"第{ci}章"
        )
        ch_id = (
            ch.get("id")
            or ch.get("group_id")
            or f"outline-ch-{ci}"
        )
        stype_raw = (
            ch.get("structure_type")
            or ch.get("group_structure_type")
            or "toolbox"
        )
        stype = str(stype_raw).strip().lower()
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
    registry = build_llm_registry(cfg)
    default_llm = registry.get("default") or pick_llm(cfg, registry, None)
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
