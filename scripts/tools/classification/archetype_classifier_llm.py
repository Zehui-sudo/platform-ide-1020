#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
仅使用大模型（LLM）进行知识点原型判别的脚本。

功能：
- 输入：Markdown 学习大纲文件路径（例如：web-learner/public/javascript-learning-path.md）
- 输出：逐条知识点的判别结果（9 大原型 + 开关），以及模型给出的置信度与简要理由。

特点：
- 不包含任何本地规则或关键词打分逻辑，判别完全依赖 LLM。
- 通过根目录 config.json 中的 llms 配置选择具体模型（支持 deepseek 的 OpenAI 兼容接口、Gemini）。
- 输出为 JSONL（每行一个 JSON 对象），便于下游管道消费。

使用示例：
  python scripts/archetype_classifier_llm.py web-learner/public/javascript-learning-path.md \
    --config config.json --llm deepseek-chat --output out.jsonl --pretty

依赖：
- 对 deepseek（OpenAI 兼容）需要安装 openai 库：pip install openai
- 对 gemini 需要安装 google-generativeai：pip install google-generativeai

注意：
- 本脚本只负责“判别”，不生成内容。
- 若 LLM 返回非 JSON，将尝试从回复中提取 JSON；多次失败则回退为低置信度的占位结果。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import concurrent.futures as cf


# -----------------------------
# Markdown 大纲解析（仅负责提取知识点）
# -----------------------------


HEADING_RE = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<text>.+?)\s*$")
LIST_RE = re.compile(r"^(?P<indent>\s*)(?:[-*+]|\d+\.)\s+(?P<text>.+?)\s*$")
CODE_FENCE_RE = re.compile(r"^\s*```")

# learning-path 专用标题格式（带 id 标签）
H1_WITH_ID = re.compile(r"^#\s+(?P<title>.+?)\s*\(id:\s*(?P<id>[^)]+)\)\s*$")
H2_CHAPTER = re.compile(r"^##\s+(?P<title>.+?)\s*\(id:\s*(?P<id>[^)]+)\)\s*$")
H3_GROUP = re.compile(r"^###\s+(?P<num>[\d\.]+)?\s*(?P<title>.+?)\s*\(id:\s*(?P<id>[^)]+)\)\s*$")
H4_SECTION = re.compile(r"^####\s+(?P<num>[\d\.]+)?\s*(?P<title>.+?)\s*\(id:\s*(?P<id>[^)]+)\)\s*$")


@dataclass
class Point:
    """代表一个知识点。

    适配 learning-path：以四级标题（#### ... (id: js-sec-...)）为知识点。
    """

    id: int  # 递增编号，便于展示
    text: str  # 知识点标题文本（不含 id 部分）
    path: List[str]  # [H1, Chapter, Group, Title]
    line_no: int
    source_id: Optional[str] = None  # 原始 (id: js-sec-...) 值


def parse_markdown_outline(path: str) -> List[Point]:
    """解析 Markdown 大纲（learning-path 标准优先）：
    - 以 H1/H2/H3/H4 带 (id: xxx) 的结构为准；特别地，H4 (js-sec-*) 为知识点。
    - 保留一个兼容模式：若未命中 learning-path 模式，则尝试解析列表项作为知识点。
    - 忽略代码块内容。
    """

    points: List[Point] = []
    in_code_block = False
    next_id = 1

    h1_title = ""
    chapter_title = ""
    group_title = ""

    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"[错误] 找不到文件: {path}", file=sys.stderr)
        return []

    # 第一遍：优先尝试 learning-path 的 Hx + (id: ...) 格式
    for idx, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")

        if CODE_FENCE_RE.match(line):
            in_code_block = not in_code_block
            continue
        if in_code_block or not line.strip():
            continue

        if (m := H1_WITH_ID.match(line)):
            h1_title = m.group("title").strip()
            continue
        if (m := H2_CHAPTER.match(line)):
            chapter_title = m.group("title").strip()
            continue
        if (m := H3_GROUP.match(line)):
            group_title = m.group("title").strip()
            continue
        if (m := H4_SECTION.match(line)):
            title = m.group("title").strip()
            sec_id = m.group("id").strip()
            path_parts = [p for p in [h1_title, chapter_title, group_title, title] if p]
            points.append(Point(id=next_id, text=title, path=path_parts, line_no=idx, source_id=sec_id))
            next_id += 1

    if points:
        return points

    # 兜底：老式列表项解析（如果没有 learning-path 风格的 H4）
    headings_stack: List[str] = []
    bullets_stack: List[str] = []
    in_code_block = False
    next_id = 1

    def set_heading(level: int, title: str) -> None:
        while len(headings_stack) >= level:
            headings_stack.pop()
        headings_stack.append(title.strip())

    for idx, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")

        if CODE_FENCE_RE.match(line):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        m = HEADING_RE.match(line)
        if m:
            level = len(m.group("hashes"))
            title = m.group("text").strip()
            set_heading(level, title)
            bullets_stack.clear()
            continue

        m = LIST_RE.match(line)
        if m:
            indent = m.group("indent")
            text = m.group("text").strip()
            depth = max(0, len(indent) // 2)
            while len(bullets_stack) > depth:
                bullets_stack.pop()
            bullets_stack.append(text)
            path_parts = [*headings_stack, *bullets_stack]
            points.append(Point(id=next_id, text=text, path=path_parts.copy(), line_no=idx, source_id=None))
            next_id += 1

    return points


# -----------------------------
# 读取配置并选择 LLM
# -----------------------------


def load_config(path: str) -> Dict[str, Any]:
    """读取根目录 config.json（或其他路径）并返回字典。"""
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
    temperature: Optional[float] = 0.3


def choose_llm(cfg: Dict[str, Any], llm_key: Optional[str]) -> LLMConfig:
    """从 config.json 中选择一个 llm 配置。
    优先顺序：命令行 --llm > cfg['node_llm'].get('select_prompt_template') > cfg['node_llm'].get('default')。
    """
    llms = cfg.get("llms") or {}
    if not llms:
        raise RuntimeError("配置中缺少 'llms'。")

    # 从 node_llm 读取默认
    if not llm_key:
        node_llm = cfg.get("node_llm") or {}
        llm_key = node_llm.get("select_prompt_template") or node_llm.get("default")
    if not llm_key:
        # 再退回任意一个 llm 条目
        llm_key = next(iter(llms.keys()))

    entry = llms.get(llm_key)
    if not entry:
        raise RuntimeError(f"在 config.json 中找不到 llm: {llm_key}")

    provider = entry.get("provider") or "openai"
    model = entry.get("model") or llm_key
    api_key = entry.get("api_key") or os.environ.get("OPENAI_API_KEY")
    base_url = entry.get("base_url")
    temperature = entry.get("temperature", 0.3)
    return LLMConfig(key=llm_key, provider=provider, model=model, api_key=api_key, base_url=base_url, temperature=temperature)


# -----------------------------
# 调用不同 Provider 的 LLM
# -----------------------------


class LLMCaller:
    """包装不同 Provider 的调用。"""

    def __init__(self, conf: LLMConfig):
        self.conf = conf
        self._client = None
        self._init()

    def _init(self) -> None:
        # 根据 provider 初始化客户端
        if self.conf.provider in ("deepseek", "openai"):
            try:
                from openai import OpenAI
            except Exception:
                raise SystemExit("缺少 openai 库，请先安装：pip install openai")
            if not self.conf.api_key:
                raise SystemExit("未配置 API Key。请在 config.json 或环境变量中提供。")
            # OpenAI 兼容：DeepSeek 需要 base_url
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

    def classify(self, prompt: str, max_tokens: int = 1024) -> str:
        """发送 prompt 并返回模型的原始字符串回复。"""
        if self.conf.provider in ("deepseek", "openai"):
            # 使用 Chat Completions（OpenAI 兼容）
            resp = self._client.chat.completions.create(
                model=self.conf.model,
                messages=[
                    {"role": "system", "content": "你是一个只输出 JSON 的分类助手。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.conf.temperature or 0.3,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content or ""
        elif self.conf.provider == "gemini":
            # 使用 Google Generative AI
            model = self._client.GenerativeModel(self.conf.model)
            resp = model.generate_content(prompt)
            return getattr(resp, "text", "") or ""
        else:
            raise RuntimeError("未知 provider")


# -----------------------------
# 构造 LLM 提示词（只让模型给 JSON）
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


def build_prompt(point_text: str, context_path: List[str]) -> str:
    """构造分类指令：
    - 给出“知识点文本”和“父级上下文路径”
    - 让大模型在 9 个原型中二选一并设置开关
    - 强制要求只输出 JSON（不包含任何解释文字）
    """

    context = " / ".join(context_path[:-1]) if len(context_path) > 1 else ""
    archetype_list = ", ".join(ARCHETYPES)

    return f"""
请作为“知识点模板路由器”，仅根据给定信息为知识点选择一个最合适的“原型（archetype）”并设置“开关（switches）”。

【任务约束】
- 只能在以下 9 个原型中选择一个（必须二选一）：
  {archetype_list}
- 输出必须是标准 JSON，不得包含多余文本、注释或 Markdown。
- JSON 键一律使用小写下划线风格。

【开关注意】
- 可用开关（按需出现）：include_code, code_lang, include_math, math_depth, include_comparison_table, include_steps_checklist, include_case_snippets, include_eval_metrics, include_references, audience_level, tone_style
- audience_level 可取：beginner / intermediate / expert；若无法判断可省略。
- code_lang 可取：python / javascript / typescript / java / cpp / go / rust 等；若无法判断可省略。

【知识点信息】
- point_text: {point_text}
- parent_context: {context}

【输出 JSON 模板】
{{
  "archetype": "<从 9 个原型中选择一个>",
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
    "audience_level": "<beginner|intermediate|expert 可省略>",
    "tone_style": "<expository|code-guide|proof|quickstart|tutorial|analysis|narrative|design|diagnostic 可省略>"
  }},
  "confidence": <0.0-1.0 的小数>,
  "rationale": "<一句话说明理由，可适当简短>"
}}

严格只输出 JSON。
"""


# -----------------------------
# 解析大模型回复为 JSON
# -----------------------------


def extract_json(s: str) -> Optional[Dict[str, Any]]:
    """从模型回复中提取 JSON：
    - 优先直接解析
    - 尝试从 ```json/``` 包裹中提取
    - 退而求其次，寻找第一个 { 开始到最后一个 } 结束的片段
    """
    s = (s or "").strip()
    if not s:
        return None
    # 1) 直接解析
    try:
        return json.loads(s)
    except Exception:
        pass
    # 2) ```json ... ```
    m = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", s, re.IGNORECASE)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    # 3) 第一个{ 到 最后一个}
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
# 主流程
# -----------------------------


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="使用 LLM 对大纲知识点进行原型 + 开关判别（无本地规则）")
    parser.add_argument("input", help="大纲 Markdown 文件路径")
    parser.add_argument("--config", default="config.json", help="配置文件路径（默认读取根目录 config.json）")
    parser.add_argument("--llm", help="使用的 llm key（覆盖 config.json 中 node_llm.select_prompt_template）")
    parser.add_argument("--output", "-o", help="输出 JSONL 文件（若未指定则保存到 output/<输入文件名>.archetype_llm.jsonl）")
    parser.add_argument("--out-dir", default="output", help="未指定 --output 时的默认输出目录（默认：output）")
    parser.add_argument("--resume", action="store_true", help="若目标 JSONL 已存在，则读取其中已处理的项并跳过，仅追加新结果")
    parser.add_argument("--fsync", action="store_true", help="每行写入后执行 fsync()，进一步保证中断情况下的数据落盘")
    parser.add_argument("--pretty", action="store_true", help="在 stderr 打印精简预览表")
    parser.add_argument("--max-tokens", type=int, default=768, help="每次调用的最大 tokens")

    args = parser.parse_args(argv)

    try:
        cfg = load_config(args.config)
        llm_cfg = choose_llm(cfg, args.llm)
    except Exception as e:
        print(f"[错误] 读取/选择大模型失败：{e}", file=sys.stderr)
        return 2

    points = parse_markdown_outline(args.input)
    if not points:
        print("[警告] 未解析到任何知识点。", file=sys.stderr)
        return 1

    try:
        caller = LLMCaller(llm_cfg)
    except SystemExit as e:
        print(str(e), file=sys.stderr)
        return 2
    except Exception as e:
        print(f"[错误] 初始化 LLM 客户端失败：{e}", file=sys.stderr)
        return 2

    # 解析输出路径：优先 --output；否则 output/<input_basename>.archetype_llm.jsonl
    out_path: Optional[Path] = None
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        base = Path(args.input).stem
        out_path = out_dir / f"{base}.archetype_llm.jsonl"

    # 读取已存在的 JSONL（在 --resume 模式下）
    processed_keys = set()
    if args.resume and out_path.exists():
        try:
            with open(out_path, "r", encoding="utf-8") as rh:
                for line in rh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                        key = rec.get("source_id") or f"{'/'.join(rec.get('path') or [])}::{rec.get('text')}"
                        if key:
                            processed_keys.add(key)
                    except Exception:
                        continue
        except Exception as e:
            print(f"[警告] 读取已存在 JSONL 失败，忽略 --resume：{e}", file=sys.stderr)
            processed_keys.clear()

    # 以追加或覆盖方式打开输出文件
    mode = "a" if (args.resume and out_path.exists()) else "w"
    out_fh = open(out_path, mode, encoding="utf-8")
    preview: List[Tuple[int, str, str, float]] = []

    # 根据 config.json 控制并行度
    max_parallel = int(cfg.get("max_parallel_requests", 5))
    if max_parallel <= 0:
        max_parallel = 1

    # 准备待处理列表（考虑 --resume）
    todo_points: List[Point] = []
    for p in points:
        key = p.source_id or f"{'/'.join(p.path)}::{p.text}"
        if processed_keys and key in processed_keys:
            continue
        todo_points.append(p)

    if not todo_points:
        print("[提示] 没有需要处理的知识点（可能已全部处理，或 --resume 生效）。", file=sys.stderr)
    else:
        print(f"[信息] 待处理 {len(todo_points)} 条，max_parallel={max_parallel}", file=sys.stderr)

    def worker(p: Point) -> Dict[str, Any]:
        prompt = build_prompt(p.text, p.path)
        try:
            raw = caller.classify(prompt, max_tokens=args.max_tokens)
        except Exception:
            raw = ""
        data = extract_json(raw) or {
            "archetype": "concept_exposition",
            "switches": {},
            "confidence": 0.0,
            "rationale": "llm_failed_or_invalid_json",
        }
        return {
            "id": p.id,
            "text": p.text,
            "path": p.path,
            "source_id": p.source_id,
            "archetype": data.get("archetype"),
            "switches": data.get("switches", {}),
            "confidence": data.get("confidence", 0.0),
            "rationale": data.get("rationale", ""),
            "llm": llm_cfg.key,
        }

    if todo_points:
        with cf.ThreadPoolExecutor(max_workers=max_parallel) as ex:
            future_map = {ex.submit(worker, p): p for p in todo_points}
            for fut in cf.as_completed(future_map):
                p = future_map[fut]
                try:
                    record = fut.result()
                except Exception as e:
                    record = {
                        "id": p.id,
                        "text": p.text,
                        "path": p.path,
                        "source_id": p.source_id,
                        "archetype": "concept_exposition",
                        "switches": {},
                        "confidence": 0.0,
                        "rationale": f"worker_exception:{e}",
                        "llm": llm_cfg.key,
                    }

                out_fh.write(json.dumps(record, ensure_ascii=False) + "\n")
                out_fh.flush()
                if args.fsync:
                    try:
                        os.fsync(out_fh.fileno())
                    except Exception:
                        pass

                if args.pretty:
                    try:
                        conf = float(record["confidence"]) if record.get("confidence") is not None else 0.0
                    except Exception:
                        conf = 0.0
                    preview.append((record["id"], record["text"], str(record.get("archetype")), conf))

    if out_fh:
        out_fh.close()

    if args.pretty:
        print("\n预览（id | archetype | conf | text）:", file=sys.stderr)
        for rid, text, arch, conf in preview[:60]:
            print(f"{rid:>4} | {arch:<20} | {conf:>4} | {text}", file=sys.stderr)
        print(f"\n已保存 JSONL：{out_path}", file=sys.stderr)
    else:
        print(f"已保存 JSONL：{out_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
