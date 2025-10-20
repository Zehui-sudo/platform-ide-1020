#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
四阶段学习大纲生成器（Brainstorm → Structure → Detail → Review）。

输入：
- 主题（--topic）
- 深度（--depth，控制粒度与规模）

输出：
- seeds.json（阶段1：发散脑暴产物）
- skeleton.json（阶段2：章节骨架）
- outline.json（阶段3：完整章/节/点 + primary_goal + suggested_modules + 稳定ID）
- learning-path.md（与现有风格一致的 Markdown 大纲）
- review.json（阶段4：评分与建议，含轻量修复后的记录）

说明：
- 本脚本不再依赖 archetype + switches。改为以 primary_goal（主要教学目标）与 suggested_modules（建议内容模块）软约束驱动后续内容生成。
- 依赖 config.json 选择大模型，支持 DeepSeek（OpenAI 兼容）与 Gemini。
- 并发受 config.json 的 max_parallel_requests 控制，可用 --max-parallel 覆盖。
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import math
import os
import re
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


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


def choose_llm(cfg: Dict[str, Any], llm_key: Optional[str], node_key_fallback: str) -> LLMConfig:
    llms = cfg.get("llms") or {}
    if not llms:
        raise RuntimeError("配置中缺少 'llms'。")
    if not llm_key:
        node_llm = cfg.get("node_llm") or {}
        llm_key = node_llm.get(node_key_fallback) or node_llm.get("default")
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

    def chat_json(self, prompt: str, max_tokens: int = 2048) -> str:
        if self.conf.provider in ("deepseek", "openai"):
            resp = self._client.chat.completions.create(
                model=self.conf.model,
                messages=[
                    {"role": "system", "content": "你是一个只输出 JSON 的助手。"},
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
# 共用工具
# -----------------------------


# archetype/switches 已废弃：改由 primary_goal + suggested_modules 软建议驱动


def _iter_balanced_fragments(s: str, open_char: str, close_char: str):
    """Yield top-level balanced JSON fragments delimited by open_char/close_char.

    Handles quotes and escapes so brackets/braces inside strings do not affect
    balance. Returns raw substrings (not parsed).
    """
    in_string = False
    string_char = ""
    escape = False
    depth = 0
    start = -1
    for i, c in enumerate(s):
        if in_string:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == string_char:
                in_string = False
            continue
        else:
            if c in ("'", '"'):
                in_string = True
                string_char = c
                continue
            if c == open_char:
                if depth == 0:
                    start = i
                depth += 1
                continue
            if c == close_char and depth > 0:
                depth -= 1
                if depth == 0 and start != -1:
                    yield s[start : i + 1]
                    start = -1


def extract_json(s: str) -> Optional[Union[Dict[str, Any], List[Any]]]:
    """Best-effort JSON extraction.

    Supports:
    - Pure JSON (object or array)
    - JSON inside fenced code blocks (```json ... ``` or ~~~json ... ~~~)
    - JSON arrays/objects embedded in surrounding text via balanced scanning
    Returns a parsed object (dict or list) or None.
    """
    s = (s or "").strip()
    if not s:
        return None

    # 1) Direct parse attempt
    try:
        return json.loads(s)
    except Exception:
        pass

    # 2) Try fenced code blocks (both ``` and ~~~)
    fence_patterns = [
        r"```(?:json|JSON)?\s*([\s\S]*?)\s*```",
        r"~~~(?:json|JSON)?\s*([\s\S]*?)\s*~~~",
    ]
    for pat in fence_patterns:
        for m in re.finditer(pat, s, flags=re.IGNORECASE):
            block = (m.group(1) or "").strip()
            if not block:
                continue
            # 2.1 Parse block as a whole
            try:
                return json.loads(block)
            except Exception:
                pass
            # 2.2 Try arrays first, then objects inside the block
            for frag in _iter_balanced_fragments(block, "[", "]"):
                try:
                    return json.loads(frag)
                except Exception:
                    continue
            for frag in _iter_balanced_fragments(block, "{", "}"):
                try:
                    return json.loads(frag)
                except Exception:
                    continue

    # 3) No code blocks: balanced scan on the whole string
    for frag in _iter_balanced_fragments(s, "[", "]"):
        try:
            return json.loads(frag)
        except Exception:
            continue
    for frag in _iter_balanced_fragments(s, "{", "}"):
        try:
            return json.loads(frag)
        except Exception:
            continue

    return None


def slugify(text: str, fallback: str = "outline") -> str:
    t = (
        text.replace("（", "(").replace("）", ")")
        .replace("—", "-")
        .strip()
    )
    t = re.sub(r"[^0-9A-Za-z\-_.\s]", "", t)
    t = re.sub(r"\s+", "-", t)
    t = t.strip("-_.").lower()
    return t or fallback


# -----------------------------
# 阶段 1：发散脑暴
# -----------------------------


PERSPECTIVES = {
    "professor": {
        "name": "资深大学教授 (Senior University Professor)",
        "focus": "负责构建坚实的理论基础和知识体系。重点在于核心概念的定义、理论的推演、知识的脉络、历史演进以及目前最新的技术方向。确保学习路径的学术严谨性和体系完整性。",
        "tags": ["core_concept", "theory", "principle", "history", "definition","trend"],
        "count": 60,
    },
    "engineer": {
        "name": "资深行业工程师 (Senior Industry Engineer)",
        "focus": "负责提供来自一线的实践经验和技能。重点在于实用工具、技术栈、工作流程、最佳实践、真实案例、以及目前最新的技术方向。确保学习内容的实用性、可操作性和前瞻性。",
        "tags": ["skill", "tool", "workflow", "best_practice", "case_study", "pitfall", "trend"],
        "count": 60,
    },
}

def build_brainstorm_prompt_by_perspective(topic: str, language: str, perspective: Dict[str, Any]) -> str:
    return f"""
你是“{perspective['name']}”，一个专注于特定视角的领域专家。
你的任务是为主题“{topic}”的学习路线图，从你的专业视角出发，进行深入的头脑风暴。

**你的视角**: {perspective['focus']}

请为**初学者**设想，输出一份知识点清单，重点突出，覆盖全面。

**输出格式 (JSON)**:
{{
  "seeds": [
    {{"text": "<短语或知识点>", "tags": {json.dumps(perspective['tags'])}, "why": "<一句话理由>"}},
    ... 至少 {perspective['count']} 项 ...
  ]
}}

**关键要求**:
- **聚焦你的视角**: 所有知识点都应与你的专家身份和视角（{perspective['focus']}）高度相关。
- **对初学者友好**: 即使是高级主题，也要思考如何为新手引入。
- **严格JSON**: 只输出 JSON，禁止任何 Markdown 或解释性文字。

请开始你的头脑风暴。
"""

def stage1_brainstorm(
    caller: LLMCaller, 
    topic: str, 
    language: str, 
    out_dir: Path, 
    basename: str, 
    max_tokens: int,
    max_parallel: int
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Stage 1: Multi-perspective brainstorming.
    Returns a tuple of (professor_seeds, engineer_seeds).
    """
    print("  -> 采用多视角脑暴策略，并行生成知识点...")

    results: Dict[str, List[Dict[str, Any]]] = {}
    def run_perspective(p_key: str, p_data: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]]]:
        print(f"    -> 视角 '{p_data['name']}' 正在生成...")
        prompt = build_brainstorm_prompt_by_perspective(topic, language, p_data)
        raw = caller.chat_json(prompt, max_tokens=max_tokens)
        data = extract_json(raw)
        seeds = (data or {}).get("seeds", [])
        print(f"    <- 视角 '{p_data['name']}' 完成，产出 {len(seeds)} 个知识点。")
        for seed in seeds:
            if isinstance(seed, dict):
                seed['perspective'] = p_key
        return p_key, seeds

    with cf.ThreadPoolExecutor(max_workers=max_parallel) as executor:
        futures = {executor.submit(run_perspective, p_key, p_data): p_key for p_key, p_data in PERSPECTIVES.items()}
        for future in cf.as_completed(futures):
            try:
                p_key, seeds_from_perspective = future.result()
                results[p_key] = seeds_from_perspective
            except Exception as e:
                p_key_on_error = futures[future]
                print(f"    [错误] 视角 '{p_key_on_error}' 生成失败: {e}", file=sys.stderr)
                results[p_key_on_error] = []

    professor_seeds = results.get("professor", [])
    engineer_seeds = results.get("engineer", [])
    
    print(f"  -> 所有视角脑暴完成。教授: {len(professor_seeds)}，工程师: {len(engineer_seeds)}")
    
    # For logging and compatibility, save a combined, deduplicated file
    all_seeds_raw = professor_seeds + engineer_seeds
    final_seeds = []
    seen_texts = set()
    for seed in all_seeds_raw:
        if not isinstance(seed, dict): continue
        text = seed.get("text", "").strip()
        if not text: continue
        normalized_text = re.sub(r'\s+', ' ', text).lower()
        if normalized_text not in seen_texts:
            seen_texts.add(normalized_text)
            final_seeds.append(seed)

    print(f"  -> 知识种子去重后共 {len(final_seeds)} 个。")

    final_data = {"seeds": final_seeds, "notes": "Generated using multi-perspective brainstorming (Professor + Engineer)."}
    path = out_dir / f"{basename}.seeds.json"
    path.write_text(json.dumps(final_data, ensure_ascii=False, indent=2), encoding="utf-8")
    
    return professor_seeds, engineer_seeds


# -----------------------------
# 阶段 2：聚类与排序（章节骨架）
# -----------------------------


def build_macro_planner_prompt_from_perspectives(topic: str, professor_seeds: List[Dict], engineer_seeds: List[Dict], depth: str, language: str) -> str:
    target_chapters = {"overview": [4, 5], "core": [5, 7], "advanced": [6, 8]}[depth]
    
    return f"""
你是一位顶级的课程总设计师，擅长融合理论与实践，为**完全没有基础的初学者**设计完美的学习路径。

**当前任务**:
你收到了关于主题“**{topic}**”的两份来自不同专家的知识点列表：
1.  **大学教授的列表**: 侧重理论、概念和知识体系。
2.  **行业工程师的列表**: 侧重实践、工具和一线经验。

你的任务是**综合这两份列表**，设计一条从理论到实践、循序渐进的学习路径。你需要将所有知识点（理论+实践）聚类成 {target_chapters[0]} 到 {target_chapters[1]} 个逻辑上连贯的核心章节，并为每个章节撰写标题和学习目标。

**关键原则**:
- **融合理论与实践**: 设计的章节应该自然地将理论和实践结合起来，而不是将它们割裂。
- **符合学习认知规律**: 从为什么学、学什么、怎么学的角度出发，确保章节安排符合人类认知规律。
- **绝对的循序渐进**: 必须从最简单、最核心的概念讲起。这是最重要的原则。

**输出格式（必须严格遵守）**:
- 仅输出一个 JSON 数组，每个元素代表一个章节，包含 "title" 与 "objective" 两个字段。
- 禁止任何非 JSON 内容。

**输入列表**:

**1. 教授的知识点 (理论视角)**:
```json
{json.dumps(professor_seeds, ensure_ascii=False, indent=2)[:3000]}
```

**2. 工程师的知识点 (实践视角)**:
```json
{json.dumps(engineer_seeds, ensure_ascii=False, indent=2)[:3000]}
```

请根据以上要求，为当前主题“{topic}”设计章节规划，并最终只输出一个纯 JSON 数组。
"""

def stage2_structure(
    caller: LLMCaller, 
    topic: str, 
    professor_seeds: List[Dict[str, Any]],
    engineer_seeds: List[Dict[str, Any]],
    depth: str, 
    language: str, 
    out_dir: Path, 
    basename: str, 
    max_tokens: int
) -> Dict[str, Any]:
    """
    Stage 2: Synthesize perspectives and create macro-structure.
    """
    path = out_dir / f"{basename}.skeleton.json"
    prompt = build_macro_planner_prompt_from_perspectives(
        topic, professor_seeds, engineer_seeds, depth, language
    )
    raw = caller.chat_json(prompt, max_tokens=max_tokens)
    
    # Enhanced parsing logic
    chapters_data = []
    parsed = extract_json(raw)

    if isinstance(parsed, list):
        chapters_data = parsed
    elif isinstance(parsed, dict):
        for key in ["chapters", "outline", "plan", "structure"]:
            if isinstance(parsed.get(key), list):
                chapters_data = parsed[key]
                break
    
    if not chapters_data and isinstance(raw, str):
        print("[警告] Stage 2 返回格式非标准或解析失败，尝试在文本中搜索JSON数组...", file=sys.stderr)
        m = re.search(r"```(?:json|JSON)?\s*(\[[\s\S]*?\])\s*```", raw)
        if m:
            try:
                candidate = json.loads(m.group(1))
                if isinstance(candidate, list):
                    chapters_data = candidate
            except Exception: pass
        if not chapters_data:
            for frag in _iter_balanced_fragments(raw, "[", "]"):
                try:
                    candidate = json.loads(frag)
                    if isinstance(candidate, list):
                        chapters_data = candidate
                        break
                except Exception: continue
        if not chapters_data:
            chapters_data = []

    for i, ch in enumerate(chapters_data):
        if isinstance(ch, dict):
             ch['id'] = ch.get('id') or f"temp-ch-{i+1}"

    # 2.2 为每个章节选择相关 seeds
    def build_chapter_seed_selector_prompt(ch_title: str, ch_objective: str, seed_list: List[Dict[str, Any]]) -> str:
        listed = [{"id": i + 1, "text": (s.get("text") or "")} for i, s in enumerate(seed_list)]
        seeds_json = json.dumps(listed, ensure_ascii=False)
        return f"""
你是一个信息分类助手。下面给出一组“知识点”列表（seeds，已按 id 编号），以及某一章节的标题与学习目标。
任务：从列表中选出与该章节最相关的 15～20 个知识点。
要求：
- 只输出一个 JSON 数组，数组元素是被选中的 seed 的 id（整数）。
- 数量控制在 15～20 个之间，按相关性从高到低排序。
- 每个 id 只能出现一次，禁止重复。
- 不要输出任何解释性文字或 Markdown，只输出纯 JSON 数组。
【章节信息】
- 标题: {ch_title}
- 学习目标: {ch_objective}
【候选 Seeds（示例字段仅含 id 与 text）】
```json
{seeds_json}
```
请只输出最终的 id 数组，例如： [3, 8, 12, ...]
"""

    # Combine seeds for the selection step
    seed_list = professor_seeds + engineer_seeds
    if chapters_data and seed_list:
        print("[阶段 2/4] 2.2 正在为每个章节选择相关 seeds（并行）...")

        def select_for_chapter(idx: int, ch: Dict[str, Any]) -> Tuple[int, List[Dict[str, Any]]]:
            title = ch.get("title") or f"第{idx}章"
            obj = ch.get("objective") or ""
            sel_prompt = build_chapter_seed_selector_prompt(title, obj, seed_list)
            raw_sel = caller.chat_json(sel_prompt, max_tokens=min(max_tokens, 1024))
            selected_ids: List[int] = []
            parsed = extract_json(raw_sel)
            def sanitize_to_ids(p) -> List[int]:
                ids: List[int] = []
                if isinstance(p, list):
                    for item in p:
                        if isinstance(item, int): ids.append(item)
                        elif isinstance(item, dict):
                            v = item.get("id") or item.get("idx") or item.get("seed_id")
                            if isinstance(v, int): ids.append(v)
                elif isinstance(p, dict):
                    for k in ("ids", "indices", "selected", "seed_ids"):
                        v = p.get(k)
                        if isinstance(v, list): ids.extend([x for x in v if isinstance(x, int)])
                return ids
            selected_ids = sanitize_to_ids(parsed)

            if not selected_ids:
                key = (title or "") + " " + (obj or "")
                key = key.strip()
                ranked = []
                for i, s in enumerate(seed_list, start=1):
                    t = s.get("text") or ""
                    score = 0
                    for part in re.split(r"\s+", key):
                        if part and part in t: score += 1
                    ranked.append((score, i))
                ranked.sort(key=lambda x: (-x[0], x[1]))
                selected_ids = [i for (_, i) in ranked[:18]]

            seen = set()
            final_ids: List[int] = []
            for i in selected_ids:
                if isinstance(i, int) and 1 <= i <= len(seed_list) and i not in seen:
                    final_ids.append(i)
                    seen.add(i)
                if len(final_ids) >= 20: break
            if len(final_ids) < 15:
                for j in range(1, len(seed_list) + 1):
                    if j not in seen:
                        final_ids.append(j)
                        seen.add(j)
                    if len(final_ids) >= 15: break

            selected_seeds = [seed_list[i - 1] for i in final_ids]
            return idx, selected_seeds

        results_sel: Dict[int, List[Dict[str, Any]]] = {}
        max_workers = min(8, max(1, len(chapters_data)))
        with cf.ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = [ex.submit(select_for_chapter, i, ch) for i, ch in enumerate(chapters_data, start=1)]
            for fut in cf.as_completed(futures):
                idx, selected_seeds = fut.result()
                results_sel[idx] = selected_seeds
        for i, ch in enumerate(chapters_data, start=1):
            ch["selected_seeds"] = results_sel.get(i, [])

    data = {"chapters": chapters_data}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


# -----------------------------
# 阶段 3：递归深化（为每章生成小节与知识点）+ 原型判别
# -----------------------------


def build_chapter_architect_prompt(
    chapter_title: str,
    chapter_objective: str,
    full_skeleton: List[Dict[str, Any]],
    current_index: int,
) -> str:
    """构建章节架构师（Stage 3）的One-Shot Prompt。

    新增：提供完整章节骨架（Stage 2 输出）作为上文上下文，避免跨章重复，保持全局连贯。
    current_index 从 1 开始，对应当前章节在骨架中的位置。
    """
    
    # The full one-shot prompt as a multi-line f-string
    return f"""### 1. 角色与目标 (Role and Goal)

**角色:** 你是一位世界顶级的课程设计师和教学架构师。你的专长是将任何领域内一组零散的知识点，重构成一个符合人类认知规律、叙事流畅、结构清晰的“最佳学习路径”。


**核心目标:** 将用户提供的章节标题、目标和相关知识点列表，转化为一个带有丰富语义元数据 (`structure_type`, `relation_to_previous`, `primary_goal`, `suggested_modules`) 的、结构化的单章节详细JSON大纲。

### 2. 核心概念定义 (Core Concepts Definition)

在你的设计中，必须严格遵循以下两种原子结构模型：

*   **流水线 (Pipeline):**
    *   **定义:** 一系列具有**强时序性或强依赖性**的知识点。它们通常描述一个连续的过程、工作流或逻辑推演。
    *   **关键特征:** 前一个知识点的**输出**是后一个知识点的**输入**。学习顺序**几乎不可更改**。
    *   **例子:** 文本预处理流程、数学定理的证明步骤、一个算法的执行过程。

*   **工具箱 (Toolbox):**
    *   **定义:** 一组围绕**共同主题或目标**，但彼此**相对独立**的知识点。
    *   **关键特征:** 知识点之间没有严格的顺序依赖，可以并行学习或按任意顺序学习。它们是解决相关问题的不同方法、工具或概念。
    *   **例子:** Python的各种数据结构、机器学习的各种分类算法、CSS的各种选择器。

### 3. 执行步骤 (Execution Steps)

1.  **分析与分组:** 仔细阅读输入的知识点列表。识别出哪些知识点可以串联成“流水线”，哪些可以归类到不同的“工具箱”中，形成小节(Group)。
2.  **设计微观结构:** 在每个小节内部，排列知识点（Section）的顺序，确保逻辑通顺。
3.  **精炼标题:** 为每个小节和知识点撰写清晰、简洁且具有引导性的标题。
4.  **注入元数据 (关键):** 在最终的JSON结构中，必须为每个小节（Group）和知识点（Section）添加以下元数据：
    *   为每个**小节 (Group)** 添加 `structure_type: "pipeline" | "toolbox"` 字段。
    *   为每个**知识点 (Section)** 添加：
        - `relation_to_previous`: `builds_on | tool_in_toolbox | alternative_to | deep_dive_into | first_in_sequence`
        - `primary_goal`: 用一句话清晰地定义该知识点的**核心内容目标**。它应精准描述“这节内容需要讲清楚什么核心问题”或“它要从什么角度去写”，而不是定义学习者的能力目标。
            - **反例 (Bad)**: "学习数据清洗" (过于宽泛，是学习目标)
            - **正例 (Good)**: "介绍数据清洗作为预处理流程第一步的核心任务，并展示常见的清洗技术。" (明确了内容范围和任务，是内容目标)
        - `suggested_modules`: 在正常的文字阐述之外，可以额外使用的**增强表达形式**清单（数组，允许从以下枚举中挑选）：
            `["code_example", "common_mistake_warning", "mermaid diagram", "checklist", "comparison", "case_study"]`
5.  **格式化输出:** 确保最终输出是一个结构严谨、格式正确的单一JSON对象，代表这一个章节的完整结构。
                        
### 4. 高质量范例 (One-Shot Example)

**输入范例:**
*   **章节标题:** "第一章：基础篇 · 让机器读懂语言"
*   **章节学习目标:** "学习如何将原始文本转化为机器可以处理的结构化数据，并了解不同的文本表示方法。"
*   **相关知识点Seeds:** `["文本清洗", "分词", "停用词移除", "词形归一化", "词袋模型", "TF-IDF", "Word2Vec"]`

**输出范例 (JSON):**
```json
{{
    "title": "第一章：基础篇 · 让机器读懂语言",
    "id": "nlp-ch-1",
    "groups": [
    {{
        "title": "1.1 文本预处理：从原始语料到结构化数据",
        "id": "nlp-gr-1-1",
        "structure_type": "pipeline",
        "sections": [
        {{
            "title": "1.1.1 起始点：预处理的重要性",
            "id": "nlp-sec-1-1-1",
            "relation_to_previous": "first_in_sequence",
            "primary_goal": "解释原始文本中存在的歧义性、非结构化等问题，阐明机器进行自然语言理解前必须进行预处理的原因。",
            "suggested_modules": ["diagram", "case_study"]
        }},
        {{
            "title": "1.1.2 第一步：基础清洗",
            "id": "nlp-sec-1-1-2",
            "relation_to_previous": "builds_on",
            "primary_goal": "介绍文本预处理流程中的第一个具体步骤——数据清洗，并列举常见的清洗目标（如移除HTML标签、特殊字符等）。",
            "suggested_modules": ["checklist", "code_example", "common_mistake_warning"]
        }},
        {{
            "title": "1.1.3 第二步：文本切分 (Tokenization)",
            "id": "nlp-sec-1-1-3",
            "relation_to_previous": "builds_on",
            "primary_goal": "讲解“分词”的核心概念，并对比不同分词粒度（如按词、按子词）的适用场景。",
            "suggested_modules": ["code_example", "comparison"]
        }},
        {{
            "title": "1.1.4 第三步：精炼词元 (停用词移除与词形归一化)",
            "id": "nlp-sec-1-1-4",
            "relation_to_previous": "builds_on",
            "primary_goal": "阐述停用词移除和词形归一化（词干提取/词形还原）的策略及其对后续任务的影响。",
            "suggested_modules": ["code_example", "common_mistake_warning"]
        }}
        ]
    }},
    {{
        "title": "1.2 文本表示方法：将词语变为向量",
        "id": "nlp-gr-1-2",
        "structure_type": "toolbox",
        "sections": [
        {{
            "title": "1.2.1 核心思想：为何需要文本表示",
            "id": "nlp-sec-1-2-1",
            "relation_to_previous": "first_in_sequence",
            "primary_goal": "阐述计算机无法直接处理文本，必须将其数值化（向量化）的核心原因。",
            "suggested_modules": ["diagram"]
        }},
        {{
            "title": "1.2.2 工具一 (离散表示)：词袋模型与TF-IDF",
            "id": "nlp-sec-1-2-2",
            "relation_to_previous": "tool_in_toolbox",
            "primary_goal": "完整介绍词袋模型和TF-IDF的核心思想、构建步骤、以及两者作为离散表示方法的优缺点。",
            "suggested_modules": ["code_example", "comparison", "exercise"]
        }},
        {{
            "title": "1.2.3 工具二 (分布式表示)：词向量",
            "id": "nlp-sec-1-2-3",
            "relation_to_previous": "tool_in_toolbox",
            "primary_goal": "介绍词嵌入（Word Embedding）作为分布式表示的核心思想，并解释其如何通过向量空间捕捉词汇的语义关系。",
            "suggested_modules": ["code_example", "case_study"]
        }}
        ]
    }}
    ]
}}
```---
**【全局章节骨架概览（来自 Stage 2）】**

为确保不与其它章节内容重复，并保持全局一致性，以下是整本课程的章节骨架（只含标题与学习目标）。请在设计当前章节时参考该全局结构：

```json
{json.dumps([
    {"index": i+1, "title": ch.get("title"), "objective": ch.get("objective")}
    for i, ch in enumerate(full_skeleton)
], ensure_ascii=False)}
```

当前处理的章节序号（从1开始）: {current_index}

请严格避免与其它章节标题/目标重叠，避免重复覆盖其它章节应讲述的内容；如需承接或引用其它章节，请以“承接第X章 ...”的方式在小节说明中体现。

**【当前任务】**

**章节标题:** `{chapter_title}`

**章节学习目标:** `{chapter_objective}`

请根据以上要求，为**当前任务**的章节设计详细的内部结构，并以JSON格式输出。
"""

def stage3_detail_and_classify(
    caller: LLMCaller,
    topic: str,
    skeleton: Dict[str, Any],
    seeds: Dict[str, Any],
    out_dir: Path,
    basename: str,
    max_tokens: int,
    max_parallel: int,
) -> Dict[str, Any]:
    """ Stage 3: 章节架构师，循环为每个章节设计微观结构。"""
    chapters = skeleton.get("chapters") or []
    detailed_chapters: List[Dict[str, Any]] = []

    print("[阶段 3/4] 开始调用章节架构师，逐章设计微观结构...")

    def design_one_chapter(idx: int, ch_info: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        ch_title = ch_info.get("title") or f"第{idx}章"
        ch_objective = ch_info.get("objective") or ""
        print(f"  -> 正在为章节 '{ch_title}' ({idx}/{len(chapters)}) 设计结构...")
        
        prompt = build_chapter_architect_prompt(
            chapter_title=ch_title,
            chapter_objective=ch_objective,
            full_skeleton=chapters,
            current_index=idx,
        )
        raw = caller.chat_json(prompt, max_tokens=max_tokens)
        
        # 解析LLM返回的单章节JSON
        detailed_chapter_json = extract_json(raw)
        
        if not detailed_chapter_json or not isinstance(detailed_chapter_json, dict):
            print(f"    [警告] 解析章节 '{ch_title}' 的结构失败，将使用空结构。", file=sys.stderr)
            return idx, {"title": ch_title, "id": ch_info.get('id'), "groups": []}

        # 确保顶层信息一致
        detailed_chapter_json['title'] = ch_title
        detailed_chapter_json['id'] = ch_info.get('id')
        detailed_chapter_json['objective'] = ch_objective

        return idx, detailed_chapter_json

    if chapters:
        results: Dict[int, Dict[str, Any]] = {}
        with cf.ThreadPoolExecutor(max_workers=max_parallel) as ex:
            futures = [ex.submit(design_one_chapter, i, ch) for i, ch in enumerate(chapters, start=1)]
            for fut in cf.as_completed(futures):
                idx, detailed_ch = fut.result()
                results[idx] = detailed_ch
        detailed_chapters = [results[i] for i in range(1, len(chapters) + 1)]

    print("  -> 所有章节的微观结构设计完成。 ")
    final_outline = {"chapters": detailed_chapters}
    (out_dir / f"{basename}.outline.stage3.json").write_text(json.dumps(final_outline, ensure_ascii=False, indent=2), encoding="utf-8")
    return final_outline


# -----------------------------
# 统一补默认 + 生成稳定 ID + 渲染 Markdown
# -----------------------------


def apply_defaults_and_ids(topic: str, data: Dict[str, Any]) -> Dict[str, Any]:
    # 允许上游传入 meta.topic_slug（例如外部已生成可读的英文slug）
    pre_slug = (data.get("meta") or {}).get("topic_slug") if isinstance(data.get("meta"), dict) else None
    topic_slug = pre_slug or slugify(topic)
    data.setdefault("meta", {})
    data["meta"].update({"topic": topic, "topic_slug": topic_slug, "schema_version": "pipeline.v1"})
    chapters = data.get("chapters") or []
    for ci, ch in enumerate(chapters, start=1):
        ch_id = f"{topic_slug}-ch-{ci}"
        ch["id"] = ch_id
        groups = ch.get("groups") or []
        for gi, gr in enumerate(groups, start=1):
            gr_id = f"{topic_slug}-gr-{ci}-{gi}"
            gr["id"] = gr_id
            sections = gr.get("sections") or []
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
                # 统一采用 primary_goal + suggested_modules 的软建议模式
                if "primary_goal" not in sec:
                    # 回退兼容旧字段 goal
                    if "goal" in sec:
                        sec["primary_goal"] = sec.get("goal")
                if not isinstance(sec.get("suggested_modules"), list):
                    sec["suggested_modules"] = []
    return data


def render_markdown(data: Dict[str, Any]) -> str:
    topic = data.get("meta", {}).get("topic", "主题")
    topic_slug = data.get("meta", {}).get("topic_slug", slugify(topic))
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
                # 如果标题已包含形如 “X.Y” 或 “X.Y.Z” 的编号前缀，则去掉，避免与我们计算编号重复
                try:
                    import re as _re
                    s_clean = _re.sub(r"^\s*\d+(?:\.\d+)*\s+", "", s_title)
                except Exception:
                    s_clean = s_title
                lines.append(f"#### {ci}.{gi}.{si} {s_clean} (id: {sec.get('id')})")
    return "\n".join(lines) + "\n"

def build_global_review_prompt(topic: str, data_with_ids: Dict[str, Any]) -> str:
    """构建“全局视角”的LLM审阅提示，要求LLM同时输出审核报告和修改后的大纲。"""
    
    outline_json_str = json.dumps(data_with_ids, ensure_ascii=False, indent=2)

    return f"""
你是一个顶级的“课程大纲总编辑”，拥有丰富的教学设计经验和批判性思维。你的任务是分两步完成对一个课程大纲的审阅和修订。

【输入】
待审阅的课程大纲JSON：
```json
{outline_json_str}
```

【任务第一步：内部审阅】
请在你的“脑中”严格依据以下六大“黄金标准”对输入的大纲进行深入分析，并构思出所有必要的修改。

*审阅标准 (黄金标准)*
1.  **逻辑递进性 (Logical Progression)**: 知识点的组织顺序是否符合认知规律？
2.  **知识脚手架 (Knowledge Scaffolding)**: 复杂的后期知识点，其所需的前置基础概念是否已铺垫？
3.  **完整性与覆盖度 (Completeness & Coverage)**: 是否覆盖了所有必要的知识领域？有无关键盲区？
4.  **结构均衡性 (Structural Balance)**: 各章节的体量是否与其重要性大致成正比？命名是否精准？
5.  **实用性与深度 (Practicality & Depth)**: 是否包含实践应用，并深入到“为什么”的层面？
6.  **元数据合理性 (Metadata Suitability)**: `primary_goal` 是否精准切题？`suggested_modules` 是否匹配？

【任务第二步：输出结果】
完成内部审阅和构思后，请将你的工作成果以一个单一JSON对象的格式输出。这个JSON对象必须包含两个顶级键：`review_report` 和 `modified_outline`。

1.  `review_report`: 这是你给人类看的审核报告，记录了你所做的主要修改。请遵循范例的格式，清晰地说明修改的类型、理由和细节。
2.  `modified_outline`: 这是你将所有修改建议应用到原始大纲后，产出的最终的、完整的、结构与输入完全相同的大纲JSON对象。

【高质量范例】
*输入范例 (一个有问题的“面包烘焙”大纲JSON):*
```json
{{
  "meta": {{ "topic": "面包烘焙入门" }},
  "chapters": [
    {{ "title": "第一章：基础原料", "id": "bread-ch-1", "groups": [] }},
    {{ "title": "第二章：高级塑形技巧", "id": "bread-ch-2", "groups": [] }},
    {{
      "title": "第三章：揉面", 
      "id": "bread-ch-3", 
      "groups": [{{
        "title": "3.1 关于酵母的东西", 
        "id": "bread-gr-3-1",
        "sections": [{{ "title": "酵母", "id": "bread-sec-3-1-1", "primary_goal": "学习酵母"}}]
      }}]
    }}
  ]
}}
```

*输出范例 (包含review_report和modified_outline的完整JSON):*
```json
{{
  "review_report": {{
    "overall_assessment": "整体结构存在逻辑问题，且有关键步骤缺失，部分命名和目标过于模糊。",
    "suggested_changes": [
      {{
        "type": "宏观结构调整 - 章节重排序",
        "reasoning": "根据‘逻辑递进性’标准，‘揉面’应在‘高级塑形’之前。",
        "change_detail": "交换了原第二章和第三章的顺序。"
      }},
      {{
        "type": "微观内容调整 - 重命名与目标修正",
        "target_id": "bread-sec-3-1-1",
        "reasoning": "原始命名‘关于酵母的东西’和目标‘学习酵母’过于模糊。",
        "change_detail": "将标题修改为‘激活酵母：发酵成功的第一步’，并具体化了primary_goal。"
      }},
      {{
        "type": "完整性调整 - 补充",
        "reasoning": "缺少了‘烘烤’这一核心环节。",
        "change_detail": "在‘高级塑形技巧’之后补充了新的一章‘第四章：烘烤的艺术’。"
      }}
    ]
  }},
  "modified_outline": {{
    "meta": {{ "topic": "面包烘焙入门" }},
    "chapters": [
      {{ "title": "第一章：基础原料", "id": "bread-ch-1", "groups": [] }},
      {{
        "title": "第二章：揉面与发酵", 
        "id": "bread-ch-3", 
        "groups": [{{
          "title": "2.1 激活酵母：发酵成功的第一步", 
          "id": "bread-gr-3-1",
          "sections": [{{ 
            "title": "激活酵母", 
            "id": "bread-sec-3-1-1", 
            "primary_goal": "解释活性干酵母和即发干酵母的区别，并提供一个激活酵母的详细分步指南。"
          }}]
        }}]
      }},
      {{ "title": "第三章：高级塑形技巧", "id": "bread-ch-2", "groups": [] }},
      {{ "title": "第四章：烘烤的艺术", "id": "bread-ch-4-new", "groups": [] }}
    ]
  }}
}}
```

【你的任务】
现在，请对最上方提供的【输入】大纲进行全面审阅和修订，并严格按照【输出格式】和【高质量范例】的样式，返回一个包含`review_report`和`modified_outline`的最终JSON对象。
"""

def stage4_llm_global_review(
    caller_review: LLMCaller,
    topic: str,
    data_with_ids: Dict[str, Any],
    max_tokens: int = 4096,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """执行LLM全局审阅，返回(审核报告, 修改后的大纲)元组。"""
    prompt = build_global_review_prompt(topic, data_with_ids)
    raw = caller_review.chat_json(prompt, max_tokens=max_tokens)
    parsed_response = extract_json(raw) or {}

    # 安全地提取两个部分
    review_report = parsed_response.get("review_report") or {
        "overall_assessment": "Failed to parse LLM review report.",
        "suggested_changes": [],
    }
    modified_outline = parsed_response.get("modified_outline") or data_with_ids # 如果解析失败，返回原始大纲

    # 包装审核报告，增加模型信息
    final_review_report = {
        "mode": "llm_review_and_apply",
        "model": getattr(caller_review, "conf", None) and getattr(caller_review.conf, "key", None),
        "review": review_report
    }

    return final_review_report, modified_outline


# -----------------------------
# 主流程（四阶段）
# -----------------------------


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="四阶段学习大纲生成（Brainstorm→Structure→Detail→Review）")
    parser.add_argument("--topic", required=True, help="主题")
    parser.add_argument("--depth", choices=["overview", "core", "advanced"], default="core", help="控制规模与粒度")
    parser.add_argument("--language", default="zh", help="输出语言（默认 zh）")
    parser.add_argument("--config", default="config.json", help="配置文件路径")
    parser.add_argument("--llm-gen", help="用于生成（阶段1/2/3细节）的 LLM key（覆盖 config.node_llm.generate_outline）")
    parser.add_argument("--llm-cls", help="用于大纲细化/分类的 LLM key（覆盖 config.node_llm.generate_prompt_template）")
    parser.add_argument("--llm-review", help="用于全局审阅（阶段4 LLM）的 LLM key（覆盖 config.node_llm.generate_and_review_parallel.review）")
    parser.add_argument("--out-dir", default="output", help="输出目录（默认 output）")
    parser.add_argument("--basename", help="输出文件基名（默认由 topic 派生）")
    parser.add_argument("--max-tokens", type=int, default=4096, help="单次调用最大 tokens")
    parser.add_argument("--max-parallel", type=int, help="并发（覆盖 config.max_parallel_requests）")
    parser.add_argument("--resume", action="store_true", help="如存在中间产物则尽量复用（seeds/skeleton）")
    parser.add_argument("--review-mode", choices=["llm", "none"], default="llm", help="阶段4审查模式：llm=执行LLM审核，none=跳过")
    parser.add_argument("--pretty", action="store_true", help="在 stderr 打印简要摘要")

    args = parser.parse_args(argv)

    try:
        cfg = load_config(args.config)
        gen_cfg = choose_llm(cfg, args.llm_gen, "generate_outline")
        cls_cfg = choose_llm(cfg, args.llm_cls, "generate_prompt_template")
        # 审阅模型：优先 --llm-review，其次 node_llm.generate_and_review_parallel.review，最后 fallback default
        review_cfg = None
        if args.review_mode == "llm":
            try:
                review_cfg = choose_llm(cfg, args.llm_review, "generate_and_review_parallel.review")
            except Exception:
                # 尝试 fallback 到 default
                try:
                    review_cfg = choose_llm(cfg, args.llm_review, "default")
                except Exception:
                    review_cfg = None
    except Exception as e:
        print(f"[错误] 读取/选择大模型失败：{e}", file=sys.stderr)
        return 2

    try:
        gen_caller = LLMCaller(gen_cfg)
        cls_caller = LLMCaller(cls_cfg)
        review_caller = None
        if args.review_mode == "llm" and review_cfg is not None:
            review_caller = LLMCaller(review_cfg)
    except SystemExit as e:
        print(str(e), file=sys.stderr)
        return 2
    except Exception as e:
        print(f"[错误] 初始化 LLM 客户端失败：{e}", file=sys.stderr)
        return 2

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    basename = args.basename or slugify(args.topic)

    max_parallel = args.max_parallel or int(cfg.get("max_parallel_requests", 5))
    if max_parallel <= 0:
        max_parallel = 1
    
    print(f"🚀 开始为主题 '{args.topic}' 生成学习大纲...")

    # 阶段 1：seeds
    print("\n[阶段 1/4] 正在进行发散脑暴，生成知识种子...")
    seeds_path = out_dir / f"{basename}.seeds.json"
    if args.resume and seeds_path.exists():
        # If we resume, we can't distinguish professor/engineer seeds.
        # So we load the combined seeds and pass them to both arguments in stage2.
        print("  -> 发现并复用 'seeds.json'。")
        seeds_for_downstream = json.loads(seeds_path.read_text(encoding="utf-8"))
        professor_seeds = seeds_for_downstream.get("seeds", [])
        engineer_seeds = [] # Can't know, so leave empty. Stage 2 prompt will handle it.
        print(f"  -> 复用知识种子 {len(professor_seeds)} 个。")
    else:
        professor_seeds, engineer_seeds = stage1_brainstorm(
            gen_caller, args.topic, args.language, out_dir, basename, args.max_tokens, max_parallel
        )
        # For stage3, it needs a single list. Let's use the combined list from the saved seeds.json
        seeds_for_downstream = json.loads(seeds_path.read_text(encoding="utf-8"))

    # 阶段 2：skeleton
    print("\n[阶段 2/4] 正在聚类与排序，构建章节骨架...")
    skeleton_path = out_dir / f"{basename}.skeleton.json"
    if args.resume and skeleton_path.exists():
        skeleton = json.loads(skeleton_path.read_text(encoding="utf-8"))
        print("  -> 发现并复用 'skeleton.json'。")
    else:
        skeleton = stage2_structure(
            caller=gen_caller,
            topic=args.topic,
            professor_seeds=professor_seeds,
            engineer_seeds=engineer_seeds,
            depth=args.depth,
            language=args.language,
            out_dir=out_dir,
            basename=basename,
            max_tokens=args.max_tokens
        )
    print(f"  -> 章节骨架构建完毕，共 {len(skeleton.get('chapters', []))} 章。")

    # 阶段 3：detail + classify
    stage3 = stage3_detail_and_classify(
        caller=cls_caller, # stage3 uses the classification model
        topic=args.topic,
        skeleton=skeleton,
        seeds=seeds_for_downstream, # Pass the combined seeds dict
        out_dir=out_dir,
        basename=basename,
        max_tokens=args.max_tokens,
        max_parallel=max_parallel,
    )

    print("\n[阶段 4/4] 正在进行最终处理、审查与生成文件...")
    # Stage 3's output is the initial outline
    initial_outline = apply_defaults_and_ids(args.topic, {"chapters": stage3.get("chapters") or []})

    # Always save the pre-review version from Stage 3
    (out_dir / f"{basename}.outline.json").write_text(json.dumps(initial_outline, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  -> 已保存 Stage 3 原始大纲 ({basename}.outline.json)")

    review_json = {"mode": args.review_mode}
    modified_outline = initial_outline # Default to initial if review is skipped

    if args.review_mode == "llm" and review_caller is not None:
        print(f"  -> 开始调用 LLM ({review_caller.conf.key}) 进行全局审阅和修订...")
        review_report, modified_outline_data = stage4_llm_global_review(
            caller_review=review_caller,
            topic=args.topic,
            data_with_ids=initial_outline,
            max_tokens=args.max_tokens,
        )
        review_json.update(review_report)
        modified_outline = modified_outline_data # Use the LLM's modified version
        print("  -> LLM 全局审阅和修订完成。")
    else:
        print("  -> 跳过 Stage 4 审阅。 ")
        review_json["review"] = {"overall_assessment": "Review was skipped.", "suggested_changes": []}

    # Save the review report
    (out_dir / f"{basename}.review.json").write_text(json.dumps(review_json, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  -> 已保存审核报告 ({basename}.review.json)")

    # Save the final, potentially modified outline
    (out_dir / f"{basename}.outline.reviewed.json").write_text(json.dumps(modified_outline, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  -> 已保存 Stage 4 修订后大纲 ({basename}.outline.reviewed.json)")

    # Render and save the final markdown from the MODIFIED outline
    final_md_text = render_markdown(modified_outline)
    (out_dir / f"{basename}.learning-path.md").write_text(final_md_text, encoding="utf-8")
    print(f"  -> 已保存最终学习路径 ({basename}.learning-path.md)")


    print("\n✅ 大纲生成流程完毕！")
    if args.pretty:
        # Use the modified_outline for the final count
        ch_count = len(modified_outline.get("chapters") or [])
        sec_count = sum(len(gr.get("sections") or []) for ch in modified_outline.get("chapters") or [] for gr in ch.get("groups") or [])
        print("---", file=sys.stderr)
        print(f"主题：{args.topic}", file=sys.stderr)
        print(f"生成完成：{out_dir / (basename + '.learning-path.md')}", file=sys.stderr)
        print(f"章节数：{ch_count}，知识点数：{sec_count}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
