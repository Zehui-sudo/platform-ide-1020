#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Classify knowledge points in a Markdown learning outline into
one of 9 archetypes + switches (feature flags).

Design goals:
- Zero external dependencies (pure stdlib).
- Robust-enough Markdown outline parsing (headings + bullets).
- Hybrid classifier: rules/keywords with optional LLM refinement hook.
- Clear, inspectable output (JSONL with rationale + confidence).

Archetypes (9):
- algorithm_impl             (算法实现 / Code Guide)
- math_derivation            (数学推导 / Proof)
- concept_exposition         (概念/框架阐释)
- api_quickstart             (API/工具速用)
- procedure_checklist        (流程/操作/Checklist)
- comparative_analysis       (比较与选型)
- case_study                 (案例/应用)
- architecture_design        (设计/架构)
- troubleshooting            (诊断/排错)

Output per knowledge point (JSON line):
{
  "id": 12,
  "text": "Async/Await",
  "path": ["JavaScript", "Concurrency", "Async/Await"],
  "archetype": "concept_exposition",
  "switches": {"include_code": true, "audience_level": "beginner"},
  "confidence": 0.78,
  "rationale": {"concept_exposition": ["概念", "基础"], "api_quickstart": ["示例"]}
}

Usage:
  python scripts/archetype_classifier.py path/to/outline.md \
    --output out.jsonl --pretty

Optional (disabled by default):
  --use-llm to enable LLM refinement if you have an accessible provider.
  This script won’t import any SDKs; see llm_refine() for instructions.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


# -----------------------------
# Markdown outline parsing
# -----------------------------


HEADING_RE = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<text>.+?)\s*$")
LIST_RE = re.compile(r"^(?P<indent>\s*)(?:[-*+]|\d+\.)\s+(?P<text>.+?)\s*$")
CODE_FENCE_RE = re.compile(r"^\s*```")


@dataclass
class Point:
    id: int
    text: str
    path: List[str]
    line_no: int


def parse_markdown_outline(path: str) -> List[Point]:
    """Parse headings + bullet lists from a Markdown outline.

    Heuristics:
    - Headings form the section path (H1..H6).
    - Bullet items (unordered/ordered) are treated as knowledge points.
    - Nested bullet depth is inferred from indentation (2+ spaces per level).
    - Code blocks (```) are ignored while scanning.
    """

    points: List[Point] = []
    headings_stack: List[str] = []  # e.g., [H1, H2, ...]
    bullets_stack: List[str] = []   # hierarchical bullet titles (not emitted)

    in_code_block = False
    next_id = 1

    def set_heading(level: int, title: str) -> None:
        # Ensure headings_stack size == level
        while len(headings_stack) >= level:
            headings_stack.pop()
        headings_stack.append(title.strip())

    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"[ERROR] File not found: {path}", file=sys.stderr)
        return []

    for idx, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")

        # Toggle code block state
        if CODE_FENCE_RE.match(line):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # Headings
        m = HEADING_RE.match(line)
        if m:
            level = len(m.group("hashes"))
            title = m.group("text").strip()
            set_heading(level, title)
            bullets_stack.clear()  # reset bullets on new heading
            continue

        # Bullet / ordered item
        m = LIST_RE.match(line)
        if m:
            indent = m.group("indent")
            text = m.group("text").strip()
            # Compute bullet depth (2 spaces per level by heuristic)
            depth = max(0, len(indent) // 2)
            while len(bullets_stack) > depth:
                bullets_stack.pop()
            bullets_stack.append(text)
            path_parts = [*headings_stack, *bullets_stack]

            points.append(
                Point(id=next_id, text=text, path=path_parts.copy(), line_no=idx)
            )
            next_id += 1
            continue

    return points


# -----------------------------
# Archetype classifier (rules)
# -----------------------------


ARCHETYPES = [
    "algorithm_impl",
    "math_derivation",
    "concept_exposition",
    "api_quickstart",
    "procedure_checklist",
    "comparative_analysis",
    "case_study",
    "architecture_design",
    "troubleshooting",
]


def _re(kw: str) -> re.Pattern:
    return re.compile(kw, re.IGNORECASE)


KEYWORDS: Dict[str, List[re.Pattern]] = {
    # 算法实现 / Code Guide
    "algorithm_impl": [
        _re(r"\balgorithm\b|算法"),
        _re(r"实现|手写|from\s+scratch|implementation"),
        _re(r"复杂度|complexity|时间复杂度|空间复杂度"),
        _re(r"代码|code|示例|example|样例|demo"),
        _re(r"训练|预测|regression|classification|cluster|优化|optimi[sz]e"),
        _re(r"\bpython\b|\bjavascript\b|\btypescript\b|\bjava\b|\brust\b|\bgo\b|\bc\+\+\b"),
    ],
    # 数学推导 / Proof
    "math_derivation": [
        _re(r"证明|推导|proof|derive|derivation"),
        _re(r"定理|定律|theorem|lemma|corollary"),
        _re(r"公式|方程|equation|closed[- ]form|梯度|偏导|likelihood|收敛|convergence"),
    ],
    # 概念/框架阐释
    "concept_exposition": [
        _re(r"概念|原理|定义|definition|what\s+is|overview|语义|theory|背景|history|分类"),
        _re(r"基础|入门|basics|introduction|intro|fundamentals|术语|terminology"),
    ],
    # API/工具速用
    "api_quickstart": [
        _re(r"API|SDK|endpoint|接口|文档|reference"),
        _re(r"安装|install|pip|npm|yarn|import|依赖|dependency|package|模块"),
        _re(r"使用|用法|usage|示例|example|quickstart|getting\s+started"),
        _re(r"CLI|命令行|command|flag|参数|option"),
    ],
    # 流程/操作/Checklist
    "procedure_checklist": [
        _re(r"流程|步骤|过程|SOP|checklist|指南|guide|how\s+to|操作|部署|配置|setup"),
        _re(r"持续集成|CI|CD|release|发布|上线|rollback|回滚|验收"),
    ],
    # 比较与选型
    "comparative_analysis": [
        _re(r"对比|比较|vs\.?|versus|差异|优缺点|trade[- ]?off|选型|选择|benchmark"),
    ],
    # 案例/应用
    "case_study": [
        _re(r"案例|case\s+study|实战|实践|应用|use\s+case|经验|复盘|落地|project"),
    ],
    # 设计/架构
    "architecture_design": [
        _re(r"架构|architecture|设计|design|组件|component|模块|module|接口|接口设计|UML|微服务|DDD|拓扑|时序|data\s+flow"),
        _re(r"模式|pattern|SOLID|依赖倒置|layered|hexagonal|clean\s+architecture"),
    ],
    # 诊断/排错
    "troubleshooting": [
        _re(r"错误|error|异常|exception|排错|调试|debug|故障|diagnos(e|is)|复现|repro|not\s+found|undefined|TypeError|Crash"),
        _re(r"日志|log|stack\s*trace|堆栈|issue|bug|修复|fix"),
    ],
}


# Default switch templates per archetype
DEFAULT_SWITCHES: Dict[str, Dict[str, object]] = {
    "algorithm_impl": {
        "include_code": True,
        "code_lang": None,  # inferred if possible
        "include_eval_metrics": False,
        "include_math": False,
        "audience_level": None,
        "tone_style": "code-guide",
    },
    "math_derivation": {
        "include_math": True,
        "math_depth": "deep",
        "include_code": False,
        "audience_level": None,
        "tone_style": "proof",
    },
    "concept_exposition": {
        "include_code": False,
        "include_case_snippets": False,
        "audience_level": None,
        "tone_style": "expository",
    },
    "api_quickstart": {
        "include_code": True,
        "code_lang": None,
        "include_references": True,
        "audience_level": None,
        "tone_style": "quickstart",
    },
    "procedure_checklist": {
        "include_steps_checklist": True,
        "include_code": False,
        "audience_level": None,
        "tone_style": "tutorial",
    },
    "comparative_analysis": {
        "include_comparison_table": True,
        "include_code": False,
        "audience_level": None,
        "tone_style": "analysis",
    },
    "case_study": {
        "include_case_snippets": True,
        "include_code": False,
        "audience_level": None,
        "tone_style": "narrative",
    },
    "architecture_design": {
        "include_code": False,
        "audience_level": None,
        "tone_style": "design",
    },
    "troubleshooting": {
        "include_code": False,
        "include_steps_checklist": True,
        "audience_level": None,
        "tone_style": "diagnostic",
    },
}


LANG_HINTS = {
    "python": _re(r"\bpython\b|\.py\b|pandas|numpy|scikit|pytorch|tensorflow"),
    "javascript": _re(r"\bjavascript\b|\bjs\b|\.js\b|node\.?js|browser|web"),
    "typescript": _re(r"\btypescript\b|\bts\b|\.ts\b"),
    "java": _re(r"\bjava\b|JVM|spring"),
    "cpp": _re(r"c\+\+|\.cpp\b|\.cc\b|STL"),
    "go": _re(r"\bgo(lang)?\b|\.go\b"),
    "rust": _re(r"\brust\b|\.rs\b|cargo"),
}


AUDIENCE_HINTS = {
    "beginner": _re(r"入门|基础|beginner|basics|introduction|fundamental|新手"),
    "intermediate": _re(r"进阶|intermediate|实践|实战|advanced\s+guide|pro\s+tips"),
    "expert": _re(r"专家|expert|in\s+depth|深入|高级|theory|proof"),
}


def score_text(text: str, context: str) -> Tuple[str, Dict[str, float], Dict[str, List[str]]]:
    """Score a knowledge point against all archetypes.

    Returns:
      (best_archetype, scores, rationale_matches)
    """
    # Normalize
    t = text.strip()
    c = context.strip()
    blob = f"{t} | {c}"

    scores: Dict[str, float] = {k: 0.0 for k in ARCHETYPES}
    rationale: Dict[str, List[str]] = {k: [] for k in ARCHETYPES}

    # Keyword scoring
    for arch, patterns in KEYWORDS.items():
        for p in patterns:
            if p.search(blob):
                scores[arch] += 1.0
                rationale[arch].append(p.pattern)

    # Context nudges (headings influence)
    # Common outline hints
    heading_nudges = [
        ("concept_exposition", _re(r"overview|intro|basics|基础|概述|概念|introduction"), 0.6),
        ("api_quickstart", _re(r"api|reference|文档|安装|setup|quickstart"), 0.6),
        ("procedure_checklist", _re(r"step|步骤|流程|guide|操作|教程|deployment|部署"), 0.6),
        ("comparative_analysis", _re(r"vs\.?|对比|比较|选型|优缺点"), 0.7),
        ("troubleshooting", _re(r"error|错误|调试|排错|debug|issue|常见问题|FAQ"), 0.7),
        ("architecture_design", _re(r"架构|architecture|设计|patterns?"), 0.5),
    ]
    for arch, rx, w in heading_nudges:
        if rx.search(c):
            scores[arch] += w
            rationale[arch].append(f"nudge:{rx.pattern}")

    # Tie-breaking / defaults
    # If nothing matched, prefer concept exposition as safe default.
    if all(v == 0 for v in scores.values()):
        scores["concept_exposition"] = 0.5
        rationale["concept_exposition"].append("default:empty")

    # If algorithm and api both score similarly, lean by presence of complexity/algorithm lexicon
    if abs(scores["algorithm_impl"] - scores["api_quickstart"]) <= 0.5:
        if _re(r"复杂度|complexity|算法|algorithm|手写|from\s+scratch").search(blob):
            scores["algorithm_impl"] += 0.3
            rationale["algorithm_impl"].append("tie-break:alg-lexicon")

    # Choose best
    best = max(scores.items(), key=lambda kv: kv[1])[0]
    return best, scores, rationale


def infer_switches(archetype: str, text: str, context: str) -> Dict[str, object]:
    switches = json.loads(json.dumps(DEFAULT_SWITCHES[archetype]))  # deep copy via JSON
    blob = f"{text} | {context}"

    # audience level
    for lvl, rx in AUDIENCE_HINTS.items():
        if rx.search(blob):
            switches["audience_level"] = lvl
            break

    # code language
    if switches.get("include_code"):
        for lang, rx in LANG_HINTS.items():
            if rx.search(blob):
                switches["code_lang"] = lang
                break

    # math depth
    if archetype == "algorithm_impl":
        # if math-y words present, enable include_math lightly
        if _re(r"公式|方程|gradient|梯度|偏导|likelihood|loss|损失").search(blob):
            switches["include_math"] = True
            switches["math_depth"] = switches.get("math_depth", "light")

    if archetype in ("algorithm_impl", "api_quickstart"):
        # eval metrics trigger
        if _re(r"评估|指标|metric|accuracy|f1|precision|recall|benchmark").search(blob):
            switches["include_eval_metrics"] = True

    if archetype == "comparative_analysis":
        if _re(r"表|table|对比表").search(blob):
            switches["include_comparison_table"] = True

    if archetype in ("procedure_checklist", "troubleshooting"):
        switches["include_steps_checklist"] = True

    if archetype == "case_study":
        switches["include_case_snippets"] = True

    return switches


def confidence_from_scores(best: str, scores: Dict[str, float]) -> float:
    best_score = scores[best]
    total = sum(scores.values()) + 1e-9
    # ratio of best vs total (bounded)
    conf = min(0.99, max(0.3, best_score / total))
    return round(conf, 2)


# -----------------------------
# Optional: LLM refinement hook
# -----------------------------


def llm_refine(
    text: str,
    context: str,
    current: str,
    switches: Dict[str, object],
    provider: Optional[str] = None,
) -> Tuple[str, Dict[str, object], Optional[str]]:
    """Optional refinement via LLM.

    This is a no-op placeholder by default to keep the script offline.
    To enable, set --use-llm and PROVIDER env, then implement your call here.

    Returns: (archetype, switches, provider_used)
    """
    # Intentionally not importing any SDK to keep this file dependency-free.
    # Suggested integration points (choose one, then add minimal code):
    # - OpenAI:   set env OPENAI_API_KEY and provider="openai"
    # - AzureAI:  set env AZURE_OPENAI_API_KEY and provider="azure"
    # - Ollama:   local model via HTTP, provider="ollama"
    # - vLLM/self-hosted: provider="http"
    _ = (text, context, switches)
    if provider:
        # You can implement a small client here if needed.
        # For now we just return the current result unchanged and annotate provider.
        return current, switches, provider
    return current, switches, None


# -----------------------------
# CLI / main
# -----------------------------


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Classify knowledge points in a Markdown outline into archetypes + switches"
    )
    parser.add_argument("input", help="Path to Markdown outline, e.g., web-learner/public/javascript-learning-path.md")
    parser.add_argument("--output", "-o", help="Output JSONL file (default: stdout)")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print a compact table to stderr")
    parser.add_argument("--use-llm", action="store_true", help="Enable optional LLM refinement (no network calls by default)")
    parser.add_argument("--provider", choices=["openai", "azure", "ollama", "http"], help="LLM provider key (only if --use-llm)")

    args = parser.parse_args(argv)

    points = parse_markdown_outline(args.input)
    if not points:
        print("[WARN] No points parsed or file missing.", file=sys.stderr)
        return 1

    # Prepare output stream
    out_fh = open(args.output, "w", encoding="utf-8") if args.output else sys.stdout

    rows_for_pretty: List[Tuple[int, str, str, float]] = []

    for p in points:
        context = " / ".join(p.path[:-1])  # parent path as context
        best, scores, rationale = score_text(p.text, context)
        switches = infer_switches(best, p.text, context)
        conf = confidence_from_scores(best, scores)

        # Optional LLM refinement (no-op unless provider is implemented)
        provider_used = None
        if args.use_llm:
            best, switches, provider_used = llm_refine(p.text, context, best, switches, args.provider)

        record = {
            "id": p.id,
            "text": p.text,
            "path": p.path,
            "archetype": best,
            "switches": switches,
            "confidence": conf,
            "rationale": {k: v for k, v in rationale.items() if v},
        }
        if provider_used:
            record["refined_by"] = provider_used

        out_fh.write(json.dumps(record, ensure_ascii=False) + "\n")

        if args.pretty:
            rows_for_pretty.append((p.id, p.text, best, conf))

    if out_fh is not sys.stdout:
        out_fh.close()

    if args.pretty:
        # Print a compact view to stderr (ID, text, archetype, confidence)
        print("\nPreview (id | archetype | conf | text):", file=sys.stderr)
        for rid, text, arch, conf in rows_for_pretty[:50]:
            print(f"{rid:>4} | {arch:<20} | {conf:>4} | {text}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
