#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基于三份顶尖教材目录，重构并整合为“Python 中的异步实现”的入门课程目录（单一 JSON 输出）。

功能
- 读取 scripts/textbook_toc_pipeline_langgraph.py 的输出 JSON（包含 3 本教材目录）。
- 将预置的提示词与输入材料拼接，调用 LLM（config.json 选择，默认 gemini-2.5-pro）。
- 解析仅含 JSON 的响应，写出整合后的新目录 JSON。

使用
  python scripts/pipelines/langgraph/reconstruct_outline_langgraph.py \
    --input output/textbook_tocs/quantum-mechanics-20251016-152638.json \
    --llm-key gemini-2.5-pro \
    --learning-style principles \
    --expected-content "我希望在学习完之后能让我知道量子计算机的运作原理和为什么有显著的速度优势" \
    --print-prompt \
    --stream

依赖
  pip install -U google-generativeai openai
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# -----------------------------
# 常量与工具
# -----------------------------

def _find_repo_root() -> Path:
    p = Path(__file__).resolve()
    for parent in [p] + list(p.parents):
        if (parent / "config.json").exists():
            return parent
    return Path(__file__).resolve().parents[-1]

BASE_DIR = _find_repo_root()
CONFIG_PATH = BASE_DIR / "config.json"


def _load_config(path: Optional[str] = None) -> Dict[str, Any]:
    cfg_path = Path(path) if path else CONFIG_PATH
    if not cfg_path.exists():
        raise SystemExit(f"[错误] 未找到配置文件: {cfg_path}")
    try:
        return json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise SystemExit(f"[错误] 解析配置文件失败: {e}")


def _slugify(text: str, fallback: str = "outline") -> str:
    t = (
        (text or "").replace("（", "(").replace("）", ")").replace("—", "-")
        .strip()
    )
    t = re.sub(r"[^0-9A-Za-z\-_.\s]", "", t)
    t = re.sub(r"\s+", "-", t)
    t = t.strip("-_.").lower()
    return t or fallback


def _extract_json(s: str) -> Dict[str, Any]:
    """从 LLM 原始输出中提取 JSON 对象，并给出具体失败原因。

    解析顺序：
      1) 直接整体解析。
      2) 解析 ```json 围栏内的对象文本。
      3) 截取最外层花括号的子串进行解析。

    若三步均失败，返回包含各步骤错误细节的明确错误信息（含位置与截断的上下文片段）。
    """
    s = (s or "").strip()
    if not s:
        raise ValueError("空响应：模型未返回任何文本。")

    reasons: List[str] = []

    def _mk_snippet(text: str, pos: int | None = None, radius: int = 60) -> str:
        if not text:
            return ""
        if pos is None or pos < 0 or pos >= len(text):
            head = text[:200]
            tail = text[-200:] if len(text) > 400 else ""
            mid = " … " if tail else ""
            return f"head='{head}'{mid}{(' tail=' + tail) if tail else ''}"
        start = max(0, pos - radius)
        end = min(len(text), pos + radius)
        frag = text[start:end]
        return f"near_pos[{pos}]: '{frag}'"

    # 1) 直接解析
    try:
        data = json.loads(s)
        if isinstance(data, dict):
            return data
        reasons.append(f"直接解析得到类型: {type(data).__name__}（顶层需为对象）")
    except json.JSONDecodeError as e:  # type: ignore[attr-defined]
        reasons.append(
            f"直接解析失败: {e.msg} (line {e.lineno}, col {e.colno}) | {_mk_snippet(s, e.pos)}"
        )
    except Exception as e:
        reasons.append(f"直接解析异常: {e!r}")

    # 检测是否包含围栏
    has_fence = "```" in s

    # 2) ```json 包裹
    m = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", s, re.IGNORECASE)
    if not m:
        if has_fence:
            reasons.append("存在代码围栏，但未匹配到 {…} 对象内容")
        else:
            reasons.append("未发现 ```json 围栏")
    else:
        frag = (m.group(1) or "").strip()
        try:
            data = json.loads(frag)
            if isinstance(data, dict):
                return data
            reasons.append(f"```json 围栏内解析到类型: {type(data).__name__}（顶层需为对象）")
        except json.JSONDecodeError as e:  # type: ignore[attr-defined]
            reasons.append(
                f"```json 围栏解析失败: {e.msg} (line {e.lineno}, col {e.colno}) | {_mk_snippet(frag, e.pos)}"
            )
        except Exception as e:
            reasons.append(f"```json 围栏解析异常: {e!r}")

    # 3) 最外层 { ... } 截取
    start = s.find("{")
    end = s.rfind("}")
    if start == -1 or end == -1 or end <= start:
        reasons.append("未找到成对的大括号 { … } 以供截取")
    else:
        frag2 = s[start : end + 1].strip()
        try:
            data = json.loads(frag2)
            if isinstance(data, dict):
                return data
            reasons.append(f"大括号截取解析到类型: {type(data).__name__}（顶层需为对象）")
        except json.JSONDecodeError as e:  # type: ignore[attr-defined]
            reasons.append(
                f"大括号截取解析失败: {e.msg} (line {e.lineno}, col {e.colno}) | {_mk_snippet(frag2, e.pos)}"
            )
        except Exception as e:
            reasons.append(f"大括号截取解析异常: {e!r}")

    # 汇总错误信息
    snippet = _mk_snippet(s)
    reason_text = "; ".join(reasons) if reasons else "未知原因"
    raise ValueError(f"无法从模型输出中提取 JSON 对象：{reason_text} | 输出片段: {snippet}")


# -----------------------------
# LLM 选择与调用
# -----------------------------

@dataclass
class LLMConfig:
    key: str
    provider: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.4


def choose_llm(cfg: Dict[str, Any], llm_key: Optional[str]) -> LLMConfig:
    llms = cfg.get("llms") or {}
    if not llms:
        raise SystemExit("配置中缺少 llms。")
    # 默认优先 gemini-2.5-pro
    default_key = "gemini-2.5-pro" if "gemini-2.5-pro" in llms else None
    key = llm_key or default_key or next(iter(llms.keys()))
    entry = llms.get(key)
    if not entry:
        raise SystemExit(f"在 config.json 中找不到 llm: {key}")
    provider = entry.get("provider", "gemini")
    model = entry.get("model") or key
    api_key = entry.get("api_key") or os.environ.get("OPENAI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    base_url = entry.get("base_url")
    temperature = float(entry.get("temperature", 0.4))
    return LLMConfig(key=key, provider=provider, model=model, api_key=api_key, base_url=base_url, temperature=temperature)


class LLMCaller:
    """最小封装：支持 Gemini 与 OpenAI 兼容端点。"""

    def __init__(self, conf: LLMConfig) -> None:
        self.conf = conf
        self._client = None
        self.last_info: Dict[str, Any] = {}
        self._init()

    def _init(self) -> None:
        provider = (self.conf.provider or "").lower()
        if provider in ("openai", "openai_compat", "deepseek"):
            try:
                from openai import OpenAI
            except Exception:
                raise SystemExit("缺少 openai 库，请先安装：pip install -U openai")
            if not self.conf.api_key:
                raise SystemExit("未配置 OpenAI 兼容 API Key。")
            self._client = OpenAI(api_key=self.conf.api_key, base_url=self.conf.base_url)
        elif provider == "gemini":
            try:
                import google.generativeai as genai
            except Exception:
                raise SystemExit("缺少 google-generativeai 库，请先安装：pip install -U google-generativeai")
            if not self.conf.api_key:
                raise SystemExit("未配置 Gemini API Key。")
            genai.configure(api_key=self.conf.api_key)
            self._client = genai
        else:
            raise SystemExit(f"暂不支持的 provider: {self.conf.provider}")

    def complete(self, prompt: str, max_tokens: int = 65536) -> str:
        provider = (self.conf.provider or "").lower()
        self.last_info = {}
        if provider in ("openai", "openai_compat", "deepseek"):
            try:
                resp = self._client.chat.completions.create(
                    model=self.conf.model,
                    messages=[
                        {"role": "system", "content": "你是一个严谨的课程设计助手。除非被明确要求，否则只输出 JSON。"},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=self.conf.temperature,
                    max_tokens=max_tokens,
                )
            except Exception as e:
                raise RuntimeError(f"OpenAI 兼容端点调用失败: {type(e).__name__}: {e}") from e
            # 记录完成原因
            try:
                ch0 = (getattr(resp, "choices", None) or [None])[0]
                fr = getattr(ch0, "finish_reason", None)
                self.last_info = {"finish_reason": str(fr) if fr is not None else None}
            except Exception:
                pass
            return resp.choices[0].message.content or ""
        elif provider == "gemini":
            model = self._client.GenerativeModel(
                self.conf.model,
                generation_config={
                    "temperature": self.conf.temperature,
                    "max_output_tokens": max_tokens,
                },
            )
            try:
                resp = model.generate_content(prompt)
            except Exception as e:
                # 尝试将 Gemini 的底层错误上抛并保留原始信息
                raise RuntimeError(f"Gemini generate_content 调用失败: {type(e).__name__}: {e}") from e
            # 记录 finish_reason/prompt_feedback 以便诊断是否被截断/拦截
            info: Dict[str, Any] = {}
            try:
                cands = list(getattr(resp, "candidates", []) or [])
                fins = []
                for c in cands:
                    fr = getattr(c, "finish_reason", None)
                    fins.append(str(fr))
                if fins:
                    info["finish_reasons"] = fins
            except Exception:
                pass
            try:
                pf = getattr(resp, "prompt_feedback", None)
                if pf:
                    info["prompt_feedback"] = str(pf)
            except Exception:
                pass
            self.last_info = info
            return getattr(resp, "text", "") or ""
        else:
            raise RuntimeError("未知 provider")

    def stream_complete(self, prompt: str, max_tokens: int = 8192):
        """生成器：以流式方式产出模型输出的文本块。"""
        provider = (self.conf.provider or "").lower()
        self.last_info = {}
        if provider in ("openai", "openai_compat", "deepseek"):
            try:
                stream = self._client.chat.completions.create(
                    model=self.conf.model,
                    messages=[
                        {"role": "system", "content": "你是一个严谨的课程设计助手。除非被明确要求，否则只输出 JSON。"},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=self.conf.temperature,
                    max_tokens=max_tokens,
                    stream=True,
                )
            except Exception as e:
                raise RuntimeError(f"OpenAI 兼容端点流式调用失败: {type(e).__name__}: {e}") from e
            last_finish = None
            for chunk in stream:
                try:
                    choices = getattr(chunk, "choices", None) or []
                    for ch in choices:
                        # 记录最后一个 finish_reason
                        fr = getattr(ch, "finish_reason", None)
                        if fr:
                            last_finish = str(fr)
                        delta = getattr(ch, "delta", None)
                        content = getattr(delta, "content", None) if delta is not None else None
                        if content:
                            yield content
                except Exception:
                    # 某些兼容端点返回结构不同，尝试容错
                    text = getattr(chunk, "text", None)
                    if text:
                        yield text
            self.last_info = {"finish_reason": last_finish}
        elif provider == "gemini":
            model = self._client.GenerativeModel(
                self.conf.model,
                generation_config={
                    "temperature": self.conf.temperature,
                    "max_output_tokens": max_tokens,
                },
            )
            try:
                resp = model.generate_content(prompt, stream=True)
            except Exception as e:
                raise RuntimeError(f"Gemini 流式调用失败: {type(e).__name__}: {e}") from e
            try:
                for ch in resp:
                    text = getattr(ch, "text", None)
                    if text:
                        yield text
                # 确保拉取完整响应（对 Gemini 流重要）
                try:
                    resp.resolve()
                except Exception:
                    pass
            except Exception:
                # 兼容性回退：非流式
                try:
                    full = model.generate_content(prompt)
                except Exception as e:
                    raise RuntimeError(f"Gemini 非流式回退也失败: {type(e).__name__}: {e}") from e
                t = getattr(full, "text", "") or ""
                if t:
                    yield t
                resp = full
            # 记录 finish_reason/prompt_feedback 以便诊断
            info: Dict[str, Any] = {}
            try:
                cands = list(getattr(resp, "candidates", []) or [])
                fins = []
                for c in cands:
                    fr = getattr(c, "finish_reason", None)
                    fins.append(str(fr))
                if fins:
                    info["finish_reasons"] = fins
            except Exception:
                pass
            try:
                pf = getattr(resp, "prompt_feedback", None)
                if pf:
                    info["prompt_feedback"] = str(pf)
            except Exception:
                pass
            self.last_info = info
        else:
            raise RuntimeError("未知 provider")


# -----------------------------
# Prompt 模板
# -----------------------------

PROMPT_CLASSIFY_SUBJECT = r"""
You are a curriculum designer's assistant. Your task is to classify a given subject into one of two categories: "theory" or "tool".

**Category Definitions:**

*   **Theory:** Refers to a field of knowledge, a discipline, or a conceptual framework. It focuses on the "why" and the underlying principles. Learning this involves understanding concepts, models, and their interconnections. Examples: "Natural Language Processing", "Microeconomics", "Deep Learning", "Algorithms".
*   **Tool:** Refers to a specific technology, programming language, library, or framework. It focuses on the "how-to" and practical application. Learning this involves mastering syntax, APIs, commands, and best practices for building things. Examples: "Python", "React", "Tailwind CSS", "Git", "Docker".

**Task:**
Classify the following subject. Respond with a single word: `theory` or `tool`.

**Subject:** "[subject]"
"""

PROMPT_INSTRUCTION_THEORIES = r"""
你是一位顶尖的课程设计师和该领域的专家。你的核心任务是基于以下提供的三份世界顶级教材的目录，为**本科大三学生**设计一份全面而深入的入门课程大纲。

**【核心目标】**
新大纲旨在帮助学习者构建一个**“T型知识结构”**。他们不仅要掌握**[subject]**领域从问题到解决方案的**核心叙事主线（T的横向）**，还必须深入理解每个关键节点上的**核心模型、算法或实现机制（T的纵向）**。学完后，他们应具备分析复杂问题、选择合适模型、并为后续项目实战打下坚实基础的能力。

**【原则要求】**

1.  **原则一：构建‘T型知识’，兼顾宏观叙事与微观深度**：
    *   **宏观叙事（横向）**：清晰地勾勒出领域发展的核心脉络，以一系列**根本性问题（Fundamental Question）**串联起关键的技术范式演进。让学习者理解“为什么需要这项技术”。
    *   **微观深度（纵向）**：对于叙事主线上的每一个**关键技术节点**（如：词向量、RNN、Transformer），必须深入展开，**至少包含**：
        *   **核心思想与工作原理**（The Core Idea & How it Works）。
        *   **关键的技术组件或算法步骤**（Key Components / Algorithmic Steps）。
        *   **该技术的主要变体及其权衡**（Important Variants and Their Trade-offs，例如：LSTM vs. GRU）。
        *   **它的优势与局限性**（Strengths and Limitations）。
    *   **必须排除**：纯粹的历史遗留细节和与主线无关的零散知识点。所有深度内容都必须服务于对核心节点的理解。

2.  **原则二：采用‘问题-思想-机制’的递进式逻辑框架**：
    *   目录结构需清晰地反映该领域的**核心挑战和技术演进**。
    *   每一章节都应围绕一个**“根本性问题”**展开。
    *   在提出问题后，首先介绍解决该问题的**“核心思想/范式”**（Core Idea/Paradigm）。
    *   然后，必须有一个或多个小节专门**“拆解关键机制”**（Unpacking the Key Mechanisms），深入讲解实现该思想的具体模型、结构或算法。
    *   **强调**概念间的依赖关系，例如，清晰地展示RNN如何为Seq2Seq铺路，Seq2Seq的局限性又如何催生了Attention机制。

3.  **原则三：连接‘理论知识’与‘实践应用’**：
    *   最终目标是让学习者获得**‘可应用知识’（Applicable Knowledge）**，能够将理论模型与具体的任务场景联系起来。
    *   每个关键技术节点都必须关联一个**“典型应用场景”或“标准任务”**（Canonical Application / Standard Task），例如：讲解RNN时，关联“语言模型”；讲解Seq2Seq时，关联“机器翻译”。
    *   在适当的地方，可以加入**“案例分析”或“实践指南”**，例如，“如何为一个文本分类任务选择并微调一个合适的预训练模型”。

请根据以上原则，审阅并整合以下提供的三本教材目录，输出一份全新的、符合要求的入门课程目录：

输入材料：textbook_toc_pipeline_langgraph.py 搜集的三份世界级教材目录

学习者期望（可选）

**【设计要求】**
在你的设计中，必须严格遵循以下两种原子结构模型：

*   **流水线 (Pipeline):**
    *   **定义:** 一系列具有**强时序性或强依赖性**的知识点。它们通常描述一个连续的过程、工作流或逻辑推演。
    *   **关键特征:** 前一个知识点的**输出**是后一个知识点的**输入**。学习顺序**几乎不可更改**。
    *   **例子:** 文本预处理流程、数学定理的证明步骤、一个算法的执行过程。

*   **工具箱 (Toolbox):**
    *   **定义:** 一组围绕**共同主题或目标**，但彼此**相对独立**的知识点。
    *   **关键特征:** 知识点之间没有严格的顺序依赖，可以并行学习或按任意顺序学习。它们是解决相关问题的不同方法、工具或概念。
    *   **例子:** Python的各种数据结构、机器学习的各种分类算法、CSS的各种选择器。

**【构建步骤】**
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
        - `suggested_contents`: 该知识点中**建议包含的核心内容**清单（数组）。
5.  **格式化输出:** 确保最终输出是一个结构严谨、格式正确的单一JSON对象，代表这一个章节的完整结构。不要包含任何多余解释性的文字
        
**【输出范例 (JSON)】**
```json
{
    "title": "Natural Language Processing: From Foundations to Large Models",
    "id": "cs-nlp-301",
    "groups": [
        {
            "title": "第一章：基础篇 · 让机器理解语言的基石",
            "id": "nlp-ch-1",
            "structure_type": "pipeline",
            "sections": [
                {
                    "title": "1.1 根本问题：为何机器处理文本如此困难？",
                    "id": "nlp-sec-1-1-1",
                    "relation_to_previous": "first_in_sequence",
                    "primary_goal": "通过展示语言的歧义性、非结构化和多样性，阐明自然语言处理（NLP）领域的核心挑战，并建立起将文本转化为机器可处理格式的必要性。",
                    "suggested_modules": [
                        "case_study",
                        "mermaid diagram"
                    ],
                    "suggested_contents": [
                        "**核心概念：歧义性 (Ambiguity)** - 展示词法歧义 (e.g., 'bank'), 句法歧义 (e.g., 'I saw a man with a telescope'), 和语义歧义的实例。",
                        "**核心挑战：非结构化特性** - 对比非结构化的自然语言与结构化的数据库表格，强调从文本中提取信息的难度。",
                        "**核心挑战：上下文依赖** - 解释同一个词在不同上下文中意义完全不同，引出上下文理解的重要性。",
                        "**基本框架** - 提出NLP任务的基本处理流程：原始文本 -> 预处理 -> 特征表示 -> 模型建模 -> 任务输出。"
                    ]
                },
                {
                    "title": "1.2 文本预处理：从原始语料到结构化词元流",
                    "id": "nlp-sec-1-1-2",
                    "relation_to_previous": "builds_on",
                    "primary_goal": "介绍作为所有NLP任务起点的文本预处理流水线，包括分词（Tokenization）、规范化（Normalization）和过滤（Filtering）等关键步骤及其实现方法。",
                    "suggested_modules": [
                        "code_example",
                        "checklist",
                        "common_mistake_warning"
                    ],
                    "suggested_contents": [
                        "**分词 (Tokenization)** - 讲解词分词、句子分词，并简要介绍更高级的子词分词（如BPE），并讨论其对处理未登录词的优势。",
                        "**规范化 (Normalization)** - 详细对比词干提取 (Stemming) 和词形还原 (Lemmatization) 的区别，并提供具体例子 (e.g., 'studies' -> 'studi' vs. 'study')。",
                        "**过滤 (Filtering)** - 解释停用词 (Stop Words) 移除的概念，并讨论何时应该（或不应该）移除停用词。",
                        "**代码实践** - 提供使用NLTK或spaCy库完成一套完整预处理流程的Python代码片段。"
                    ]
                }
            ]
        },
        {
            "title": "第二章：文本表示 · 将词语转化为向量",
            "id": "nlp-ch-2",
            "structure_type": "toolbox",
            "sections": [
                {
                    "title": "2.1 核心思想：分布式表示假说",
                    "id": "nlp-sec-2-1-1",
                    "relation_to_previous": "first_in_sequence",
                    "primary_goal": "解释将词语映射到向量空间的核心思想，并引入“一个词的含义由其上下文决定”的分布式假说，作为理解现代词向量模型的基础。",
                    "suggested_modules": [
                        "mermaid diagram"
                    ],
                    "suggested_contents": [
                        "**核心引言** - 引用J.R. Firth的名言：'You shall know a word by the company it keeps.'",
                        "**向量空间类比** - 使用2D/3D图示展示词向量关系，例如著名的 `vector('King') - vector('Man') + vector('Woman') ≈ vector('Queen')`。",
                        "**分布式 vs. 符号表示** - 对比词向量（分布式）与One-Hot编码（符号式）的差异，强调分布式表示的语义捕捉能力。"
                    ]
                },
                {
                    "title": "2.2 工具一 (统计方法)：TF-IDF与词袋模型",
                    "id": "nlp-sec-2-2-1",
                    "relation_to_previous": "tool_in_toolbox",
                    "primary_goal": "详细拆解词袋模型（BoW）和TF-IDF的计算原理，并分析它们作为稀疏、离散表示方法的优势（简单、可解释）与核心局限（无法捕捉语义、维度灾难）。",
                    "suggested_modules": [
                        "code_example",
                        "comparison"
                    ],
                    "suggested_contents": [
                        "**词袋模型 (BoW)** - 解释如何将一个句子或文档表示为一个忽略语序的词频向量。",
                        "**TF-IDF计算** - 分步讲解词频 (Term Frequency) 和逆文档频率 (Inverse Document Frequency) 的计算公式和直觉含义。",
                        "**动手计算** - 提供一个包含3-4个短文档的小型语料库，手动计算其中某个词的TF-IDF值。",
                        "**优劣分析** - 总结其优点（简单高效）和缺点（稀疏性、维度灾难、无语义信息）。"
                    ]
                },
                {
                    "title": "2.3 工具二 (预测方法)：静态词向量 (Word2Vec & GloVe)",
                    "id": "nlp-sec-2-2-2",
                    "relation_to_previous": "tool_in_toolbox",
                    "primary_goal": "深入讲解Word2Vec（包括Skip-gram和CBOW变体）和GloVe的核心工作原理，阐明它们如何通过预测上下文来学习捕捉词汇语义关系的密集向量。",
                    "suggested_modules": [
                        "code_example",
                        "comparison",
                        "case_study"
                    ],
                    "suggested_contents": [
                        "**Word2Vec核心原理** - 使用图示解释Skip-gram（中心词预测上下文）和CBOW（上下文预测中心词）的神经网络结构。",
                        "**GloVe核心原理** - 解释GloVe如何结合全局词-词共现矩阵的统计信息与预测方法的优点。",
                        "**代码实践** - 展示如何加载预训练的Word2Vec或GloVe模型，并用它来寻找近义词或完成词汇类比任务。",
                        "**可视化** - 使用t-SNE等降维方法可视化词向量空间，直观感受语义相近的词在空间中聚集的现象。"
                    ]
                },
                {
                    "title": "2.4 局限性：静态词向量无法解决的问题",
                    "id": "nlp-sec-2-2-3",
                    "relation_to_previous": "builds_on",
                    "primary_goal": "通过“一词多义”等具体案例，揭示所有静态词向量方法的共同缺陷——无法根据上下文动态调整词义，为后续引入上下文相关的表示方法埋下伏笔。",
                    "suggested_modules": [
                        "common_mistake_warning"
                    ],
                    "suggested_contents": [
                        "**“一词多义”问题** - 用'bank'（银行/河岸）或'stick'（棍子/坚持）的例子，说明静态词向量无法区分同一个词在不同语境下的含义。",
                        "**上下文无关** - 强调静态词向量为每个词生成一个固定的向量，无论其上下文如何变化。",
                        "**引出下一章** - 明确指出解决此问题的关键在于模型需要具备理解和记忆上下文的能力。"
                    ]
                }
            ]
        }
    ]
}
```
"""


# 新增：理论类（原理学习 principles）风格的完整 Prompt（与 deep_preview 平行，保持相同输出协议）
PROMPT_INSTRUCTION_THEORIES_PRINCIPLES = r"""
你是一位顶尖的课程设计师和该领域的专家。你的核心任务是基于以下提供的三份世界顶级教材的目录，为**本科大三学生**设计一份全面而深入的入门课程大纲。

**【核心目标】**
新目录旨在帮助学习者快速构建对**[subject]**核心原理的**概念脚手架（Conceptual Scaffold）**。学完后，他们应能运用所学知识解释该领域的基本现象，并为后续的深入学习打下坚实、结构化的基础。

**【原则要求】**
1.  **遵循80/20原则，聚焦核心**：
    *   专注于阐释该领域中，能够解释80%现象的20%核心公理、模型或理论。
    *   **必须排除**：1）历史上重要但已过时的细节；2）过于细分的专业分支内容；3）复杂的数学推导或非必要的实现细节。
    *   重点应放在该领域的**第一性原理（First Principles）、核心思想（Core Ideas）和分析框架（Analytical Frameworks）**上，而非零散的知识点。

2.  **构建‘问题-解决方案’的逻辑框架**：
    *   目录结构需清晰地反映该领域的**核心结构（例如：从宏观到微观，从理论到应用，按时间线发展）**。
    *   每一章节都应以该领域的一个**根本性问题（Fundamental Question）**为驱动（例如，“社会财富是如何创造和分配的？” -> 经济学中的生产与分配理论）。
    *   **特别强调**不同概念之间的内在逻辑和依赖关系，让知识形成一个连贯、自洽的体系。

3.  **强调‘解释性知识’与现实世界的联系**：
    *   最终目标是让学习者获得**‘解释性知识’（Explanatory Knowledge）**，使他们能够用学科视角**分析和解释**现实世界中的相关现象，而不是进行专业级别的操作或计算。
    *   每个核心概念都必须与一个**具体、可感知的现实案例或应用场景强绑定**（例如，讲解“机会成本”时，要关联到“选择读研而非工作的得失”）。
    *   鼓励在章节命名和内容描述中使用**生动、恰当的类比**，以降低非专业人士的认知门槛，并建立直观理解。

请根据以上原则，审阅并整合以下提供的三本教材目录，输出一份全新的、符合要求的入门课程目录：

输入材料：textbook_toc_pipeline_langgraph.py 搜集的三份世界级教材目录

学习者期望（可选）

**【设计要求】**
在你的设计中，必须严格遵循以下两种原子结构模型：

*   **流水线 (Pipeline):**
    *   **定义:** 一系列具有**强时序性或强依赖性**的知识点。它们通常描述一个连续的过程、工作流或逻辑推演。
    *   **关键特征:** 前一个知识点的**输出**是后一个知识点的**输入**。学习顺序**几乎不可更改**。
    *   **例子:** 文本预处理流程、数学定理的证明步骤、一个算法的执行过程。

*   **工具箱 (Toolbox):**
    *   **定义:** 一组围绕**共同主题或目标**，但彼此**相对独立**的知识点。
    *   **关键特征:** 知识点之间没有严格的顺序依赖，可以并行学习或按任意顺序学习。它们是解决相关问题的不同方法、工具或概念。
    *   **例子:** Python的各种数据结构、机器学习的各种分类算法、CSS的各种选择器。

**【构建步骤】**
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
        - `suggested_contents`: 该知识点中**建议包含的核心内容**清单（数组）。
5.  **格式化输出:** 确保最终输出是一个结构严谨、格式正确的单一JSON对象，代表这一个章节的完整结构。不要包含任何多余解释性的文字
        
**【输出范例 (JSON)】**
```json
{
    "title": "Natural Language Processing: From Foundations to Large Models",
    "id": "cs-nlp-301",
    "groups": [
        {
            "title": "第一章：基础篇 · 让机器理解语言的基石",
            "id": "nlp-ch-1",
            "structure_type": "pipeline",
            "sections": [
                {
                    "title": "1.1 根本问题：为何机器处理文本如此困难？",
                    "id": "nlp-sec-1-1-1",
                    "relation_to_previous": "first_in_sequence",
                    "primary_goal": "通过展示语言的歧义性、非结构化和多样性，阐明自然语言处理（NLP）领域的核心挑战，并建立起将文本转化为机器可处理格式的必要性。",
                    "suggested_modules": [
                        "case_study",
                        "mermaid diagram"
                    ],
                    "suggested_contents": [
                        "**核心概念：歧义性 (Ambiguity)** - 展示词法歧义 (e.g., 'bank'), 句法歧义 (e.g., 'I saw a man with a telescope'), 和语义歧义的实例。",
                        "**核心挑战：非结构化特性** - 对比非结构化的自然语言与结构化的数据库表格，强调从文本中提取信息的难度。",
                        "**核心挑战：上下文依赖** - 解释同一个词在不同上下文中意义完全不同，引出上下文理解的重要性。",
                        "**基本框架** - 提出NLP任务的基本处理流程：原始文本 -> 预处理 -> 特征表示 -> 模型建模 -> 任务输出。"
                    ]
                },
                {
                    "title": "1.2 文本预处理：从原始语料到结构化词元流",
                    "id": "nlp-sec-1-1-2",
                    "relation_to_previous": "builds_on",
                    "primary_goal": "介绍作为所有NLP任务起点的文本预处理流水线，包括分词（Tokenization）、规范化（Normalization）和过滤（Filtering）等关键步骤及其实现方法。",
                    "suggested_modules": [
                        "code_example",
                        "checklist",
                        "common_mistake_warning"
                    ],
                    "suggested_contents": [
                        "**分词 (Tokenization)** - 讲解词分词、句子分词，并简要介绍更高级的子词分词（如BPE），并讨论其对处理未登录词的优势。",
                        "**规范化 (Normalization)** - 详细对比词干提取 (Stemming) 和词形还原 (Lemmatization) 的区别，并提供具体例子 (e.g., 'studies' -> 'studi' vs. 'study')。",
                        "**过滤 (Filtering)** - 解释停用词 (Stop Words) 移除的概念，并讨论何时应该（或不应该）移除停用词。",
                        "**代码实践** - 提供使用NLTK或spaCy库完成一套完整预处理流程的Python代码片段。"
                    ]
                }
            ]
        },
        {
            "title": "第二章：文本表示 · 将词语转化为向量",
            "id": "nlp-ch-2",
            "structure_type": "toolbox",
            "sections": [
                {
                    "title": "2.1 核心思想：分布式表示假说",
                    "id": "nlp-sec-2-1-1",
                    "relation_to_previous": "first_in_sequence",
                    "primary_goal": "解释将词语映射到向量空间的核心思想，并引入“一个词的含义由其上下文决定”的分布式假说，作为理解现代词向量模型的基础。",
                    "suggested_modules": [
                        "mermaid diagram"
                    ],
                    "suggested_contents": [
                        "**核心引言** - 引用J.R. Firth的名言：'You shall know a word by the company it keeps.'",
                        "**向量空间类比** - 使用2D/3D图示展示词向量关系，例如著名的 `vector('King') - vector('Man') + vector('Woman') ≈ vector('Queen')`。",
                        "**分布式 vs. 符号表示** - 对比词向量（分布式）与One-Hot编码（符号式）的差异，强调分布式表示的语义捕捉能力。"
                    ]
                },
                {
                    "title": "2.2 工具一 (统计方法)：TF-IDF与词袋模型",
                    "id": "nlp-sec-2-2-1",
                    "relation_to_previous": "tool_in_toolbox",
                    "primary_goal": "详细拆解词袋模型（BoW）和TF-IDF的计算原理，并分析它们作为稀疏、离散表示方法的优势（简单、可解释）与核心局限（无法捕捉语义、维度灾难）。",
                    "suggested_modules": [
                        "code_example",
                        "comparison"
                    ],
                    "suggested_contents": [
                        "**词袋模型 (BoW)** - 解释如何将一个句子或文档表示为一个忽略语序的词频向量。",
                        "**TF-IDF计算** - 分步讲解词频 (Term Frequency) 和逆文档频率 (Inverse Document Frequency) 的计算公式和直觉含义。",
                        "**动手计算** - 提供一个包含3-4个短文档的小型语料库，手动计算其中某个词的TF-IDF值。",
                        "**优劣分析** - 总结其优点（简单高效）和缺点（稀疏性、维度灾难、无语义信息）。"
                    ]
                },
                {
                    "title": "2.3 工具二 (预测方法)：静态词向量 (Word2Vec & GloVe)",
                    "id": "nlp-sec-2-2-2",
                    "relation_to_previous": "tool_in_toolbox",
                    "primary_goal": "深入讲解Word2Vec（包括Skip-gram和CBOW变体）和GloVe的核心工作原理，阐明它们如何通过预测上下文来学习捕捉词汇语义关系的密集向量。",
                    "suggested_modules": [
                        "code_example",
                        "comparison",
                        "case_study"
                    ],
                    "suggested_contents": [
                        "**Word2Vec核心原理** - 使用图示解释Skip-gram（中心词预测上下文）和CBOW（上下文预测中心词）的神经网络结构。",
                        "**GloVe核心原理** - 解释GloVe如何结合全局词-词共现矩阵的统计信息与预测方法的优点。",
                        "**代码实践** - 展示如何加载预训练的Word2Vec或GloVe模型，并用它来寻找近义词或完成词汇类比任务。",
                        "**可视化** - 使用t-SNE等降维方法可视化词向量空间，直观感受语义相近的词在空间中聚集的现象。"
                    ]
                },
                {
                    "title": "2.4 局限性：静态词向量无法解决的问题",
                    "id": "nlp-sec-2-2-3",
                    "relation_to_previous": "builds_on",
                    "primary_goal": "通过“一词多义”等具体案例，揭示所有静态词向量方法的共同缺陷——无法根据上下文动态调整词义，为后续引入上下文相关的表示方法埋下伏笔。",
                    "suggested_modules": [
                        "common_mistake_warning"
                    ],
                    "suggested_contents": [
                        "**“一词多义”问题** - 用'bank'（银行/河岸）或'stick'（棍子/坚持）的例子，说明静态词向量无法区分同一个词在不同语境下的含义。",
                        "**上下文无关** - 强调静态词向量为每个词生成一个固定的向量，无论其上下文如何变化。",
                        "**引出下一章** - 明确指出解决此问题的关键在于模型需要具备理解和记忆上下文的能力。"
                    ]
                }
            ]
        }
    ]
}
```
"""

# 专用于“工具类（Tool）”主题的大纲生成 Prompt
PROMPT_INSTRUCTION_TOOLS = r"""
这份大纲旨在构建一个**“技能金字塔”**。学习者将从最基础的语法和概念（金字塔的底层）开始，通过一系列精心设计的、层层递进的知识点，逐步掌握更高级的特性和应用模式，最终达到能够独立使用 **[subject]** 进行项目开发的水平（金字塔的顶层）。

**【核心原则】**
1.  **原则一：循序渐进，构建稳固的技能阶梯**：
    *   **严格的自底向上结构**：必须从该工具最核心、最基础的“原子”知识点开始（例如，编程语言从“变量和数据类型”开始）。
    *   **清晰的依赖关系**：后续章节必须建立在前面章节知识的基础之上。
    *   **从“是什么”到“怎么用”**：每个大的模块都应遵循从基础概念到实际应用的逻辑。

2.  **原则二：闭环教学，融合‘是什么’‘怎么用’与‘为何这么用’**：
    *   对于每一个关键知识点，其内容设计应围绕三个核心：
        *   **核心语法/API (是什么)**：清晰地展示如何使用该功能。
        *   **核心概念 (怎么用)**：用简洁的语言解释其工作原理和目的。
        *   **典型用法与最佳实践 (为何这么用)**：提供最常见的应用场景或社区推崇的最佳实践。

3.  **原则三：结构化输出，为下游生成提供精确指令**：
    *   最终的输出必须是结构化的JSON，作为下一阶段内容生成的“教学大纲”和“明确指令”。
    *   必须合理使用 `pipeline` (强顺序依赖) 和 `toolbox` (功能相关但无序) 两种结构类型来组织知识点。

**输入材料 (可选):**
如果提供了相关的参考资料（如其他课程大纲），请进行整合和提炼。如果没有提供，请基于你对该工具的通用知识来构建大纲。

学习者期望（可选）

**【构建步骤】**
1.  **分析与分组:** 基于 **[subject]** 的内在逻辑，设计出层层递进的章节（Group）。
2.  **设计微观结构:** 在每个章节内部，排列知识点（Section）的顺序，确保逻辑通顺。
3.  **精炼标题:** 撰写清晰、简洁、面向实践的标题。
4.  **注入元数据 (关键):** 在最终的JSON结构中，为每个小节（Group）和知识点（Section）添加元数据：
    *   `structure_type: "pipeline" | "toolbox"`
    *   `relation_to_previous`: `builds_on | tool_in_toolbox | alternative_to | deep_dive_into | first_in_sequence`
    *   `primary_goal`: 用一句话清晰地定义该知识点的**核心内容目标**。
    *   `suggested_modules`: 教学模块建议清单，可从 `["code_example", "common_mistake_warning", "comparison", "case_study", "mermaid_diagram"]` 中选择。
    *   `suggested_contents`: **建议包含的核心内容**关键词清单。
5.  **内容限定:** 直接输出需要学习的内容，不要包含 学习背景、环境调试、安装配置 等与核心技能无关的内容。
6.  **格式化输出:** 你的输出必须是一个单一的、完整的、语法正确的 JSON 对象，不能包含任何解释性文字、注释或 Markdown 标记。


**【输出范例 (JSON)】**
```json
{
    "title": "Python 核心技能路径",
    "id": "python-core",
    "groups": [
        {
            "title": "第一章：基础语法与数据类型",
            "id": "py-ch-1",
            "structure_type": "pipeline",
            "sections": [
                {
                    "title": "1.2 字符串操作",
                    "id": "py-sec-1-2",
                    "relation_to_previous": "builds_on",
                    "primary_goal": "深入讲解字符串的常用操作，包括格式化、切片和常用方法，这是文本处理的基础。",
                    "suggested_modules": [
                        "code_example",
                        "comparison",
                        "common_mistake_warning"
                    ],
                    "suggested_contents": [
                        "f-string 格式化",
                        "字符串切片 [start:stop:step]",
                        "字符串方法 .strip()",
                        "字符串方法 .split()",
                        "字符串方法 .join()",
                        "字符串拼接 (+)"
                    ]
                }
            ]
        }
    ]
}
"""


def build_prompt(
    subject: str,
    materials: Dict[str, Any],
    subject_type: str,
    learning_style: Optional[str] = None,
    expected_content: Optional[str] = None,
) -> str:
    subject_type = (subject_type or "theory").strip().lower()
    # 仅投喂 tocs 列表，避免包裹额外说明字段
    mat_obj = {"tocs": materials.get("materials") or []}
    mat_json = json.dumps(mat_obj, ensure_ascii=False, indent=2)

    # 统一期望文段
    expect_clean = (expected_content or "").strip()
    expect_placeholder = "学习者期望（可选）"
    expect_injection = (
        "\n\n【学习者期望】\n" + expect_clean + "\n" if expect_clean else ""
    )

    if subject_type == "tool":
        # 工具类：材料为可选参考；风格参数不生效
        text = PROMPT_INSTRUCTION_TOOLS.strip()
        try:
            text = re.sub(r"\[subject\]", subject, text)
        except Exception:
            text = text.replace("[subject]", subject)
        if (materials.get("materials") or []):
            injection = (
                "\n\n【可选参考材料（JSON）】如有以下教材目录可参考：\n"
                "```json\n" + mat_json + "\n```\n"
            )
            text = text + "\n" + injection
        # 期望内容：在材料之后追加；若模板中包含占位符，则先移除以避免裸占位
        if expect_clean:
            text = text.replace(expect_placeholder, "")
            text = text + "\n" + expect_injection
        else:
            text = text.replace(expect_placeholder, "")
        return text

    # 理论类：按学习风格选择 prompt（deep_preview 使用现有模板；principles 使用新模板）
    style = (learning_style or "deep_preview").strip().lower()
    if style == "principles":
        text = PROMPT_INSTRUCTION_THEORIES_PRINCIPLES.strip()
    else:
        text = PROMPT_INSTRUCTION_THEORIES.strip()
    try:
        text = re.sub(r"\[subject\]", subject, text)
    except Exception:
        text = text.replace("[subject]", subject)
    placeholder = "输入材料：textbook_toc_pipeline_langgraph.py 搜集的三份世界级教材目录"
    injection = (
        "\n\n【输入材料（JSON）】三本教材目录如下：\n"
        "```json\n" + mat_json + "\n```\n"
    )
    if placeholder in text:
        parts = text.split(placeholder)
        text = parts[0] + injection + (parts[1] if len(parts) > 1 else "")
    else:
        text = text + "\n" + injection
    # 期望内容：尽量使用占位符位置（放在输入材料之后）；若缺失则在材料段之后紧跟追加
    if expect_clean:
        if expect_placeholder in text:
            text = text.replace(expect_placeholder, expect_injection)
        else:
            text = text + "\n" + expect_injection
    else:
        text = text.replace(expect_placeholder, "")
    return text


# -----------------------------
# I/O 处理
# -----------------------------


def _load_toc_input(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise SystemExit(f"[错误] 读取/解析输入文件失败: {e}")
    if not isinstance(data, dict) or "tocs" not in data:
        raise SystemExit("[错误] 输入 JSON 无效：缺少 'tocs' 字段。")
    return data


def _prepare_materials(input_obj: Dict[str, Any], limit: int = 3) -> Dict[str, Any]:
    subject = str(input_obj.get("subject") or "Python 中的异步实现")
    tocs: List[Dict[str, Any]] = input_obj.get("tocs", []) or []
    items: List[Dict[str, Any]] = []
    for t in tocs:
        if not isinstance(t, dict):
            continue
        if t.get("error"):
            continue
        items.append({
            "book": t.get("book", {}),
            "toc": t.get("toc", []),
            "source": t.get("source", ""),
        })
        if len(items) >= limit:
            break
    return {"subject": subject, "materials": items}


# -----------------------------
# 分类：theory / tool
# -----------------------------

def classify_subject(subject: str, llm: LLMCaller) -> str:
    """调用轻量模型对主题分类。

    返回：
      - 'theory' 或 'tool' 之一；
      - 若出错或输出异常，返回以 'error:' 开头的错误信息字符串（不回退为 'theory'）。
    """
    try:
        prompt = PROMPT_CLASSIFY_SUBJECT.replace("[subject]", subject)
        resp = llm.complete(prompt, max_tokens=1096)
    except Exception as e:
        return f"error: classify failed: {e}"
    ans = (resp or "").strip().strip('`"\'').lower()
    if ans in {"tool", "theory"}:
        return ans
    return f"error: unexpected classifier output: {ans!r}"


# -----------------------------
# main
# -----------------------------


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="整合 3 本教材目录 → 入门课程 JSON（只输出 JSON）")
    p.add_argument("--input", required=True, help="textbook_toc_pipeline_langgraph.py 的输出 JSON 文件路径，或目录（取最新）")
    p.add_argument("--llm-key", default=None, help="config.json.llms 的键名（默认 gemini-2.5-pro）")
    p.add_argument("--classifier-llm-key", default=None, help="用于主题分类的 LLM 键名（默认 gemini-2.5-flash 如存在）")
    p.add_argument("--subject-type", choices=["theory", "tool"], default=None, help="手工指定主题类型，跳过自动分类")
    p.add_argument("--learning-style", required=True, default="原理学习", help="学习风格（必选，仅理论类生效）：principles | deep_preview | 原理学习 | 深度预习")
    p.add_argument("--expected-content", default=None, help="学习者期望（可选，作为 prompt 追加，放在输入材料之后）")
    p.add_argument("--config", default=str(CONFIG_PATH), help="配置文件路径（默认项目根 config.json）")
    p.add_argument("--out", default=None, help="输出文件路径；未提供则自动生成到 output/reconstructed_outline")
    p.add_argument("--max-tokens", type=int, default=65536, help="最大 tokens，默认 8192")
    p.add_argument("--print-prompt", action="store_true", help="在终端输出发送给 LLM 的完整 Prompt 以便调试")
    p.add_argument("--stream", action="store_true", help="启用流式输出，在控制台实时显示模型响应")
    args = p.parse_args(argv)

    in_path = Path(args.input)
    if in_path.is_dir():
        # 目录下选择最近修改的 json
        cands = sorted(in_path.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        if not cands:
            print("[错误] 输入目录中未找到 .json 文件。", file=sys.stderr)
            return 2
        in_path = cands[0]

    input_obj = _load_toc_input(in_path)
    subject = str(input_obj.get("subject"))
    materials = _prepare_materials(input_obj, limit=3)

    cfg = _load_config(args.config)
    # 规范化/校验学习风格
    def _normalize_style(s: Optional[str]) -> str:
        val = (s or "").strip().lower()
        mapping = {
            "principles": "principles",
            "原理学习": "principles",
            "deep_preview": "deep_preview",
            "深度预习": "deep_preview",
        }
        return mapping.get(val, mapping.get(s or "", ""))

    norm_style = _normalize_style(args.learning_style)
    if norm_style not in ("principles", "deep_preview"):
        print("[错误] --learning-style 必须为 principles/deep_preview 或 对应中文：原理学习/深度预习", file=sys.stderr)
        return 2
    llm_conf = choose_llm(cfg, args.llm_key)

    # 分类模型（优先 gemini-2.5-flash）
    default_classifier_key = "gemini-2.5-flash" if (cfg.get("llms") or {}).get("gemini-2.5-flash") else None
    classifier_conf = choose_llm(cfg, args.classifier_llm_key or default_classifier_key)
    classifier = LLMCaller(classifier_conf)

    # 决定 subject_type
    if args.subject_type:
        subject_type = args.subject_type
    else:
        subject_type = classify_subject(subject, classifier)
        if subject_type not in ("theory", "tool"):
            print(f"[错误] 主题分类失败: {subject_type}", file=sys.stderr)
            return 3
    print(f"[信息] 主题分类结果: {subject} → {subject_type}", file=sys.stderr)

    # 组装 prompt 并调用 LLM（根据主题类型 + 学习风格路由；tool 分支忽略风格）
    prompt = build_prompt(
        subject,
        materials,
        subject_type,
        learning_style=norm_style,
        expected_content=(args.expected_content or "").strip() or None,
    )
    if args.print_prompt:
        print("========== DEBUG: Prompt Begin ==========", file=sys.stderr)
        print(prompt, file=sys.stderr)
        print("=========== DEBUG: Prompt End ===========", file=sys.stderr)
    caller = LLMCaller(llm_conf)
    if args.stream:
        print("[信息] 正在以流式方式接收模型输出…", file=sys.stderr)
        buf: List[str] = []
        try:
            for piece in caller.stream_complete(prompt, max_tokens=args.max_tokens):
                buf.append(piece)
                # 实时打印到 stderr，不干扰最终文件输出
                print(piece, end="", file=sys.stderr, flush=True)
        except Exception as e:
            print("[错误] LLM 流式调用失败:", f"{type(e).__name__}: {e}", file=sys.stderr)
            return 1
        print("", file=sys.stderr)  # 换行
        raw = "".join(buf)
    else:
        try:
            raw = caller.complete(prompt, max_tokens=args.max_tokens)
        except Exception as e:
            print("[错误] LLM 调用失败:", f"{type(e).__name__}: {e}", file=sys.stderr)
            return 1

    # 如有完成原因/拦截信息，输出提示（便于诊断截断/安全拦截）
    try:
        info = getattr(caller, "last_info", None) or {}
        if info:
            print(f"[调试] LLM 完成信息: {info}", file=sys.stderr)
    except Exception:
        pass
    try:
        output_obj = _extract_json(raw)
    except Exception as e:
        print("[错误] 解析 LLM 输出失败（已包含具体原因）:", e, file=sys.stderr)
        print("[建议] 可使用 --print-prompt 或 --stream 以诊断提示词与响应。", file=sys.stderr)
        return 1

    # 注入元数据：记录主题与分类（用于后续内容生成分叉）
    try:
        if isinstance(output_obj, dict):
            meta = output_obj.get("meta")
            if not isinstance(meta, dict):
                meta = {}
            meta.setdefault("subject", subject)
            meta.setdefault("subject_type", subject_type)
            meta.setdefault("learning_style", norm_style)
            if args.expected_content is not None:
                meta.setdefault("expected_content", (args.expected_content or "").strip())
            # 若上游输入包含 subject_slug，也写入，便于后续链路使用
            try:
                in_slug = (input_obj.get("subject_slug") or "").strip()
                if in_slug:
                    meta.setdefault("subject_slug", in_slug)
            except Exception:
                pass
            output_obj["meta"] = meta
    except Exception:
        pass

    # 输出位置
    if args.out:
        out_path = Path(args.out)
    else:
        out_dir = BASE_DIR / "output" / "reconstructed_outline"
        out_dir.mkdir(parents=True, exist_ok=True)
        # 优先使用输入 JSON 的 subject_slug；
        # 若缺失则基于 subject 生成 slug（回退为 'subject' 以避免历史固定前缀）。
        in_slug = (input_obj.get("subject_slug") or "").strip()
        slug = in_slug or _slugify(subject or "", "subject")
        out_path = out_dir / f"{slug}-reconstructed-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"

    out_path.write_text(json.dumps(output_obj, ensure_ascii=False, indent=2), encoding="utf-8")

    # 简要摘要到 stderr
    print(f"[完成] 已生成整合目录: {out_path}", file=sys.stderr)
    print(f"使用模型: {llm_conf.key} ({llm_conf.provider}:{llm_conf.model})", file=sys.stderr)
    print(f"输入教材数: {len(materials.get('materials') or [])}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
