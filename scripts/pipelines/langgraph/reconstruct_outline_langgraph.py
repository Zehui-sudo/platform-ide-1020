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
    """严格从 prompt_catalog.md 加载，失败则抛出异常。"""
    try:
        # 确保 prompts 包可被导入
        _project_root = Path(__file__).resolve().parents[3]
        if str(_project_root) not in sys.path:
            sys.path.insert(0, str(_project_root))
        from prompts.prompt_loader import get_prompt
        return get_prompt(key)
    except (ImportError, KeyError, FileNotFoundError) as e:
        raise RuntimeError(
            f"无法从 prompt_catalog.md 加载 '{key}'。请确保 prompts/prompt_loader.py 和 prompts/prompt_catalog.md 文件存在且配置正确。"
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
        resp = llm.complete(prompt, max_tokens=10)
    except Exception as e:
        return f"error: classify failed: {e}"
    ans = (resp or "").strip().strip('`\"\'').lower()
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
    registry = build_llm_registry(cfg)
    caller = pick_llm(cfg, registry, args.llm_key)

    # 分类模型（优先 node_llm.classify_subject，再退回 CLI，再退回 default）
    node_llm = cfg.get("node_llm") or {}
    prefer_cls_key = None
    if isinstance(node_llm, dict):
        val = node_llm.get("classify_subject")
        if isinstance(val, str):
            prefer_cls_key = val
    if args.classifier_llm_key:
        prefer_cls_key = args.classifier_llm_key
    classifier = pick_llm(cfg, registry, prefer_cls_key)

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
