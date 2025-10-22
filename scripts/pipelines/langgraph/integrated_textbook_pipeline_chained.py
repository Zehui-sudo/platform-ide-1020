#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
串联模式的完整流水线：教材推荐/目录检索（TOC） → 大纲重构（按 theory/tool 分流）

设计要点
- 不新增新的 LangGraph 节点，直接复用并串联两个现有脚本：
  1) scripts/pipelines/langgraph/textbook_toc_pipeline_langgraph.py
  2) scripts/pipelines/langgraph/reconstruct_outline_langgraph.py
- 输出结构与 integrated_textbook_pipeline_langgraph.py 基本一致：
  {
    "subject", "top_n", "recommendations", "tocs", "reconstructed_outline", "timestamp"
  }
- 重构阶段沿用“精准区分 tool/theory + 不同生成方式 + 输出 meta.subject/subject_type”。

运行示例
  python3 scripts/pipelines/langgraph/integrated_textbook_pipeline_chained.py \
    --subject "Web媒体加密" \
    --top-n 3 \
    --print-prompt \
    --stream \
    --gemini-llm-key gemini-2.5-pro-zhongzhuan \
    --kimi-llm-key kimi-k2 \
    --reconstruct-llm-key gemini-2.5-pro-zhongzhuan \
    --classifier-llm-key deepseek-chat \
    --learning-style principles \
    --expected-content "主流流媒体平台视频分发的加密方式，如何防止恶意下载" \
    --log
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# -----------------------------
# 基础工具（独立实现，避免对下游脚本私有函数的强耦合）
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


def _slugify(text: str, fallback: str = "subject") -> str:
    import re as _re
    t = (text or "").replace("（", "(").replace("）", ")").replace("—", "-").strip()
    t = _re.sub(r"[^0-9A-Za-z\-_.\s]", "", t)
    t = _re.sub(r"\s+", "-", t)
    t = t.strip("-_.").lower()
    return t or fallback


def _import_module_from_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"无法从路径加载模块: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


class _Tee:
    """简单的终端输出 Tee：同时写入原有流与日志文件。

    用于将所有 print/logging 输出镜像到 output 下的 .log 文件。
    """

    def __init__(self, *streams):
        self._streams = [s for s in streams if s is not None]

    def write(self, data: str) -> int:  # type: ignore[override]
        total = 0
        for s in self._streams:
            try:
                cnt = s.write(data)
                total = max(total, cnt if isinstance(cnt, int) else len(data))
            except Exception:
                # 忽略写入异常，避免影响主流程
                pass
        self.flush()
        return total or len(data)

    def flush(self) -> None:  # type: ignore[override]
        for s in self._streams:
            try:
                s.flush()
            except Exception:
                pass

    def isatty(self) -> bool:  # 兼容性
        try:
            return bool(getattr(self._streams[0], "isatty", lambda: False)())
        except Exception:
            return False


# -----------------------------
# 阶段一：复用 TOC 流水线（LangGraph）
# -----------------------------

def run_toc_pipeline(
    subject: str,
    top_n: int,
    max_parallel: int,
    cfg: Dict[str, Any],
    gemini_llm_key: Optional[str],
    kimi_llm_key: Optional[str],
    expected_content: Optional[str] = None,
    print_prompt: bool = False,
) -> Dict[str, Any]:
    """调用 textbook_toc_pipeline_langgraph 的图，返回 {subject, subject_slug, recommendations, tocs}。"""
    toc_path = (
        Path(__file__).resolve().parent / "textbook_toc_pipeline_langgraph.py"
    )
    toc_mod = _import_module_from_path("_toc_pipeline", toc_path)

    # 读取 LLM 配置（直接复用该脚本的加载逻辑与 dataclass）
    gem_cfg = toc_mod.load_gemini_config(cfg, gemini_llm_key)
    kimi_cfg = toc_mod.load_kimi_config(cfg, kimi_llm_key)

    app = toc_mod.build_graph()
    init_state = {
        "subject": subject,
        "top_n": max(1, int(top_n)),
        "max_parallel": max(1, int(max_parallel)),
        "gemini": gem_cfg,
        "kimi": kimi_cfg,
        "expected_content": (expected_content or "").strip(),
        "print_prompt": bool(print_prompt),
    }
    logging.getLogger(__name__).info(
        "[1/2] 运行 TOC 流水线 … subject=%s top_n=%d max_parallel=%d",
        subject,
        top_n,
        max_parallel,
    )
    final_state = app.invoke(init_state)
    return {
        "subject": subject,
        "subject_slug": final_state.get("subject_slug") or _slugify(subject, "subject"),
        "expected_content": init_state.get("expected_content", ""),
        "recommendations": final_state.get("recommendations", []),
        "tocs": final_state.get("tocs", []),
    }


# -----------------------------
# 阶段二：复用重构逻辑（函数式，非新节点）
# -----------------------------

def run_reconstruct(
    subject: str,
    subject_slug: Optional[str],
    tocs: List[Dict[str, Any]],
    cfg: Dict[str, Any],
    reconstruct_llm_key: Optional[str],
    classifier_llm_key: Optional[str],
    force_subject_type: Optional[str],
    learning_style: Optional[str],
    expected_content: Optional[str],
    print_prompt: bool,
    stream: bool,
    max_tokens: Optional[int],
) -> Dict[str, Any]:
    """根据 subject 类型路由不同 Prompt，生成并解析输出，注入 meta。"""
    recon_path = (
        Path(__file__).resolve().parent / "reconstruct_outline_langgraph.py"
    )
    recon_mod = _import_module_from_path("_reconstruct_pipeline", recon_path)

    # 构造可用材料（最多 3 份）
    items: List[Dict[str, Any]] = []
    for t in tocs or []:
        if not isinstance(t, dict) or t.get("error"):
            continue
        items.append({
            "book": t.get("book", {}),
            "toc": t.get("toc", []),
            "source": t.get("source", ""),
        })
        if len(items) >= 3:
            break
    if len(items) < 2:
        raise ValueError(f"有效教材目录不足2份，无法进行重构。当前有效数量：{len(items)}")

    # 选择生成与分类 LLM
    llm_conf = recon_mod.choose_llm(cfg, reconstruct_llm_key)
    default_classifier_key = (
        "gemini-2.5-flash" if (cfg.get("llms") or {}).get("gemini-2.5-flash") else None
    )
    classifier_conf = recon_mod.choose_llm(cfg, classifier_llm_key or default_classifier_key)
    classifier = recon_mod.LLMCaller(classifier_conf)

    # 决定 subject_type
    if force_subject_type:
        subject_type = force_subject_type.strip().lower()
    else:
        subject_type = recon_mod.classify_subject(subject, classifier)
        if subject_type not in ("theory", "tool"):
            raise SystemExit(f"[错误] 主题分类失败: {subject_type}")
    print(f"[信息] 主题分类结果: {subject} → {subject_type}", file=sys.stderr)

    # 组装 Prompt（按类型 + 学习风格路由）
    materials_obj = {"subject": subject, "materials": items}
    try:
        prompt = recon_mod.build_prompt(
            subject,
            materials_obj,
            subject_type,
            learning_style=learning_style,
            expected_content=(expected_content or "").strip() or None,
        )
    except TypeError:
        # 兼容旧版函数签名（未接受新增参数）
        prompt = recon_mod.build_prompt(subject, materials_obj, subject_type)
    if print_prompt:
        print("========== DEBUG: Prompt Begin ==========", file=sys.stderr)
        print(prompt, file=sys.stderr)
        print("=========== DEBUG: Prompt End ===========", file=sys.stderr)

    # 调用 LLM
    caller = recon_mod.LLMCaller(llm_conf)
    if stream:
        print("[信息] 正在以流式方式接收模型输出…", file=sys.stderr)
        buf: List[str] = []
        for piece in caller.stream_complete(
            prompt, max_tokens=max_tokens if (max_tokens and max_tokens > 0) else 8192
        ):
            buf.append(piece)
            print(piece, end="", file=sys.stderr, flush=True)
        print("", file=sys.stderr)
        raw = "".join(buf)
    else:
        raw = caller.complete(
            prompt, max_tokens=max_tokens if (max_tokens and max_tokens > 0) else None
        )

    try:
        output_obj = recon_mod._extract_json(raw)
    except Exception as e:
        raise SystemExit(f"[错误] LLM 输出解析失败: {e}")

    # 注入元数据（包含 subject_slug → topic_slug）
    try:
        if isinstance(output_obj, dict):
            meta = output_obj.get("meta")
            if not isinstance(meta, dict):
                meta = {}
            meta.setdefault("subject", subject)
            meta.setdefault("subject_type", subject_type)
            # 将 slug 传递给下游，便于统一命名
            meta.setdefault("topic_slug", subject_slug or _slugify(subject, "subject"))
            if learning_style:
                meta.setdefault("learning_style", learning_style)
            if expected_content is not None:
                meta.setdefault("expected_content", (expected_content or "").strip())
            output_obj["meta"] = meta
    except Exception:
        pass

    return output_obj


# -----------------------------
# CLI 入口
# -----------------------------

def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="复用+串联：教材 TOC → 大纲重构 的完整流水线")
    p.add_argument("--subject", required=True, help="主题，例如：计算机网络、微观经济学")
    p.add_argument("--top-n", type=int, default=3, help="获取目录的教材数量")
    p.add_argument("--max-parallel", type=int, default=5, help="Kimi 并行查询上限")
    p.add_argument("--gemini-llm-key", type=str, default=None, help="config.json.llms 中 Gemini 的 key，例如 gemini-2.5-pro")
    p.add_argument("--kimi-llm-key", type=str, default=None, help="config.json.llms 中 Kimi 的 key，例如 kimi-k2")
    p.add_argument("--reconstruct-llm-key", type=str, default=None, help="config.json.llms 中重构阶段使用的 LLM key")
    p.add_argument("--classifier-llm-key", type=str, default=None, help="用于主题分类的 LLM 键名（默认 gemini-2.5-flash 如存在）")
    p.add_argument("--subject-type", choices=["theory", "tool"], default=None, help="手工指定主题类型，跳过自动分类")
    p.add_argument("--learning-style", required=True, help="学习风格（必选）：principles | deep_preview | 原理学习 | 深度预习（仅理论类生效）")
    p.add_argument("--expected-content", type=str, default=None, help="学习者期望（可选，追加于输入材料之后）")
    p.add_argument("--max-tokens", type=int, default=32768, help="重构阶段最大 tokens，默认无限制")
    p.add_argument("--print-prompt", action="store_true", help="在终端输出发送给重构 LLM 的完整 Prompt 以便调试")
    p.add_argument("--stream", action="store_true", help="启用流式输出，在控制台实时显示模型响应")
    p.add_argument("--config", default=str(CONFIG_PATH), help="配置文件路径（默认项目根 config.json）")
    p.add_argument("--out", type=str, default=None, help="综合输出 JSON 文件路径，可选")
    p.add_argument("--log", action="store_true", help="将终端输出镜像到 output/integrated_pipeline 下的 .log 文件")
    p.add_argument("--debug", action="store_true", help="等同 --log，并将日志级别提升为 DEBUG")
    args = p.parse_args(argv)

    # 计算时间戳与 slug，用于默认输出文件命名（与日志配对）
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    pre_slug = _slugify(args.subject, "subject")
    # 若开启日志，将终端输出镜像到日志文件
    log_fp = None
    _orig_stdout, _orig_stderr = sys.stdout, sys.stderr
    if args.log or args.debug:
        pre_out_dir = BASE_DIR / "output" / "integrated_pipeline"
        pre_out_dir.mkdir(parents=True, exist_ok=True)
        log_path = pre_out_dir / f"{pre_slug}-integrated-{ts}.log"
        log_fp = open(log_path, "w", encoding="utf-8")
        sys.stdout = _Tee(sys.stdout, log_fp)
        sys.stderr = _Tee(sys.stderr, log_fp)

    # 初始化 logging（其输出写入 stderr；若启用 Tee 即被镜像到文件）
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger(__name__)

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
        raise SystemExit("[错误] --learning-style 必须为 principles/deep_preview 或 对应中文：原理学习/深度预习")

    # 阶段一：TOC
    stage1 = run_toc_pipeline(
        subject=args.subject,
        top_n=max(1, int(args.top_n)),
        max_parallel=max(1, int(args.max_parallel)),
        cfg=cfg,
        gemini_llm_key=args.gemini_llm_key,
        kimi_llm_key=args.kimi_llm_key,
        expected_content=(args.expected_content or "").strip() if hasattr(args, 'expected_content') else None,
        print_prompt=bool(args.print_prompt),
    )

    # 阶段二：重构
    reconstructed = run_reconstruct(
        subject=stage1["subject"],
        subject_slug=stage1.get("subject_slug"),
        tocs=stage1.get("tocs", []) or [],
        cfg=cfg,
        reconstruct_llm_key=args.reconstruct_llm_key,
        classifier_llm_key=args.classifier_llm_key,
        force_subject_type=args.subject_type,
        learning_style=norm_style,
        expected_content=args.expected_content,
        print_prompt=bool(args.print_prompt),
        stream=bool(args.stream),
        max_tokens=args.max_tokens,
    )

    # 汇总 & 输出
    out_obj = {
        "subject": stage1["subject"],
        "subject_slug": stage1.get("subject_slug") or _slugify(args.subject, "subject"),
        "top_n": max(1, int(args.top_n)),
        "expected_content": stage1.get("expected_content", (args.expected_content or "")),
        "recommendations": stage1.get("recommendations", []),
        "tocs": stage1.get("tocs", []),
        "reconstructed_outline": reconstructed,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = BASE_DIR / "output" / "integrated_pipeline"
        out_dir.mkdir(parents=True, exist_ok=True)
        slug = out_obj.get("subject_slug") or _slugify(args.subject, "subject")
        # 复用启动时刻的时间戳，便于与 .log 文件配对
        out_path = out_dir / f"{slug}-integrated-{ts}.json"

    out_path.write_text(json.dumps(out_obj, ensure_ascii=False, indent=2), encoding="utf-8")

    # 摘要
    logger.info("[完成] 输出文件: %s", out_path)
    recs = out_obj.get("recommendations", []) or []
    logger.info("推荐教材: %d 本 (展示前 %d 本)", len(recs), min(3, len(recs)))
    for i, b in enumerate(recs[:3], 1):
        logger.info("  %d. %s", i, b.get('title', '(no title)'))
    tocs = out_obj.get("tocs", []) or []
    ok = sum(1 for t in tocs if not t.get("error"))
    logger.info("目录获取成功: %d/%d", ok, len(tocs))
    if out_obj.get("reconstructed_outline"):
        logger.info("大纲重构: 成功")
    else:
        logger.warning("大纲重构: 失败")

    # 收尾：还原终端并关闭日志文件（仅在启用日志时）
    if log_fp is not None:
        try:
            sys.stdout.flush(); sys.stderr.flush()
        except Exception:
            pass
        try:
            sys.stdout = _orig_stdout
            sys.stderr = _orig_stderr
        except Exception:
            pass
        try:
            log_fp.flush(); log_fp.close()
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
