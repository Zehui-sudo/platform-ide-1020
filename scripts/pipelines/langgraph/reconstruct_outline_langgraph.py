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
import logging
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from scripts.common.llm import build_llm_registry, pick_llm
from scripts.common.utils import repo_root as _repo_root, load_config as _load_config, slugify as _slugify, extract_json_object as _extract_json

# -----------------------------
# 常量与工具
# -----------------------------

BASE_DIR = _repo_root()
CONFIG_PATH = BASE_DIR / "config.json"

    


# -----------------------------
# Prompt 模板
# -----------------------------






# 新增：理论类（原理学习 principles）风格的完整 Prompt（与 deep_preview 平行，保持相同输出协议）


# 专用于“工具类（Tool）”主题的大纲生成 Prompt



def _prompt_from_catalog(key: str) -> str:
    """严格从 prompt_catalog_data.py 加载，失败则抛出异常。"""
    try:
        # 确保 prompts 包可被导入
        _project_root = Path(__file__).resolve().parents[3]
        if str(_project_root) not in sys.path:
            sys.path.insert(0, str(_project_root))
        from prompts.prompt_loader import get_prompt
        return get_prompt(key)
    except (ImportError, KeyError, FileNotFoundError) as e:
        raise RuntimeError(
            f"无法加载 Prompt '{key}'。请确认 prompts/prompt_loader.py 和 prompts/prompt_catalog_data.py 配置正确并可被导入。"
        ) from e


def build_prompt(
    subject: str,
    materials: Dict[str, Any],
    subject_type: str,
    learning_style: Optional[str] = None,
    expected_content: Optional[str] = None,
) -> str:
    subject_type = (subject_type or "theory").strip().lower()
    mat_obj = {"tocs": materials.get("materials") or []}
    mat_json = json.dumps(mat_obj, ensure_ascii=False, indent=2)

    expect_clean = (expected_content or "").strip()
    expect_placeholder = "学习者期望（可选）"
    expect_injection = f"\n\n【学习者期望】\n{expect_clean}\n" if expect_clean else ""

    if subject_type == "tool":
        text = _prompt_from_catalog("reconstruct.tools").strip()
        text = text.replace("[subject]", subject)
        if materials.get("materials"):
            injection = (
                "\n\n【可选参考材料（JSON）】如有以下教材目录可参考：\n"
                f"```json\n{mat_json}\n```\n"
            )
            text += "\n" + injection
    else:
        style = (learning_style or "deep_preview").strip().lower()
        key = f"reconstruct.theories.{style}"
        text = _prompt_from_catalog(key).strip()
        text = text.replace("[subject]", subject)
        placeholder = "输入材料：textbook_toc_pipeline_langgraph.py 搜集的三份世界级教材目录"
        injection = (
            "\n\n【输入材料（JSON）】三本教材目录如下：\n"
            f"```json\n{mat_json}\n```\n"
        )
        if placeholder in text:
            text = text.replace(placeholder, injection)
        else:
            text += "\n" + injection

    if expect_clean:
        if expect_placeholder in text:
            text = text.replace(expect_placeholder, expect_injection)
        else:
            text += "\n" + expect_injection
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


def prepare_materials_from_tocs(subject: str, tocs: List[Dict[str, Any]], limit: int = 3) -> Dict[str, Any]:
    """根据 TOC 列表构造 Prompt 所需的精简材料结构。"""
    return _prepare_materials({"subject": subject, "tocs": tocs}, limit=limit)


# -----------------------------
# 分类：theory / tool
# -----------------------------

@dataclass
class LLMCaller:
    """LLM 调用器的简单包装，以满足类型提示。"""
    complete: Any
    stream_complete: Any

def classify_subject(subject: str, llm: LLMCaller) -> str:
    """调用轻量模型对主题分类。"""
    try:
        tmpl = _prompt_from_catalog("reconstruct.classify_subject")
        prompt = tmpl.replace("[subject]", subject)
        resp = llm.complete(prompt, max_tokens=8096)
    except Exception as e:
        return f"error: classify failed: {e}"
    ans = (resp or "").strip().strip('`\"\'').lower()
    if ans in {"tool", "theory"}:
        return ans
    return f"error: unexpected classifier output: {ans!r}"


@dataclass
class ReconstructOutlineResult:
    outline: Dict[str, Any]
    subject_type: str
    learning_style: str
    prompt: str
    raw_response: str
    llm_info: Dict[str, Any]


def _normalize_learning_style(style: Optional[str]) -> str:
    val = (style or "").strip().lower()
    mapping = {
        "principles": "principles",
        "原理学习": "principles",
        "deep_preview": "deep_preview",
        "深度预习": "deep_preview",
    }
    normalized = mapping.get(val, mapping.get(style or "", ""))
    if normalized:
        return normalized
    if not style:
        return "principles"
    raise ValueError("学习风格需为 principles/deep_preview 或 对应中文：原理学习/深度预习")


def _describe_llm(llm: Any, key_hint: Optional[str]) -> Dict[str, Any]:
    """提取 LLM 的关键信息，便于日志记录。"""
    info: Dict[str, Any] = {}
    if key_hint:
        info["key"] = key_hint
    cfg = getattr(llm, "_cfg", None)
    if cfg:
        info.setdefault("provider", getattr(cfg, "provider", None))
        info.setdefault("model", getattr(cfg, "model", None))
        info.setdefault("temperature", getattr(cfg, "temperature", None))
        info.setdefault("max_tokens", getattr(cfg, "max_tokens", None))
    return {k: v for k, v in info.items() if v is not None}


def run_reconstruct_outline(
    subject: str,
    *,
    materials: Dict[str, Any],
    cfg: Optional[Dict[str, Any]] = None,
    reconstruct_llm_key: Optional[str] = None,
    classifier_llm_key: Optional[str] = None,
    subject_type: Optional[str] = None,
    learning_style: Optional[str] = None,
    expected_content: Optional[str] = None,
    subject_slug: Optional[str] = None,
    print_prompt: bool = False,
    stream: bool = False,
    max_tokens: Optional[int] = None,
    logger: Optional[logging.Logger] = None,
) -> ReconstructOutlineResult:
    """执行大纲重构阶段，返回结构化结果。"""
    cfg = cfg or _load_config(CONFIG_PATH)
    logger = logger or logging.getLogger(__name__)

    node_llm_cfg = cfg.get("node_llm") or {}

    registry = build_llm_registry(cfg)

    target_reconstruct_key = reconstruct_llm_key
    if not target_reconstruct_key:
        val = node_llm_cfg.get("reconstruct_outline")
        if isinstance(val, str):
            target_reconstruct_key = val
    caller = pick_llm(cfg, registry, target_reconstruct_key)

    prefer_cls_key = classifier_llm_key
    if prefer_cls_key is None:
        val = node_llm_cfg.get("classify_subject")
        if isinstance(val, str):
            prefer_cls_key = val
    classifier = pick_llm(cfg, registry, prefer_cls_key)

    norm_style = _normalize_learning_style(learning_style)
    expected_clean = (expected_content or "").strip()

    if subject_type:
        final_subject_type = subject_type.strip().lower()
    else:
        final_subject_type = classify_subject(subject, classifier)
        logger.info("主题分类: %s → %s", subject, final_subject_type)
        if final_subject_type not in ("theory", "tool"):
            raise RuntimeError(f"主题分类失败: {final_subject_type}")
    logger.info("主题分类: %s → %s", subject, final_subject_type)
    print(f"[信息] 主题分类结果: {subject} → {final_subject_type}", file=sys.stderr)

    materials_obj = materials or {"subject": subject, "materials": []}
    usable_materials = []
    for item in materials_obj.get("materials", []) or []:
        if isinstance(item, dict) and not item.get("error"):
            usable_materials.append(item)
    if len(usable_materials) == 0:
        raise ValueError("无有效教材目录，无法进行大纲重构。")

    prompt = build_prompt(
        subject,
        materials_obj,
        final_subject_type,
        learning_style=norm_style,
        expected_content=expected_clean or None,
    )
    if print_prompt:
        print("========== DEBUG: Prompt Begin ==========", file=sys.stderr)
        print(prompt, file=sys.stderr)
        print("=========== DEBUG: Prompt End ===========", file=sys.stderr)

    max_tokens_arg = None if (max_tokens is None or max_tokens <= 0) else max_tokens
    try:
        if stream:
            print("[信息] 正在以流式方式接收模型输出…", file=sys.stderr)
            buf: List[str] = []
            for piece in caller.stream_complete(prompt, max_tokens=max_tokens_arg):
                buf.append(piece)
                print(piece, end="", file=sys.stderr, flush=True)
            print("", file=sys.stderr)
            raw = "".join(buf)
        else:
            raw = caller.complete(prompt, max_tokens=max_tokens_arg)
    except Exception as e:
        raise RuntimeError(f"LLM 调用失败: {type(e).__name__}: {e}") from e

    try:
        info = getattr(caller, "last_info", None) or {}
        if info:
            logger.debug("LLM 完成信息: %s", info)
    except Exception:
        pass

    try:
        output_obj = _extract_json(raw)
    except Exception as e:
        raise RuntimeError(f"解析 LLM 输出失败: {e}") from e

    # 注入 meta 数据
    try:
        if isinstance(output_obj, dict):
            meta = output_obj.get("meta")
            if not isinstance(meta, dict):
                meta = {}
            meta.setdefault("subject", subject)
            meta.setdefault("subject_type", final_subject_type)
            meta.setdefault("learning_style", norm_style)
            if expected_content is not None:
                meta.setdefault("expected_content", expected_clean)
            if subject_slug:
                meta.setdefault("subject_slug", subject_slug)
                meta.setdefault("topic_slug", subject_slug)
            output_obj["meta"] = meta
    except Exception:
        pass

    return ReconstructOutlineResult(
        outline=output_obj,
        subject_type=final_subject_type,
        learning_style=norm_style,
        prompt=prompt,
        raw_response=raw,
        llm_info=_describe_llm(caller, reconstruct_llm_key),
    )


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
    subject = str(input_obj.get("subject") or "")
    materials = _prepare_materials(input_obj, limit=3)

    cfg = _load_config(args.config)
    subject_slug = (input_obj.get("subject_slug") or "").strip() or None
    logger = logging.getLogger(__name__)

    try:
        outcome = run_reconstruct_outline(
            subject=subject,
            materials=materials,
            cfg=cfg,
            reconstruct_llm_key=args.llm_key,
            classifier_llm_key=args.classifier_llm_key,
            subject_type=args.subject_type,
            learning_style=args.learning_style,
            expected_content=args.expected_content,
            subject_slug=subject_slug,
            print_prompt=args.print_prompt,
            stream=args.stream,
            max_tokens=args.max_tokens,
            logger=logger,
        )
    except Exception as e:
        print(f"[错误] {e}", file=sys.stderr)
        return 1

    if args.out:
        out_path = Path(args.out)
    else:
        out_dir = BASE_DIR / "output" / "reconstructed_outline"
        out_dir.mkdir(parents=True, exist_ok=True)
        # 优先使用输入 JSON 的 subject_slug；
        # 若缺失则基于 subject 生成 slug（回退为 'subject' 以避免历史固定前缀）。
        slug = subject_slug or _slugify(subject or "", "subject")
        out_path = out_dir / f"{slug}-reconstructed-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"

    out_path.write_text(json.dumps(outcome.outline, ensure_ascii=False, indent=2), encoding="utf-8")

    # 简要摘要到 stderr
    print(f"[完成] 已生成整合目录: {out_path}", file=sys.stderr)
    llm_info = outcome.llm_info
    llm_desc = llm_info.get("key")
    provider = llm_info.get("provider")
    model = llm_info.get("model")
    if provider and model:
        if llm_desc:
            print(f"使用模型: {llm_desc} ({provider}:{model})", file=sys.stderr)
        else:
            print(f"使用模型: {provider}:{model}", file=sys.stderr)
    elif llm_desc:
        print(f"使用模型: {llm_desc}", file=sys.stderr)
    print(f"输入教材数: {len(materials.get('materials') or [])}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
