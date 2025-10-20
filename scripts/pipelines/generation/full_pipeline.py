#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Full pipeline orchestrator

串联两段现有流程（仅引用函数，不复制实现）：
- 大纲阶段：scripts/integrated_textbook_pipeline_langgraph.py
- 章节生成阶段：scripts/generate_chapters_from_integrated_standalone.py

作用：
- 给定主题（subject），先运行“教材推荐→目录检索→大纲重构”；
- 接着将重构后大纲传入独立的章节级生成脚本，按章节生成内容、审查和（可选）自动修复，最后发布到 web-learner/public/content/<topic_slug>/ 下。

注意：
- 该脚本只做流程串联，核心逻辑与配置完全复用上述两个脚本中的函数与约定；
- 默认读取项目根目录的 config.json；
- 如需更详细的 LLM 调试信息（模型与所有 Prompt），可开启 --debug（作用于章节生成阶段）。

用法示例：
  python scripts/pipelines/generation/full_pipeline.py \
    --subject "tailwind css" \
    --top-n 3 \
    --debug

"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from datetime import datetime
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# 基础路径
def _find_repo_root() -> Path:
    p = Path(__file__).resolve()
    for parent in [p] + list(p.parents):
        if (parent / "config.json").exists():
            return parent
    return Path(__file__).resolve().parents[-1]

BASE_DIR = _find_repo_root()


# 确保可以以包形式导入 scripts/* 模块与根目录模块
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# -------- 阶段一：大纲生成（导入可调用函数） --------
from scripts.pipelines.langgraph.integrated_textbook_pipeline_langgraph import (
    build_graph as _build_outline_graph,
    _load_config as _load_cfg_outline,
    load_gemini_config as _load_gemini,
    load_kimi_config as _load_kimi,
    choose_llm as _choose_llm,
)


# -------- 阶段二：章节生成（导入可调用函数） --------
from scripts.pipelines.generation.generate_chapters_from_integrated_standalone import (
    load_config as _load_cfg_gen,
    ensure_dir as _ensure_dir,
    slugify as _slugify,
    _convert_reconstructed_to_outline_struct as _to_outline_struct,
    _points_from_struct as _points_from_struct,
    _parse_selected as _parse_selected,
    init_llm as _init_llm,
    build_llm_registry as _build_llm_registry,
    select_llm_for_node as _select_llm_for_node,
    generate_and_review_by_chapter_node as _gen_and_review_by_chapter,
    propose_and_apply_fixes_node as _propose_and_apply_fixes,
    save_and_publish_node as _save_and_publish,
    gather_and_report_node as _gather_and_report,
)


def _run_outline_stage(
    *,
    subject: str,
    top_n: int,
    max_parallel: int,
    gemini_llm_key: Optional[str],
    kimi_llm_key: Optional[str],
    reconstruct_llm_key: Optional[str],
    max_tokens: Optional[int],
) -> Dict[str, Any]:
    """运行教材推荐→目录检索→大纲重构，返回包含 reconstructed_outline 的对象。"""
    logger = logging.getLogger(__name__)
    cfg = _load_cfg_outline()
    gem_cfg = _load_gemini(cfg, gemini_llm_key)
    kimi_cfg = _load_kimi(cfg, kimi_llm_key)
    reconstruct_llm = _choose_llm(cfg, reconstruct_llm_key)

    logger.info(
        "[Outline] subject=%s | top_n=%d | parallel=%d | Gemini=%s | Kimi=%s | ReconstructLLM=%s",
        subject, top_n, max_parallel, gem_cfg.model, kimi_cfg.model, reconstruct_llm.model,
    )

    app = _build_outline_graph()
    init_state = {
        "subject": subject,
        "top_n": max(1, int(top_n)),
        "max_parallel": max(1, int(max_parallel)),
        "max_tokens": max_tokens,
        "gemini": gem_cfg,
        "kimi": kimi_cfg,
        "reconstruct_llm": reconstruct_llm,
    }
    final_state = app.invoke(init_state)

    out = {
        "subject": subject,
        "top_n": init_state["top_n"],
        "recommendations": final_state.get("recommendations", []),
        "tocs": final_state.get("tocs", []),
        "reconstructed_outline": final_state.get("reconstructed_outline"),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    if not out.get("reconstructed_outline"):
        raise RuntimeError("大纲重构失败：未得到 reconstructed_outline")
    return out


def _render_outline_md(outline_struct: Dict[str, Any], fallback_subject: str) -> str:
    """渲染简要大纲 Markdown（与章节脚本保持一致的轻量渲染逻辑）。"""
    try:
        import re as _re
        lines: List[str] = []
        topic = outline_struct.get("meta", {}).get("topic", fallback_subject)
        topic_slug = outline_struct.get("meta", {}).get("topic_slug", _slugify(topic))
        lines.append(f"# {topic} (id: {topic_slug})")
        chs = outline_struct.get("chapters") or []
        for ci, ch in enumerate(chs, start=1):
            lines.append("")
            lines.append(f"## 第{ci}章：{ch.get('title','')} (id: {ch.get('id')})")
            for gi, gr in enumerate(ch.get("groups") or [], start=1):
                lines.append(f"### {ci}.{gi} {gr.get('title','')} (id: {gr.get('id')})")
                for si, sec in enumerate((gr.get("sections") or []), start=1):
                    st = sec.get('title','')
                    try:
                        s_clean = _re.sub(r"^\s*\d+(?:\.\d+)*\s+", "", st)
                    except Exception:
                        s_clean = st
                    lines.append(f"#### {ci}.{gi}.{si} {s_clean} (id: {sec.get('id')})")
        return "\n".join(lines) + "\n"
    except Exception:
        return ""


def _run_generation_stage(
    *,
    integrated_obj: Dict[str, Any],
    config_path: str,
    selected_chapters: Optional[str],
    max_parallel: Optional[int],
    skip_content_review: bool,
    skip_fixes: bool,
    auto_apply_mode: Optional[str],
    auto_apply_threshold_major: Optional[float],
    no_sanitize_mermaid: bool,
    output_subdir: Optional[str],
    debug: bool,
) -> Dict[str, Any]:
    """运行章节生成/审查/修复/发布阶段，返回最终状态（含报告）。"""
    logger = logging.getLogger(__name__)

    reconstructed = integrated_obj.get("reconstructed_outline") or {}
    if not reconstructed:
        raise RuntimeError("缺少 reconstructed_outline，无法进入生成阶段")
    subject = integrated_obj.get("subject") or reconstructed.get("title") or "主题"

    # 配置
    cfg = _load_cfg_gen(config_path)
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        cfg["debug"] = True
    if max_parallel:
        cfg["max_parallel_requests"] = int(max_parallel)
    if skip_content_review:
        cfg["skip_content_review"] = True
    if skip_fixes:
        cfg["skip_fixes"] = True
    if auto_apply_mode is not None:
        cfg["auto_apply_mode"] = auto_apply_mode
    if auto_apply_threshold_major is not None:
        cfg["auto_apply_threshold_major"] = float(auto_apply_threshold_major)
    if no_sanitize_mermaid:
        cfg["sanitize_mermaid"] = False

    # 大纲结构与点集
    outline_struct = _to_outline_struct(subject, reconstructed)
    points = _points_from_struct(outline_struct)

    topic_slug = outline_struct.get("meta", {}).get("topic_slug") or _slugify(subject)
    subdir = output_subdir or topic_slug

    # Debug 文件输出（与章节脚本一致）
    if debug:
        try:
            dbg_dir = BASE_DIR / "output" / subdir
            _ensure_dir(dbg_dir)
            dbg_path = dbg_dir / "log.txt"
            fh = logging.FileHandler(dbg_path, encoding="utf-8")
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            logging.getLogger().addHandler(fh)
            logger.debug(f"调试日志文件: {dbg_path}")
        except Exception as e:
            logger.warning(f"创建调试日志文件失败: {e}")

    # 渲染概要大纲（供修复提示参考）
    outline_md = _render_outline_md(outline_struct, subject)

    # 章节选择
    chapters = outline_struct.get("chapters") or []
    total = len(chapters)
    indices = _parse_selected(selected_chapters, total)
    selected_titles = [chapters[i - 1].get("title", "") for i in indices]
    logger.info(f"[Generate] 选择章节: {indices} -> {[t or '未命名' for t in selected_titles]}")

    # 初始状态
    state: Dict[str, Any] = {
        "topic": subject,
        "topic_meta": {"lang": "zh"},
        "topic_slug": topic_slug,
        "config": cfg,
        "output_subdir": subdir,
        "outline_struct": outline_struct,
        "outline_final_md": outline_md,
        "points": points,
        "selected_chapters": selected_titles,
    }

    # 构建 LLM 实例（生成、审查、修复）
    default_llm = _init_llm(cfg)
    registry = _build_llm_registry(cfg)

    def _pick(node: str, subrole: Optional[str] = None):
        return _select_llm_for_node(cfg, registry, node, subrole) or default_llm

    gen_llm = _pick("generate_and_review_by_chapter", "generate")
    rev_llm = _pick("generate_and_review_by_chapter", "review")
    prop_llm = _pick("propose_and_apply_fixes", "propose")

    # 运行阶段：生成+审查 → 修复 → 保存与发布 → 汇总
    s1 = asyncio.run(_gen_and_review_by_chapter(state, gen_llm, rev_llm))
    s2 = asyncio.run(_propose_and_apply_fixes(s1, prop_llm)) if not cfg.get("skip_fixes", False) else s1
    s3 = _save_and_publish(s2)
    s4 = _gather_and_report(s3)
    return s4


def main() -> int:
    ap = argparse.ArgumentParser(description="Run full pipeline: outline → chapter generation")
    # 阶段一（大纲）
    ap.add_argument("--subject", required=True, help="主题，例如：计算机网络、微观经济学")
    ap.add_argument("--top-n", type=int, default=3, help="获取目录的教材数量（默认 3）")
    ap.add_argument("--max-parallel", type=int, default=5, help="Kimi 并行查询上限（默认 5）")
    ap.add_argument("--gemini-llm-key", type=str, default=None, help="config.json.llms 中 Gemini 的 key，如 gemini-2.5-pro")
    ap.add_argument("--kimi-llm-key", type=str, default=None, help="config.json.llms 中 Kimi 的 key，如 kimi-k2")
    ap.add_argument("--reconstruct-llm-key", type=str, default=None, help="config.json.llms 中重构阶段使用的 LLM key")
    ap.add_argument("--max-tokens", type=int, default=None, help="重构阶段最大 tokens，默认无限制")
    ap.add_argument("--save-intermediate", action="store_true", help="保存大纲阶段的中间 JSON（可选）")

    # 阶段二（章节生成）
    ap.add_argument("--config", default=str(BASE_DIR / "config.json"), help="配置文件路径（默认 config.json）")
    ap.add_argument("--selected-chapters", default=None, help="选择的章节编号（如 1,3-4；留空为全部）")
    ap.add_argument("--gen-max-parallel", type=int, default=None, help="章节生成并行上限（覆盖配置）")
    ap.add_argument("--skip-content-review", action="store_true", help="跳过知识点审查（更快）")
    ap.add_argument("--skip-fixes", action="store_true", help="跳过修复提案与自动应用")
    ap.add_argument("--auto-apply-mode", type=str, choices=["off", "safe", "aggressive", "all"], default=None, help="自动应用模式")
    ap.add_argument("--auto-apply-threshold-major", type=float, default=None, help="aggressive 模式下 major 的最低信心阈值（默认 0.8）")
    ap.add_argument("--no-sanitize-mermaid", action="store_true", help="禁用 Mermaid 语法规范化修复（默认开启）")
    ap.add_argument("--output-subdir", type=str, default=None, help="输出子目录（默认 topic slug）")
    ap.add_argument("--debug", action="store_true", help="调试模式：输出更详细日志并记录所有 Prompt（章节生成阶段）")

    args = ap.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )
    logger = logging.getLogger(__name__)

    # 阶段一：大纲生成
    integrated_obj = _run_outline_stage(
        subject=args.subject,
        top_n=args.top_n,
        max_parallel=args.max_parallel,
        gemini_llm_key=args.gemini_llm_key,
        kimi_llm_key=args.kimi_llm_key,
        reconstruct_llm_key=args.reconstruct_llm_key,
        max_tokens=args.max_tokens,
    )

    # 可选：保存中间产物
    if args.save_intermediate:
        out_dir = BASE_DIR / "output" / "integrated_pipeline"
        _ensure_dir(out_dir)
        slug = _slugify(args.subject)
        out_path = out_dir / f"{slug}-integrated-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        out_path.write_text(json.dumps(integrated_obj, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("[Outline] 中间结果已保存: %s", out_path)

    # 阶段二：章节生成
    final_state = _run_generation_stage(
        integrated_obj=integrated_obj,
        config_path=args.config,
        selected_chapters=args.selected_chapters,
        max_parallel=args.gen_max_parallel,
        skip_content_review=args.skip_content_review,
        skip_fixes=args.skip_fixes,
        auto_apply_mode=args.auto_apply_mode,
        auto_apply_threshold_major=args.auto_apply_threshold_major,
        no_sanitize_mermaid=args.no_sanitize_mermaid,
        output_subdir=args.output_subdir,
        debug=args.debug,
    )

    report_md = final_state.get("report_md", "")
    if report_md:
        print("\n✅ 流水线完成。报告如下：\n")
        print(report_md)
    else:
        print("\n✅ 流水线完成。无报告可显示。\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
