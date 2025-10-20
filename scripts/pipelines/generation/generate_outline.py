#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基于“主题 + 深度”的简化大纲生成器（Markdown + JSON）。

目标：
- 输入极简：topic（主题） + depth（学习深度，默认“核心掌握”）。
- 输出可直接用于后续内容生成的大纲：
  - Markdown（人类可读，遵循章/节/知识点的层级与 id 规则）
  - JSON（结构化数据，包含每个知识点的 archetype + switches 等元数据）

特点：
- 仅一次或少量 LLM 调用（按 config.json 选择 DeepSeek/Gemini 等）。
- 强约束 JSON Schema，若模型输出非 JSON，尽力提取；缺项则按默认映射补齐。
- 简化“collect goals”：仅用 depth → 映射成易懂的学习目标与形态配比。

使用示例：
  python scripts/generate_outline.py --topic "JavaScript 核心基础" --depth core --pretty
  python scripts/generate_outline.py --topic "LangGraph 入门" --depth overview --llm deepseek-chat \
    --config config.json --out-dir output --pretty

依赖：
- openai（DeepSeek/OpenAI 兼容）或 google-generativeai（Gemini）
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# -----------------------------
# 配置与模型选择
# -----------------------------


def load_config(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"未找到配置文件: {path}")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        raise RuntimeError(f"配置文件解析失败: {e}")


@dataclass
class LLMConfig:
    key: str
    provider: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: Optional[float] = 0.4


def choose_llm(cfg: Dict[str, Any], llm_key: Optional[str]) -> LLMConfig:
    llms = cfg.get("llms") or {}
    if not llms:
        raise RuntimeError("配置中缺少 'llms'。")

    if not llm_key:
        node_llm = cfg.get("node_llm") or {}
        llm_key = node_llm.get("generate_outline") or node_llm.get("default")
    if not llm_key:
        llm_key = next(iter(llms.keys()))

    entry = llms.get(llm_key)
    if not entry:
        raise RuntimeError(f"在 config.json 中找不到 llm: {llm_key}")

    provider = entry.get("provider") or "openai"
    model = entry.get("model") or llm_key
    api_key = entry.get("api_key") or os.environ.get("OPENAI_API_KEY")
    base_url = entry.get("base_url")
    temperature = entry.get("temperature", 0.4)
    return LLMConfig(key=llm_key, provider=provider, model=model, api_key=api_key, base_url=base_url, temperature=temperature)


class LLMCaller:
    """兼容 DeepSeek/OpenAI 与 Gemini 的最小调用包装。"""

    def __init__(self, conf: LLMConfig):
        self.conf = conf
        self._client = None
        self._init()

    def _init(self) -> None:
        if self.conf.provider in ("deepseek", "openai"):
            try:
                from openai import OpenAI
            except Exception:
                raise SystemExit("缺少 openai 库，请先安装：pip install openai")
            if not self.conf.api_key:
                raise SystemExit("未配置 API Key。请在 config.json 或环境变量中提供。")
            self._client = OpenAI(api_key=self.conf.api_key, base_url=self.conf.base_url)
        elif self.conf.provider == "gemini":
            try:
                import google.generativeai as genai
            except Exception:
                raise SystemExit("缺少 google-generativeai 库，请先安装：pip install google-generativeai")
            if not self.conf.api_key:
                raise SystemExit("未配置 Gemini API Key。")
            genai.configure(api_key=self.conf.api_key)
            self._client = genai
        else:
            raise SystemExit(f"暂不支持的 provider: {self.conf.provider}")

    def complete_json(self, prompt: str, max_tokens: int = 4096) -> str:
        if self.conf.provider in ("deepseek", "openai"):
            resp = self._client.chat.completions.create(
                model=self.conf.model,
                messages=[
                    {"role": "system", "content": "你是一个只输出 JSON 的大纲助手。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.conf.temperature or 0.4,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content or ""
        elif self.conf.provider == "gemini":
            model = self._client.GenerativeModel(self.conf.model)
            resp = model.generate_content(prompt)
            return getattr(resp, "text", "") or ""
        else:
            raise RuntimeError("未知 provider")


# -----------------------------
# 工具与默认映射
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

DEFAULT_SWITCHES: Dict[str, Dict[str, Any]] = {
    "algorithm_impl": {"include_code": True, "code_lang": None, "include_math": False, "include_eval_metrics": False, "tone_style": "code-guide"},
    "math_derivation": {"include_math": True, "math_depth": "light", "include_code": False, "tone_style": "proof"},
    "concept_exposition": {"include_code": False, "include_case_snippets": False, "tone_style": "expository"},
    "api_quickstart": {"include_code": True, "code_lang": None, "include_references": True, "tone_style": "quickstart"},
    "procedure_checklist": {"include_steps_checklist": True, "include_code": False, "tone_style": "tutorial"},
    "comparative_analysis": {"include_comparison_table": True, "include_code": False, "tone_style": "analysis"},
    "case_study": {"include_case_snippets": True, "include_code": False, "tone_style": "narrative"},
    "architecture_design": {"include_code": False, "tone_style": "design"},
    "troubleshooting": {"include_steps_checklist": True, "include_code": False, "tone_style": "diagnostic"},
}

# 视觉化相关开关（可按需默认开启）
VISUAL_DEFAULTS = {
    "algorithm_impl": {"include_mermaid": True, "diagram_types": ["flowchart"], "diagram_depth": "light"},
    "procedure_checklist": {"include_mermaid": True, "diagram_types": ["flowchart"], "diagram_depth": "light"},
    "architecture_design": {"include_mermaid": True, "diagram_types": ["flowchart", "sequence"], "diagram_depth": "deep"},
    "api_quickstart": {"include_mermaid": False, "diagram_types": ["sequence"], "diagram_depth": "light"},
    "comparative_analysis": {"include_mermaid": False},
    "concept_exposition": {"include_mermaid": False},
    "case_study": {"include_mermaid": True, "diagram_types": ["gantt"], "diagram_depth": "light"},
    "math_derivation": {"include_mermaid": False},
    "troubleshooting": {"include_mermaid": True, "diagram_types": ["flowchart"], "diagram_depth": "light"},
}


def slugify(text: str, fallback: str = "outline") -> str:
    """尽量生成 ASCII slug；若失败用 fallback。"""
    # 替换中文括号为英文，去掉特殊符号
    t = (
        text.replace("（", "(").replace("）", ")")
        .replace("—", "-")
        .replace("—", "-")
        .strip()
    )
    # 移除非字母数字和空格
    t = re.sub(r"[^0-9A-Za-z\-_.\s]", "", t)
    t = re.sub(r"\s+", "-", t)
    t = t.strip("-_.").lower()
    return t or fallback


def extract_json(s: str) -> Optional[Dict[str, Any]]:
    s = (s or "").strip()
    if not s:
        return None
    # 1) 直接解析
    try:
        return json.loads(s)
    except Exception:
        pass
    # 2) ```json 包裹
    m = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", s, re.IGNORECASE)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    # 3) 截取 { ... }
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        frag = s[start : end + 1]
        try:
            return json.loads(frag)
        except Exception:
            return None
    return None


# -----------------------------
# Prompt 构造（简化 collect goals）
# -----------------------------


DEPTH_PRESETS = {
    "overview": {
        "human_goal": "了解关键概念与常用操作，能看懂、能用基础功能",
        "archetype_mix": {
            "concept_exposition": 0.5,
            "api_quickstart": 0.25,
            "procedure_checklist": 0.1,
            "comparative_analysis": 0.1,
            "case_study": 0.05,
        },
    },
    "core": {
        "human_goal": "掌握核心原理与使用方法，不做复杂推导，能独立完成常见任务",
        "archetype_mix": {
            "concept_exposition": 0.35,
            "api_quickstart": 0.2,
            "procedure_checklist": 0.15,
            "comparative_analysis": 0.1,
            "algorithm_impl": 0.1,
            "case_study": 0.1,
        },
    },
    "advanced": {
        "human_goal": "面向实战与优化，能做选型、权衡与排错，形成可演进方案",
        "archetype_mix": {
            "concept_exposition": 0.2,
            "api_quickstart": 0.15,
            "procedure_checklist": 0.2,
            "comparative_analysis": 0.15,
            "architecture_design": 0.15,
            "troubleshooting": 0.1,
            "case_study": 0.05,
        },
    },
}


OUTLINE_CONSTRAINTS = {
    "chapters": [4, 7],  # 章节数量范围
    "groups_per_chapter": [2, 4],  # 每章小节数量范围
    "sections_per_group": [4, 7],  # 每小节知识点数量范围
}


def build_outline_prompt(topic: str, depth: str, language: str = "zh") -> str:
    preset = DEPTH_PRESETS.get(depth, DEPTH_PRESETS["core"])
    human_goal = preset["human_goal"]
    mix = preset["archetype_mix"]
    mix_str = ", ".join(f"{k}:{v}" for k, v in mix.items())
    ar_list = ", ".join(ARCHETYPES)
    ch_min, ch_max = OUTLINE_CONSTRAINTS["chapters"]
    gr_min, gr_max = OUTLINE_CONSTRAINTS["groups_per_chapter"]
    se_min, se_max = OUTLINE_CONSTRAINTS["sections_per_group"]

    return f"""
你是一名课程与知识结构设计专家。请基于以下目标，产出结构化学习大纲（只输出 JSON，符合给定 Schema）。

【主题】{topic}
【学习深度】{depth}（{human_goal}）
【结构约束】章节 {ch_min}-{ch_max} 个；每章小节 {gr_min}-{gr_max} 个；每小节知识点 {se_min}-{se_max} 个；
【难度梯度】每个小节内部从 beginner → intermediate → expert 递进；
【原型分布先验】{mix_str}（可微调，但需解释理由）
【可选原型】{ar_list}
【开关键集合】include_code, code_lang, include_math, math_depth, include_comparison_table, include_steps_checklist, include_case_snippets, include_eval_metrics, include_references, include_mermaid, include_ascii_diagram, diagram_types, diagram_depth, audience_level, tone_style

【输出 JSON Schema】严格输出一个对象：
{{
  "meta": {{
    "topic": "{topic}",
    "depth": "{depth}",
    "goal": "{human_goal}",
    "language": "{language}",
    "schema_version": "outline.v1"
  }},
  "chapters": [
    {{
      "title": "<章标题>",
      "groups": [
        {{
          "title": "<小节标题>",
          "sections": [
            {{
              "title": "<知识点标题>",
              "goal": "<一句话学习目标>",
              "difficulty": "beginner|intermediate|expert",
              "archetype": "<从 9 个原型中二选一>",
              "switches": {{
                "include_code": <true|false 可省略>,
                "code_lang": "<可省略>",
                "include_math": <true|false 可省略>,
                "math_depth": "<light|deep 可省略>",
                "include_comparison_table": <true|false 可省略>,
                "include_steps_checklist": <true|false 可省略>,
                "include_case_snippets": <true|false 可省略>,
                "include_eval_metrics": <true|false 可省略>,
                "include_references": <true|false 可省略>,
                "include_mermaid": <true|false 可省略>,
                "include_ascii_diagram": <true|false 可省略>,
                "diagram_types": ["<flowchart|sequence|class|state|er|gantt 可省略>"],
                "diagram_depth": "<light|deep 可省略>",
                "audience_level": "<beginner|intermediate|expert 可省略>",
                "tone_style": "<可省略>"
              }}
            }}
          ]
        }}
      ]
    }}
  ],
  "rationale": "<关于原型分布与结构安排的简短理由>"
}}

【重要】只输出 JSON，不要解释、不要 Markdown。
"""


# -----------------------------
# 后处理：补全默认、生成 ID、渲染 Markdown
# -----------------------------


def deep_get(d: Dict[str, Any], *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def apply_defaults_and_ids(topic: str, data: Dict[str, Any]) -> Dict[str, Any]:
    topic_slug = slugify(topic)
    data.setdefault("meta", {})
    data["meta"].setdefault("topic_slug", topic_slug)

    chapters = data.get("chapters") or []
    for ci, ch in enumerate(chapters, start=1):
        ch_id = f"{topic_slug}-ch-{ci}"
        ch["id"] = ch_id
        groups = ch.get("groups") or []
        for gi, gr in enumerate(groups, start=1):
            gr_id = f"{topic_slug}-gr-{ci}-{gi}"
            gr["id"] = gr_id
            sections = gr.get("sections") or []
            # 规范小节内部难度顺序（B→I→E）
            diff_order = {"beginner": 0, "intermediate": 1, "expert": 2}
            try:
                sections.sort(key=lambda s: diff_order.get((s.get("difficulty") or "intermediate"), 1))
            except Exception:
                pass
            for si, sec in enumerate(sections, start=1):
                title = sec.get("title") or f"Section {ci}.{gi}.{si}"
                sec_slug = slugify(title, fallback=f"sec-{ci}-{gi}-{si}")
                sec_id = f"{topic_slug}-sec-{ci}-{gi}-{si}-{sec_slug}"
                sec["id"] = sec_id

                # archetype 与 switches 补默认
                arch = sec.get("archetype") or "concept_exposition"
                if arch not in ARCHETYPES:
                    arch = "concept_exposition"
                switches = sec.get("switches") or {}
                # 合并默认 + 视觉默认
                merged = {}
                merged.update(DEFAULT_SWITCHES.get(arch, {}))
                merged.update(VISUAL_DEFAULTS.get(arch, {}))
                merged.update(switches)
                sec["archetype"] = arch
                sec["switches"] = merged

    return data


def render_markdown(data: Dict[str, Any]) -> str:
    topic = deep_get(data, "meta", "topic", default="主题")
    topic_slug = deep_get(data, "meta", "topic_slug", default=slugify(topic))
    lines: List[str] = []
    lines.append(f"# {topic} (id: {topic_slug})")
    chapters = data.get("chapters") or []
    for ci, ch in enumerate(chapters, start=1):
        ch_title = ch.get("title") or f"第{ci}章"
        lines.append("")
        lines.append(f"## 第{ci}章：{ch_title} (id: {ch.get('id')})")
        groups = ch.get("groups") or []
        for gi, gr in enumerate(groups, start=1):
            gr_title = gr.get("title") or f"{ci}.{gi} 小节"
            lines.append(f"### {ci}.{gi} {gr_title} (id: {gr.get('id')})")
            sections = gr.get("sections") or []
            for si, sec in enumerate(sections, start=1):
                s_title = sec.get("title") or f"{ci}.{gi}.{si} 知识点"
                lines.append(
                    f"#### {ci}.{gi}.{si} {s_title} (id: {sec.get('id')})"
                )
    return "\n".join(lines) + "\n"


# -----------------------------
# CLI / main
# -----------------------------


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="基于主题+深度的简化大纲生成（Markdown+JSON）")
    parser.add_argument("--topic", required=True, help="主题（如：JavaScript 核心基础 / LangGraph 入门）")
    parser.add_argument("--depth", choices=["overview", "core", "advanced"], default="core", help="学习深度，默认 core（核心掌握）")
    parser.add_argument("--language", default="zh", help="输出语言（默认 zh）")
    parser.add_argument("--config", default="config.json", help="配置文件路径（默认 config.json）")
    parser.add_argument("--llm", help="使用的 llm key（覆盖 config.json 中 node_llm.generate_outline）")
    parser.add_argument("--out-dir", default="output", help="输出目录（默认 output）")
    parser.add_argument("--basename", help="输出文件基名（默认由 topic 派生）")
    parser.add_argument("--max-tokens", type=int, default=4096, help="最大 tokens（默认 4096）")
    parser.add_argument("--pretty", action="store_true", help="在 stderr 打印简要预览")

    args = parser.parse_args(argv)

    try:
        cfg = load_config(args.config)
        llm_cfg = choose_llm(cfg, args.llm)
    except Exception as e:
        print(f"[错误] 读取/选择大模型失败：{e}", file=sys.stderr)
        return 2

    try:
        caller = LLMCaller(llm_cfg)
    except SystemExit as e:
        print(str(e), file=sys.stderr)
        return 2
    except Exception as e:
        print(f"[错误] 初始化 LLM 客户端失败：{e}", file=sys.stderr)
        return 2

    prompt = build_outline_prompt(args.topic, args.depth, args.language)
    raw = caller.complete_json(prompt, max_tokens=args.max_tokens)
    data = extract_json(raw)
    if not data:
        print("[错误] LLM 未返回合法 JSON。", file=sys.stderr)
        return 1

    data = apply_defaults_and_ids(args.topic, data)

    # 渲染 Markdown
    md_text = render_markdown(data)

    # 输出路径
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    base = args.basename or slugify(args.topic)
    md_path = out_dir / f"{base}.learning-path.md"
    json_path = out_dir / f"{base}.outline.json"

    md_path.write_text(md_text, encoding="utf-8")
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.pretty:
        ch_count = len(data.get("chapters") or [])
        sec_count = sum(len(gr.get("sections") or []) for ch in data.get("chapters") or [] for gr in ch.get("groups") or [])
        print(f"已生成：{md_path}", file=sys.stderr)
        print(f"已生成：{json_path}", file=sys.stderr)
        print(f"章节数：{ch_count}，知识点数：{sec_count}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
