#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
综合教材流水线（可选阶段）：
- full        : 推荐教材 + 抓取目录 + 大纲重构（默认）
- toc         : 仅执行教材推荐与目录抓取
- reconstruct : 基于已有目录 JSON 执行大纲重构

示例
- 全流程跑 Python 教材推荐 + 目录抓取 + 大纲重构：
  python3 scripts/pipelines/langgraph/integrated_textbook_pipeline_chained.py \
    --stage full \
    --subject "无监督学习" \
    --top-n 3 \
    --learning-style deep_preview \
    --expected-content "希望知道无监督学习的应用场景，分类方式和常见的无监督学习算法" \
    --print-prompt

  - 只跑教材推荐+目录抓取：
    python3 scripts/pipelines/langgraph/integrated_textbook_pipeline_chained.py \
    --stage toc \
    --subject "命令行操作" \
    --top-n 3 \
    --print-prompt \
    --expected-content "主希望知道命令行操作，包括但不限于SSH、操作系统、文件管理、git管理、docker等" \
    --log

  - 只跑大纲重构：先准备含 tocs 的 JSON，然后执行 
    python3 scripts/pipelines/langgraph/integrated_textbook_pipeline_chained.py \
    --stage reconstruct \
    --input output/textbook_tocs/command-line-operations-20251029-173653.json \
    --expected-content "主希望知道命令行操作，包括但不限于SSH、操作系统、文件管理、git管理、docker等" \
    --learning-style principles \
    --print-prompt \
    --subject-type tool \
    --stream

"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_REPO_ROOT_CANDIDATE = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT_CANDIDATE) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT_CANDIDATE))

from scripts.common.utils import repo_root as _repo_root, load_config as _load_config, slugify as _slugify
from scripts.pipelines.langgraph.textbook_toc_pipeline_langgraph import (
    TextbookTOCResult,
    run_textbook_toc_pipeline,
)
from scripts.pipelines.langgraph.reconstruct_outline_langgraph import (
    ReconstructOutlineResult,
    prepare_materials_from_tocs,
    run_reconstruct_outline,
)

BASE_DIR = _repo_root()
CONFIG_PATH = BASE_DIR / "config.json"


class _Tee:
    """简单的终端输出 Tee：同时写入原有流与日志文件。"""

    def __init__(self, *streams):
        self._streams = [s for s in streams if s is not None]

    def write(self, data: str) -> int:  # type: ignore[override]
        total = 0
        for s in self._streams:
            try:
                cnt = s.write(data)
                total = max(total, cnt if isinstance(cnt, int) else len(data))
            except Exception:
                pass
        self.flush()
        return total or len(data)

    def flush(self) -> None:  # type: ignore[override]
        for s in self._streams:
            try:
                s.flush()
            except Exception:
                pass

    def isatty(self) -> bool:
        try:
            return bool(getattr(self._streams[0], "isatty", lambda: False)())
        except Exception:
            return False


class StepExecutionError(RuntimeError):
    """封装阶段执行失败的异常，用于统一错误处理。"""


def _run_with_retry(
    step_name: str,
    func,
    *,
    max_attempts: int = 1,
    timeout: Optional[float] = None,
    delay: float = 1.0,
    logger: Optional[logging.Logger] = None,
):
    """在重试与超时保护下执行指定步骤。"""
    attempts = max(1, int(max_attempts or 1))
    timeout_value = None if timeout is None or timeout <= 0 else float(timeout)
    wait_seconds = max(0.0, float(delay or 0.0))
    last_exc: Optional[BaseException] = None

    for attempt in range(1, attempts + 1):
        try:
            if logger:
                logger.debug("%s: 开始第 %d/%d 次尝试", step_name, attempt, attempts)
            if timeout_value is not None:
                with cf.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(func)
                    try:
                        return future.result(timeout=timeout_value)
                    except cf.TimeoutError as exc:
                        future.cancel()
                        raise TimeoutError(f"{step_name} 在 {timeout_value:.1f}s 内未完成") from exc
            return func()
        except TimeoutError as exc:
            last_exc = exc
            if logger:
                logger.warning("%s: 第 %d/%d 次尝试超时 (%s)", step_name, attempt, attempts, exc)
            if attempt < attempts and logger:
                logger.info("%s: 将在 %.1fs 后重试（超时）", step_name, wait_seconds)
        except Exception as exc:
            last_exc = exc
            if logger:
                logger.warning(
                    "%s: 第 %d/%d 次尝试失败 (%s: %s)",
                    step_name,
                    attempt,
                    attempts,
                    type(exc).__name__,
                    exc,
                )
            if attempt < attempts and logger:
                logger.info("%s: 将在 %.1fs 后重试", step_name, wait_seconds)
        if attempt < attempts and wait_seconds > 0:
            time.sleep(wait_seconds)

    message = f"{step_name} 在 {attempts} 次尝试后仍未成功"
    raise StepExecutionError(message) from last_exc


def _normalize_timeout(value: Optional[float]) -> Optional[float]:
    """将命令行传入的超时秒数规范化为正浮点数或 None。"""
    if value is None:
        return None
    try:
        ts = float(value)
    except (TypeError, ValueError):
        return None
    return ts if ts > 0 else None


def _format_timeout(value: Optional[float]) -> str:
    """将超时秒数格式化为日志友好的字符串。"""
    if value is None:
        return "不限"
    return f"{value:.1f}s"


def _resolve_json_input(path: Path) -> Path:
    if path.is_dir():
        cands = sorted(path.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        if not cands:
            raise FileNotFoundError("输入目录中未找到 .json 文件")
        return cands[0]
    if not path.exists():
        raise FileNotFoundError(f"未找到输入文件: {path}")
    return path


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"读取/解析 JSON 失败: {exc}") from exc


def execute_toc_stage(
    subject: str,
    *,
    top_n: int,
    max_parallel: int,
    cfg: Dict[str, Any],
    gemini_llm_key: Optional[str],
    kimi_llm_key: Optional[str],
    expected_content: Optional[str],
    print_prompt: bool,
    logger: logging.Logger,
    retry_attempts: int = 1,
    retry_timeout: Optional[float] = None,
    retry_delay: float = 1.0,
) -> TextbookTOCResult:
    step_name = "阶段：教材推荐与目录抓取"

    def _do_run() -> TextbookTOCResult:
        return run_textbook_toc_pipeline(
            subject=subject,
            top_n=top_n,
            max_parallel=max_parallel,
            gemini_llm_key=gemini_llm_key,
            kimi_llm_key=kimi_llm_key,
            expected_content=expected_content,
            print_prompt=print_prompt,
            cfg=cfg,
            logger=logger,
        )

    return _run_with_retry(
        step_name,
        _do_run,
        max_attempts=retry_attempts,
        timeout=retry_timeout,
        delay=retry_delay,
        logger=logger,
    )


def execute_reconstruct_stage(
    subject: str,
    tocs: List[Dict[str, Any]],
    *,
    cfg: Dict[str, Any],
    subject_slug: Optional[str],
    reconstruct_llm_key: Optional[str],
    classifier_llm_key: Optional[str],
    subject_type: Optional[str],
    learning_style: Optional[str],
    expected_content: Optional[str],
    print_prompt: bool,
    stream: bool,
    max_tokens: Optional[int],
    logger: logging.Logger,
    materials: Optional[Dict[str, Any]] = None,
    retry_attempts: int = 1,
    retry_timeout: Optional[float] = None,
    retry_delay: float = 1.0,
) -> ReconstructOutlineResult:
    step_name = "阶段：大纲重构"

    def _do_run() -> ReconstructOutlineResult:
        materials_obj = materials or prepare_materials_from_tocs(subject, tocs)
        return run_reconstruct_outline(
            subject=subject,
            materials=materials_obj,
            cfg=cfg,
            reconstruct_llm_key=reconstruct_llm_key,
            classifier_llm_key=classifier_llm_key,
            subject_type=subject_type,
            learning_style=learning_style,
            expected_content=expected_content,
            subject_slug=subject_slug,
            print_prompt=print_prompt,
            stream=stream,
            max_tokens=max_tokens,
            logger=logger,
        )

    return _run_with_retry(
        step_name,
        _do_run,
        max_attempts=retry_attempts,
        timeout=retry_timeout,
        delay=retry_delay,
        logger=logger,
    )


def run_full_pipeline(
    subject: str,
    *,
    top_n: int,
    max_parallel: int,
    cfg: Dict[str, Any],
    gemini_llm_key: Optional[str],
    kimi_llm_key: Optional[str],
    reconstruct_llm_key: Optional[str],
    classifier_llm_key: Optional[str],
    subject_type: Optional[str],
    learning_style: Optional[str],
    expected_content: Optional[str],
    print_prompt: bool,
    stream: bool,
    max_tokens: Optional[int],
    logger: logging.Logger,
    retry_delay: float = 1.0,
    toc_retry_attempts: int = 1,
    toc_retry_timeout: Optional[float] = None,
    reconstruct_retry_attempts: int = 1,
    reconstruct_retry_timeout: Optional[float] = None,
) -> Tuple[Dict[str, Any], TextbookTOCResult, ReconstructOutlineResult]:
    toc_result = execute_toc_stage(
        subject,
        top_n=top_n,
        max_parallel=max_parallel,
        cfg=cfg,
        gemini_llm_key=gemini_llm_key,
        kimi_llm_key=kimi_llm_key,
        expected_content=expected_content,
        print_prompt=print_prompt,
        logger=logger,
        retry_attempts=toc_retry_attempts,
        retry_timeout=toc_retry_timeout,
        retry_delay=retry_delay,
    )
    recon_result = execute_reconstruct_stage(
        subject,
        toc_result.get("tocs", []) or [],
        cfg=cfg,
        subject_slug=toc_result.get("subject_slug"),
        reconstruct_llm_key=reconstruct_llm_key,
        classifier_llm_key=classifier_llm_key,
        subject_type=subject_type,
        learning_style=learning_style,
        expected_content=expected_content if expected_content is not None else toc_result.get("expected_content"),
        print_prompt=print_prompt,
        stream=stream,
        max_tokens=max_tokens,
        logger=logger,
        retry_attempts=reconstruct_retry_attempts,
        retry_timeout=reconstruct_retry_timeout,
        retry_delay=retry_delay,
    )
    combined = {
        "subject": toc_result["subject"],
        "subject_slug": toc_result["subject_slug"],
        "top_n": toc_result["top_n"],
        "expected_content": toc_result.get("expected_content", expected_content or ""),
        "recommendations": toc_result.get("recommendations", []),
        "tocs": toc_result.get("tocs", []),
        "reconstructed_outline": recon_result.outline,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    return combined, toc_result, recon_result


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="综合教材流水线（可选阶段）")
    parser.add_argument("--stage", choices=["full", "toc", "reconstruct"], default="full", help="选择执行阶段，默认 full")
    parser.add_argument("--subject", help="学习主题（full/toc 阶段必填）")
    parser.add_argument("--top-n", type=int, default=3, help="获取目录的教材数量（full/toc 阶段有效）")
    parser.add_argument("--max-parallel", type=int, default=5, help="Kimi 并行检索上限（full/toc 阶段有效）")
    parser.add_argument("--gemini-llm-key", help="config.json.llms 中 Gemini 的 key")
    parser.add_argument("--kimi-llm-key", help="config.json.llms 中 Kimi 的 key")
    parser.add_argument("--reconstruct-llm-key", help="config.json.llms 中大纲重构使用的 key")
    parser.add_argument("--classifier-llm-key", help="用于主题分类的 LLM key")
    parser.add_argument("--subject-type", choices=["theory", "tool"], help="手动指定主题类型，跳过自动分类")
    parser.add_argument("--learning-style", help="学习风格：principles | deep_preview | 原理学习 | 深度预习")
    parser.add_argument("--expected-content", help="学习者期望（可选）")
    parser.add_argument("--max-tokens", type=int, default=32768, help="重构阶段的最大 tokens（full/reconstruct 阶段）")
    parser.add_argument("--print-prompt", action="store_true", help="输出 Prompt 以便调试")
    parser.add_argument("--stream", action="store_true", help="启用流式输出（full/reconstruct 阶段）")
    parser.add_argument("--input", help="TOC JSON 输入路径或目录（reconstruct 阶段必填）")
    parser.add_argument("--config", default=str(CONFIG_PATH), help="配置文件路径（默认项目根 config.json）")
    parser.add_argument("--out", help="输出 JSON 文件路径（留空则自动生成）")
    parser.add_argument("--log", action="store_true", help="full 阶段：将终端输出镜像到日志文件")
    parser.add_argument("--debug", action="store_true", help="full 阶段：开启日志并提升日志级别到 DEBUG")
    parser.add_argument("--retry-delay", type=float, default=1.0, help="重试之间的等待秒数（默认 1 秒）")
    parser.add_argument("--load-config-retries", type=int, default=1, help="加载配置的最大尝试次数（默认 1）")
    parser.add_argument("--load-config-timeout", type=float, default=180.0, help="加载配置的超时时间，单位秒（默认 180 秒）")
    parser.add_argument("--toc-retries", type=int, default=1, help="教材推荐与 TOC 阶段的最大尝试次数（默认 1）")
    parser.add_argument("--toc-timeout", type=float, default=180.0, help="教材推荐与 TOC 阶段的超时时间，单位秒（默认 180 秒）")
    parser.add_argument("--reconstruct-retries", type=int, default=1, help="大纲重构阶段的最大尝试次数（默认 1）")
    parser.add_argument("--reconstruct-timeout", type=float, default=300.0, help="大纲重构阶段的超时时间，单位秒（默认 300 秒）")
    parser.add_argument("--output-retries", type=int, default=1, help="输出写入阶段的最大尝试次数（默认 1）")
    parser.add_argument("--output-timeout", type=float, default=180.0, help="输出写入阶段的超时时间，单位秒（默认 180 秒）")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger(__name__)

    retry_delay = max(0.0, float(args.retry_delay or 0.0))
    config_retry_attempts = max(1, int(args.load_config_retries or 1))
    config_retry_timeout = _normalize_timeout(args.load_config_timeout)
    cfg = _run_with_retry(
        "阶段：加载配置",
        lambda: _load_config(args.config),
        max_attempts=config_retry_attempts,
        timeout=config_retry_timeout,
        delay=retry_delay,
        logger=logger,
    )
    stage = args.stage

    toc_retry_attempts = max(1, int(args.toc_retries or 1))
    toc_retry_timeout = _normalize_timeout(args.toc_timeout)
    reconstruct_retry_attempts = max(1, int(args.reconstruct_retries or 1))
    reconstruct_retry_timeout = _normalize_timeout(args.reconstruct_timeout)
    output_retry_attempts = max(1, int(args.output_retries or 1))
    output_retry_timeout = _normalize_timeout(args.output_timeout)

    logger.info(
        "重试配置 | delay=%.1fs | load_config=%d×/%s | toc=%d×/%s | reconstruct=%d×/%s | output=%d×/%s",
        retry_delay,
        config_retry_attempts,
        _format_timeout(config_retry_timeout),
        toc_retry_attempts,
        _format_timeout(toc_retry_timeout),
        reconstruct_retry_attempts,
        _format_timeout(reconstruct_retry_timeout),
        output_retry_attempts,
        _format_timeout(output_retry_timeout),
    )

    if stage in {"full", "toc"} and not (args.subject or "").strip():
        print("[错误] --subject 为必填参数（full/toc 阶段）。", file=sys.stderr)
        return 2
    if stage == "reconstruct" and not args.input:
        print("[错误] reconstruct 阶段必须提供 --input。", file=sys.stderr)
        return 2

    expected_clean = (args.expected_content or "").strip() or None

    node_llm_cfg = cfg.get("node_llm") or {}
    gemini_key = args.gemini_llm_key or node_llm_cfg.get("recommend_textbooks")
    kimi_key = args.kimi_llm_key or node_llm_cfg.get("retrieve_toc")
    reconstruct_key = args.reconstruct_llm_key or node_llm_cfg.get("reconstruct_outline")
    classifier_key = args.classifier_llm_key or node_llm_cfg.get("classify_subject")

    logger.info("LLM Key Mapping:")
    logger.info("  - Textbook Recommendation: %s", gemini_key)
    logger.info("  - TOC Retrieval: %s", kimi_key)
    logger.info("  - Outline Reconstruction: %s", reconstruct_key)
    logger.info("  - Subject Classification: %s", classifier_key)

    if stage == "toc":
        try:
            toc_result = execute_toc_stage(
                subject=args.subject.strip(),
                top_n=max(1, int(args.top_n)),
                max_parallel=max(1, int(args.max_parallel)),
                cfg=cfg,
                gemini_llm_key=gemini_key,
                kimi_llm_key=kimi_key,
                expected_content=expected_clean,
                print_prompt=bool(args.print_prompt),
                logger=logger,
                retry_attempts=toc_retry_attempts,
                retry_timeout=toc_retry_timeout,
                retry_delay=retry_delay,
            )
        except Exception as exc:
            print(f"[错误] {exc}", file=sys.stderr)
            return 1
        if args.out:
            out_path = Path(args.out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            out_dir = BASE_DIR / "output" / "textbook_tocs"
            out_dir.mkdir(parents=True, exist_ok=True)
            slug = toc_result.get("subject_slug") or _slugify(args.subject, "subject")
            out_path = out_dir / f"{slug}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        output_payload = json.dumps(toc_result, ensure_ascii=False, indent=2)

        def _write_toc_output() -> None:
            out_path.write_text(output_payload, encoding="utf-8")

        _run_with_retry(
            "阶段：写入 TOC 输出",
            _write_toc_output,
            max_attempts=output_retry_attempts,
            timeout=output_retry_timeout,
            delay=retry_delay,
            logger=logger,
        )
        logger.info("[完成] 输出文件: %s", out_path)
        recs = toc_result.get("recommendations", []) or []
        logger.info("推荐教材: %d 本 (展示前 %d 本)", len(recs), min(3, len(recs)))
        for i, book in enumerate(recs[:3], 1):
            logger.info("  %d. %s", i, book.get("title", "(no title)"))
        tocs = toc_result.get("tocs", []) or []
        ok = sum(1 for t in tocs if not t.get("error"))
        logger.info("目录获取成功: %d/%d", ok, len(tocs))
        return 0

    if stage == "reconstruct":
        path = _run_with_retry(
            "阶段：解析输入路径",
            lambda: _resolve_json_input(Path(args.input)),
            max_attempts=reconstruct_retry_attempts,
            timeout=reconstruct_retry_timeout,
            delay=retry_delay,
            logger=logger,
        )
        data = _run_with_retry(
            "阶段：读取 TOC JSON",
            lambda: _load_json(path),
            max_attempts=reconstruct_retry_attempts,
            timeout=reconstruct_retry_timeout,
            delay=retry_delay,
            logger=logger,
        )
        tocs = data.get("tocs") or []
        if not isinstance(tocs, list) or not tocs:
            print("[错误] 输入 JSON 中缺少有效的 tocs 列表。", file=sys.stderr)
            return 1
        subject = (args.subject or data.get("subject") or "").strip()
        if not subject:
            print("[错误] 未提供 subject，且输入 JSON 中缺失。", file=sys.stderr)
            return 1
        subject_slug = (data.get("subject_slug") or "").strip() or None
        expected_for_stage = expected_clean if args.expected_content is not None else (data.get("expected_content") or "")
        materials_obj = _run_with_retry(
            "阶段：整理教材材料",
            lambda: prepare_materials_from_tocs(subject, tocs),
            max_attempts=reconstruct_retry_attempts,
            timeout=reconstruct_retry_timeout,
            delay=retry_delay,
            logger=logger,
        )
        try:
            recon_result = execute_reconstruct_stage(
                subject,
                tocs,
                cfg=cfg,
                subject_slug=subject_slug,
                reconstruct_llm_key=reconstruct_key,
                classifier_llm_key=classifier_key,
                subject_type=args.subject_type,
                learning_style=args.learning_style,
                expected_content=expected_for_stage,
                print_prompt=bool(args.print_prompt),
                stream=bool(args.stream),
                max_tokens=args.max_tokens,
                logger=logger,
                materials=materials_obj,
                retry_attempts=reconstruct_retry_attempts,
                retry_timeout=reconstruct_retry_timeout,
                retry_delay=retry_delay,
            )
        except Exception as exc:
            print(f"[错误] {exc}", file=sys.stderr)
            return 1

        if args.out:
            out_path = Path(args.out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            out_dir = BASE_DIR / "output" / "reconstructed_outline"
            out_dir.mkdir(parents=True, exist_ok=True)
            slug = subject_slug or _slugify(subject, "subject")
            out_path = out_dir / f"{slug}-reconstructed-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        output_payload = json.dumps(recon_result.outline, ensure_ascii=False, indent=2)

        def _write_reconstruct_output() -> None:
            out_path.write_text(output_payload, encoding="utf-8")

        _run_with_retry(
            "阶段：写入重构输出",
            _write_reconstruct_output,
            max_attempts=output_retry_attempts,
            timeout=output_retry_timeout,
            delay=retry_delay,
            logger=logger,
        )

        print(f"[完成] 已生成整合目录: {out_path}", file=sys.stderr)
        info = recon_result.llm_info
        key = info.get("key")
        provider = info.get("provider")
        model = info.get("model")
        if provider and model:
            if key:
                print(f"使用模型: {key} ({provider}:{model})", file=sys.stderr)
            else:
                print(f"使用模型: {provider}:{model}", file=sys.stderr)
        elif key:
            print(f"使用模型: {key}", file=sys.stderr)
        print(f"输入教材数: {len(materials_obj.get('materials', []))}", file=sys.stderr)
        return 0

    # stage == full
    subject = args.subject.strip()
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = _slugify(subject, "subject")
    log_fp = None
    orig_stdout, orig_stderr = sys.stdout, sys.stderr

    if args.log or args.debug:
        log_dir = BASE_DIR / "output" / "integrated_pipeline"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"{slug}-integrated-{ts}.log"
        log_fp = open(log_path, "w", encoding="utf-8")
        sys.stdout = _Tee(sys.stdout, log_fp)
        sys.stderr = _Tee(sys.stderr, log_fp)

    try:
        combined, toc_result, recon_result = run_full_pipeline(
            subject,
            top_n=max(1, int(args.top_n)),
            max_parallel=max(1, int(args.max_parallel)),
            cfg=cfg,
            gemini_llm_key=gemini_key,
            kimi_llm_key=kimi_key,
            reconstruct_llm_key=reconstruct_key,
            classifier_llm_key=classifier_key,
            subject_type=args.subject_type,
            learning_style=args.learning_style,
            expected_content=expected_clean,
            print_prompt=bool(args.print_prompt),
            stream=bool(args.stream),
            max_tokens=args.max_tokens,
            logger=logger,
            retry_delay=retry_delay,
            toc_retry_attempts=toc_retry_attempts,
            toc_retry_timeout=toc_retry_timeout,
            reconstruct_retry_attempts=reconstruct_retry_attempts,
            reconstruct_retry_timeout=reconstruct_retry_timeout,
        )
    except Exception as exc:
        if log_fp is not None:
            try:
                sys.stdout.flush()
                sys.stderr.flush()
            except Exception:
                pass
            sys.stdout = orig_stdout
            sys.stderr = orig_stderr
            try:
                log_fp.flush()
                log_fp.close()
            except Exception:
                pass
        print(f"[错误] {exc}", file=sys.stderr)
        return 1

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = BASE_DIR / "output" / "integrated_pipeline"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{combined.get('subject_slug', slug)}-integrated-{ts}.json"
    combined_payload = json.dumps(combined, ensure_ascii=False, indent=2)

    def _write_full_output() -> None:
        out_path.write_text(combined_payload, encoding="utf-8")

    _run_with_retry(
        "阶段：写入综合输出",
        _write_full_output,
        max_attempts=output_retry_attempts,
        timeout=output_retry_timeout,
        delay=retry_delay,
        logger=logger,
    )

    logger.info("[完成] 输出文件: %s", out_path)
    recs = toc_result.get("recommendations", []) or []
    logger.info("推荐教材: %d 本 (展示前 %d 本)", len(recs), min(3, len(recs)))
    for i, book in enumerate(recs[:3], 1):
        logger.info("  %d. %s", i, book.get("title", "(no title)"))
    tocs = toc_result.get("tocs", []) or []
    ok = sum(1 for t in tocs if not t.get("error"))
    logger.info("目录获取成功: %d/%d", ok, len(tocs))
    if recon_result.outline:
        logger.info("大纲重构: 成功")
    else:
        logger.warning("大纲重构: 结果为空")

    if log_fp is not None:
        try:
            sys.stdout.flush()
            sys.stderr.flush()
        except Exception:
            pass
        sys.stdout = orig_stdout
        sys.stderr = orig_stderr
        try:
            log_fp.flush()
            log_fp.close()
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
