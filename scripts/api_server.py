#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI 后端：为 Platform IDE 暴露大纲与章节生成流水线的 HTTP 接口。

- /api/outline/*  提供综合教材大纲生成的启动、流式日志、结果查询与取消能力
- /api/content/*  提供章节内容生成的启动、流式日志、结果查询与取消能力

实现思路：
- 复用现有 Python 脚本（scripts/pipelines/...），通过 asyncio.create_subprocess_exec 启动子进程
- 保留原先 Next.js jobManager 的语义与阶段更新逻辑，前端无需感知差异
- 通过 SSE (Server-Sent Events) 推送日志、阶段进度、结果文件等事件
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import sys
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
import time
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from scripts.common.utils import repo_root, slugify

# ----------------------------
# 基础配置
# ----------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

REPO_ROOT = repo_root(Path(__file__))
PYTHON_BIN = os.environ.get("PYTHON") or sys.executable
CONFIG_PATH = REPO_ROOT / "config.json"
OUTLINE_SCRIPT = REPO_ROOT / "scripts" / "pipelines" / "langgraph" / "integrated_textbook_pipeline_chained.py"
CHAPTER_SCRIPT = (
    REPO_ROOT / "scripts" / "pipelines" / "generation" / "generate_chapters_from_integrated_standalone.py"
)
EXECUTION_OUTPUT_LIMIT = 10_000
DEFAULT_EXECUTION_TIMEOUT = 10.0
MAX_EXECUTION_TIMEOUT = 30.0

CHINA_TZ = timezone(timedelta(hours=8))

JOBS_STATE_DIR = REPO_ROOT / "output" / "pipeline_jobs"
JOBS_STATE_FILE = JOBS_STATE_DIR / "jobs.json"


# ----------------------------
# Job & Stage 数据结构
# ----------------------------

@dataclass
class StageState:
    id: str
    label: str
    status: str = "pending"
    progress: Optional[float] = None
    detail: Optional[str] = None

    def apply(self, patch: Dict[str, Any]) -> None:
        if "label" in patch and patch["label"]:
            self.label = str(patch["label"])
        if "status" in patch and patch["status"]:
            self.status = str(patch["status"])
        if "progress" in patch:
            prog = patch["progress"]
            if prog is None:
                self.progress = None
            else:
                try:
                    self.progress = max(0.0, min(1.0, float(prog)))
                except Exception:
                    self.progress = None
        if "detail" in patch:
            detail = patch["detail"]
            self.detail = None if detail is None else str(detail)

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "id": self.id,
            "label": self.label,
            "status": self.status,
        }
        if self.progress is not None:
            data["progress"] = self.progress
        if self.detail is not None:
            data["detail"] = self.detail
        return data


def _default_stages() -> Dict[str, StageState]:
    return {
        "collect": StageState(id="collect", label="搜集参考教材"),
        "outline": StageState(id="outline", label="整合生成大纲"),
        "content": StageState(id="content", label="生成内容"),
    }


@dataclass
class JobRecord:
    id: str
    type: str  # outline | content
    status: str = "running"
    start_ts: float = field(default_factory=lambda: datetime.now(CHINA_TZ).timestamp())
    end_ts: Optional[float] = None
    subject: Optional[str] = None
    learning_style: Optional[str] = None
    expected_content: Optional[str] = None
    output_path: Optional[str] = None
    log_path: Optional[str] = None
    total_to_fetch: Optional[int] = None
    processed: Optional[int] = None
    pid: Optional[int] = None
    stages: Dict[str, StageState] = field(default_factory=_default_stages)
    process: Optional[asyncio.subprocess.Process] = None
    subscribers: Dict[str, "asyncio.Queue[Dict[str, Any]]"] = field(default_factory=dict)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "status": self.status,
            "startTs": self.start_ts,
            "endTs": self.end_ts,
            "subject": self.subject,
            "learningStyle": self.learning_style,
            "expectedContent": self.expected_content,
            "outputPath": self.output_path,
            "logPath": self.log_path,
            "stages": {key: stage.to_dict() for key, stage in self.stages.items()},
        }


def _make_job_id(prefix: str) -> str:
    return f"{prefix}-{int(datetime.now(CHINA_TZ).timestamp() * 1000)}-{uuid4().hex[:6]}"


class JobManager:
    def __init__(self) -> None:
        self._jobs: Dict[str, JobRecord] = {}
        self._logger = logging.getLogger("JobManager")
        self._load_jobs_from_disk()
        self._persist_jobs()

    def create_job(
        self,
        job_type: str,
        *,
        subject: Optional[str] = None,
        learning_style: Optional[str] = None,
        expected_content: Optional[str] = None,
    ) -> JobRecord:
        job_id = _make_job_id(job_type)
        job = JobRecord(
            id=job_id,
            type=job_type,
            subject=subject,
            learning_style=learning_style,
            expected_content=expected_content,
        )
        self._jobs[job_id] = job
        self._persist_jobs()
        return job

    def get(self, job_id: str) -> Optional[JobRecord]:
        return self._jobs.get(job_id)

    def finish(self, job: JobRecord, status: str) -> None:
        job.status = status
        job.end_ts = datetime.now(CHINA_TZ).timestamp()
        self._persist_jobs()

    def attach(self, job: JobRecord) -> Tuple[str, "asyncio.Queue[Dict[str, Any]]"]:
        client_id = uuid4().hex
        queue: "asyncio.Queue[Dict[str, Any]]" = asyncio.Queue(maxsize=512)
        job.subscribers[client_id] = queue
        return client_id, queue

    def detach(self, job: JobRecord, client_id: str) -> None:
        job.subscribers.pop(client_id, None)

    def broadcast(self, job: JobRecord, event: str, data: Any) -> None:
        payload = {"event": event, "data": data}
        to_remove: List[str] = []
        for client_id, queue in job.subscribers.items():
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                try:
                    queue.put_nowait(payload)
                except asyncio.QueueFull:
                    to_remove.append(client_id)
        for client_id in to_remove:
            job.subscribers.pop(client_id, None)

    def update_stage(self, job: JobRecord, stage_id: str, patch: Dict[str, Any]) -> StageState:
        stage = job.stages.get(stage_id)
        if not stage:
            stage = StageState(id=stage_id, label=stage_id)
            job.stages[stage_id] = stage
        stage.apply(patch)
        self.broadcast(job, "stage", stage.to_dict())
        self._persist_jobs()
        return stage

    def touch(self, job: JobRecord) -> None:
        if job.id not in self._jobs:
            self._jobs[job.id] = job
        self._persist_jobs()

    def list_jobs(self) -> List[JobRecord]:
        return list(self._jobs.values())

    def latest_job(self, job_type: str) -> Optional[JobRecord]:
        candidates = [job for job in self._jobs.values() if job.type == job_type]
        if not candidates:
            return None
        return max(candidates, key=lambda job: job.start_ts)

    def _serialize_job(self, job: JobRecord) -> Dict[str, Any]:
        data = job.snapshot()
        data["pid"] = job.pid
        data["totalToFetch"] = job.total_to_fetch
        data["processed"] = job.processed
        # 直接从北京时间戳转换为北京时间
        start_dt = datetime.fromtimestamp(job.start_ts, tz=CHINA_TZ)
        data["startTimeIso"] = start_dt.isoformat()
        if job.end_ts is not None:
            end_dt = datetime.fromtimestamp(job.end_ts, tz=CHINA_TZ)
            data["endTimeIso"] = end_dt.isoformat()
        return data

    def _persist_jobs(self) -> None:
        try:
            JOBS_STATE_DIR.mkdir(parents=True, exist_ok=True)
            payload = [self._serialize_job(job) for job in self._jobs.values()]
            JOBS_STATE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            self._logger.warning("Failed to persist jobs: %s", exc)

    def _load_jobs_from_disk(self) -> None:
        if not JOBS_STATE_FILE.exists():
            return
        try:
            text = JOBS_STATE_FILE.read_text(encoding="utf-8")
            items = json.loads(text)
        except Exception as exc:
            self._logger.warning("Failed to load jobs from disk: %s", exc)
            return
        if not isinstance(items, list):
            return
        for item in items:
            try:
                job_id = str(item.get("id") or "").strip()
                job_type = str(item.get("type") or "outline")
                if not job_id:
                    continue
                start_ts = item.get("startTs")
                try:
                    start_ts_val = float(start_ts) if start_ts is not None else datetime.now(CHINA_TZ).timestamp()
                except (TypeError, ValueError):
                    start_ts_val = datetime.now(CHINA_TZ).timestamp()
                if isinstance(start_ts, str):
                    with suppress(Exception):
                        start_ts_val = datetime.fromisoformat(start_ts.replace("Z", "+00:00")).timestamp()
                start_time_iso = item.get("startTimeIso")
                if isinstance(start_time_iso, str):
                    with suppress(Exception):
                        start_ts_val = datetime.fromisoformat(start_time_iso.replace("Z", "+00:00")).timestamp()
                job = JobRecord(
                    id=job_id,
                    type=job_type,
                    status=str(item.get("status") or "running"),
                    start_ts=start_ts_val,
                    end_ts=item.get("endTs"),
                    subject=item.get("subject"),
                    learning_style=item.get("learningStyle"),
                    expected_content=item.get("expectedContent"),
                    output_path=item.get("outputPath"),
                    log_path=item.get("logPath"),
                    total_to_fetch=item.get("totalToFetch"),
                    processed=item.get("processed"),
                    pid=item.get("pid"),
                )
                if isinstance(item.get("endTimeIso"), str):
                    with suppress(Exception):
                        job.end_ts = datetime.fromisoformat(item["endTimeIso"].replace("Z", "+00:00")).timestamp()
                stages_data = item.get("stages") or {}
                if isinstance(stages_data, dict):
                    job.stages = {}
                    for stage_id, stage_payload in stages_data.items():
                        if not isinstance(stage_payload, dict):
                            continue
                        stage = StageState(
                            id=str(stage_id),
                            label=str(stage_payload.get("label") or stage_id),
                            status=str(stage_payload.get("status") or "pending"),
                            progress=stage_payload.get("progress"),
                            detail=stage_payload.get("detail"),
                        )
                        job.stages[str(stage_id)] = stage
                if not job.stages:
                    job.stages = _default_stages()
                self._jobs[job_id] = job
            except Exception as exc:
                self._logger.warning("Skipping persisted job due to error: %s", exc)


job_manager = JobManager()
logger = logging.getLogger("api_server")

# 自动补齐生成后的课程 JSON
_learn_data_refresh_tasks: Dict[str, asyncio.Task[None]] = {}


async def _ensure_learn_data_for_slug(slug: str) -> None:
    if not slug:
        return
    script_path = REPO_ROOT / "web-learner" / "scripts" / "generate-learn-data.mjs"
    if not script_path.exists():
        logger.error(
            "[learn-data:refresh] 脚本不存在，跳过课程补齐",
            extra={"slug": slug, "script": str(script_path)},
        )
        return

    cmd = ["node", str(script_path), f"--subjects={slug}", "--no-clean"]
    try:
        logger.info("[learn-data:refresh] 开始补齐课程", extra={"slug": slug, "cmd": cmd})
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(REPO_ROOT),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
    except Exception as exc:  # pragma: no cover - 防御性日志
        logger.exception(
            "[learn-data:refresh] 启动脚本失败",
            extra={"slug": slug, "cmd": cmd, "error": str(exc)},
        )
        return

    std_out = stdout.decode("utf-8", errors="ignore").strip() if stdout else ""
    std_err = stderr.decode("utf-8", errors="ignore").strip() if stderr else ""

    if process.returncode != 0:
        logger.error(
            "[learn-data:refresh] 补齐失败",
            extra={
                "slug": slug,
                "cmd": cmd,
                "returncode": process.returncode,
                "stdout": std_out,
                "stderr": std_err,
            },
        )
        return

    logger.info(
        "[learn-data:refresh] 补齐完成",
        extra={"slug": slug, "stdout": std_out, "stderr": std_err},
    )


def _schedule_learn_data_refresh(slug: str) -> None:
    if not slug:
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        logger.warning(
            "[learn-data:refresh] 无运行中的事件循环，跳过调度", extra={"slug": slug}
        )
        return

    existing = _learn_data_refresh_tasks.get(slug)
    if existing and not existing.done():
        logger.debug(
            "[learn-data:refresh] 已存在进行中的任务，跳过重复调度", extra={"slug": slug}
        )
        return

    task = loop.create_task(_ensure_learn_data_for_slug(slug))
    _learn_data_refresh_tasks[slug] = task

    def _cleanup(done: asyncio.Task[None], *, key: str) -> None:
        _learn_data_refresh_tasks.pop(key, None)
        try:
            done.result()
        except Exception as exc:  # pragma: no cover - 防御性日志
            logger.exception(
                "[learn-data:refresh] 任务执行出错", extra={"slug": key, "error": str(exc)}
            )

    task.add_done_callback(lambda done, key=slug: _cleanup(done, key=key))


# ----------------------------
# 工具函数
# ----------------------------


def _job_payload(job: JobRecord) -> Dict[str, Any]:
    data = job.snapshot()
    data["pid"] = job.pid
    data["totalToFetch"] = job.total_to_fetch
    data["processed"] = job.processed
    return data

def _format_sse(event: str, data: Any) -> bytes:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n".encode("utf-8")


def _normalize_path(path_str: str) -> str:
    candidate = Path(path_str.strip()).expanduser()
    if not candidate.is_absolute():
        candidate = (REPO_ROOT / candidate).resolve()
    return str(candidate)


def _ensure_exists(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _try_parse_int(value: Any) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(value)
    except Exception:
        return None


_EXECUTION_SENSITIVE_ENV_PREFIXES = (
    "OPENAI_",
    "DEEPSEEK_",
    "GOOGLE_",
    "MOONSHOT_",
    "KIMI_",
    "AWS_",
    "AZURE_",
    "GITHUB_",
)


def _build_execution_env() -> Dict[str, str]:
    """Create a sanitized environment for temporary code execution."""
    safe_env: Dict[str, str] = {}
    for key, value in os.environ.items():
        if any(key.startswith(prefix) for prefix in _EXECUTION_SENSITIVE_ENV_PREFIXES):
            continue
        safe_env[key] = value
    # Force deterministic encoding and unbuffered output
    safe_env["PYTHONUNBUFFERED"] = "1"
    safe_env["PYTHONIOENCODING"] = "utf-8"
    # Drop PYTHONPATH to avoid leaking repo internals into user code
    safe_env.pop("PYTHONPATH", None)
    return safe_env


def _trim_output(text: str) -> str:
    if len(text) <= EXECUTION_OUTPUT_LIMIT:
        return text
    return text[:EXECUTION_OUTPUT_LIMIT] + "\n...[output truncated]..."


# ----------------------------
# Outline 阶段日志解析
# ----------------------------

_COLLECT_START_PATTERNS = [
    re.compile(r"\[1/2\]\s*调用.*推荐教材"),
    re.compile(r"启动教材目录生成流水线"),
    re.compile(r"运行\s*TOC\s*流水线"),
]


def _parse_outline_line(job: JobRecord, line: str) -> None:
    text = line.strip()
    if not text:
        return

    if any(pat.search(text) for pat in _COLLECT_START_PATTERNS):
        job_manager.update_stage(job, "collect", {"status": "running", "detail": "调用推荐教材 LLM"})

    m_parallel = re.search(r"并行检索教材目录 .*待检索=(\d+)\s*本", text)
    if m_parallel:
        total = _try_parse_int(m_parallel.group(1)) or 0
        job.total_to_fetch = total
        job.processed = 0
        detail = f"已完成 0/{total or '?'}"
        job_manager.update_stage(
            job,
            "collect",
            {
                "status": "running",
                "progress": 0 if total else None,
                "detail": detail,
            },
        )
        return

    if re.search(r"完成\s*[:：]\s*《", text) or re.search(r"完成但有错误\s*[:：]", text) or re.search(r"任务异常\s*[:：]", text):
        if job.processed is None:
            job.processed = 0
        job.processed += 1
        total = job.total_to_fetch or 0
        progress = (job.processed / total) if total else None
        detail = f"已完成 {job.processed}/{total or '?'} "
        job_manager.update_stage(
            job,
            "collect",
            {
                "status": "running",
                "progress": progress,
                "detail": detail,
            },
        )
        return

    m_ok = re.search(r"目录获取成功:\s*(\d+)\/(\d+)", text)
    if m_ok:
        ok = _try_parse_int(m_ok.group(1)) or 0
        all_cnt = _try_parse_int(m_ok.group(2)) or 0
        job_manager.update_stage(
            job,
            "collect",
            {"status": "completed", "progress": 1, "detail": f"成功 {ok}/{all_cnt}"},
        )
        return

    if re.search(r"大纲重构\s*[:：]\s*成功", text):
        job_manager.update_stage(job, "outline", {"status": "completed", "progress": 1, "detail": "完成"})
        return
    if re.search(r"大纲重构\s*[:：]\s*失败", text):
        job_manager.update_stage(job, "outline", {"status": "error", "detail": "失败"})
        return
    if re.search(r"大纲重构\s*[:：]", text):
        job_manager.update_stage(job, "outline", {"status": "running", "detail": "整合大纲中…"})
        return
    if re.search(r"主题分类\s*[:：]", text):
        job_manager.update_stage(job, "outline", {"status": "running", "detail": "开始整合生成大纲"})
        return
    if re.search(r"正在以流式方式接收模型输出", text):
        job_manager.update_stage(job, "outline", {"status": "running", "detail": "模型输出中…"})
        return

    m_out = re.search(r"输出文件:\s*(.+\.json)\s*$", text)
    if m_out:
        path_str = m_out.group(1).strip()
        job.output_path = _normalize_path(path_str)
        try:
            base = Path(job.output_path)
            job.log_path = str(base.with_suffix(".log"))
        except Exception:
            job.log_path = None
        job_manager.touch(job)
        job_manager.broadcast(job, "file", {"outPath": job.output_path, "logPath": job.log_path})


# ----------------------------
# Content 阶段辅助函数
# ----------------------------

def _load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"读取 JSON 失败: {path} ({exc})") from exc


def _derive_topic_meta(integrated_path: Path) -> Tuple[Optional[str], str]:
    try:
        data = _load_json(integrated_path)
    except Exception:
        return None, "topic"
    subject = data.get("subject")
    if subject is not None:
        subject = str(subject)
    meta_slug = None
    try:
        meta = data.get("reconstructed_outline", {}).get("meta", {})
        if isinstance(meta, dict):
            slug = meta.get("topic_slug")
            if isinstance(slug, str) and slug.strip():
                meta_slug = slug.strip()
    except Exception:
        meta_slug = None
    if not meta_slug:
        s_slug = data.get("subject_slug")
        if isinstance(s_slug, str) and s_slug.strip():
            meta_slug = s_slug.strip()
    if not meta_slug and subject:
        meta_slug = slugify(subject)
    return subject, meta_slug or "topic"


def _compute_section_totals(integrated_path: Path) -> Tuple[int, List[int]]:
    try:
        data = _load_json(integrated_path)
    except Exception:
        return 0, []
    outline = data.get("reconstructed_outline") or data
    total = 0
    per_chapter: List[int] = []
    if isinstance(outline, dict):
        if isinstance(outline.get("groups"), list):
            for group in outline["groups"]:
                if isinstance(group, dict):
                    sections = group.get("sections")
                    count = len(sections) if isinstance(sections, list) else 0
                    per_chapter.append(count)
                    total += count
        elif isinstance(outline.get("chapters"), list):
            for chapter in outline["chapters"]:
                if isinstance(chapter, dict):
                    sections = chapter.get("sections")
                    count = len(sections) if isinstance(sections, list) else 0
                    per_chapter.append(count)
                    total += count
        elif isinstance(outline.get("sections"), list):
            total = len(outline.get("sections"))
            if total:
                per_chapter.append(total)
    return total, per_chapter


def _parse_content_line(
    job: JobRecord,
    line: str,
    counters: Dict[str, Any],
) -> None:
    text = line.strip()
    if not text:
        return

    m_sel = re.search(r"选择章节\s*:\s*\[([^\]]*)\]", text)
    if m_sel:
        tokens = [tok.strip() for tok in m_sel.group(1).split(",") if tok.strip()]
        total = counters.get("total") or 0
        per_chapter: List[int] = counters.get("perChapter") or []
        selected_total = 0
        for tok in tokens:
            if tok.isdigit():
                idx = int(tok)
                if 1 <= idx <= len(per_chapter):
                    selected_total += per_chapter[idx - 1]
        if selected_total > 0:
            counters["total"] = selected_total
        progress = None
        total_val = counters.get("total") or 0
        draft = counters.get("draft") or 0
        if total_val > 0:
            progress = min(0.9, (draft / total_val) * 0.9)
        job_manager.update_stage(
            job,
            "content",
            {
                "status": "running",
                "detail": f"选择章节: {len(tokens)} 个（目标 {total_val or '?'} 个知识点）",
                "progress": progress,
            },
        )
        return

    if "[已保存初稿]" in text:
        counters["draft"] = (counters.get("draft") or 0) + 1
        draft = counters["draft"]
        total_val = counters.get("total") or 0
        detail = f"初稿 {draft}/{total_val}" if total_val else f"初稿 {draft}"
        progress = None
        if total_val > 0:
            progress = min(0.9, (draft / total_val) * 0.9)
        job_manager.update_stage(job, "content", {"status": "running", "detail": detail, "progress": progress})
        return

    if not counters.get("reviewStarted") and "==== LLM Prompt [propose_fix] BEGIN ====" in text:
        counters["reviewStarted"] = True
        draft = counters.get("draft") or 0
        total_val = counters.get("total") or 0
        detail = (
            f"初稿 {draft}/{total_val} · 审核阶段"
            if total_val > 0
            else "审核阶段：模型输出质检中…"
        )
        progress = None
        if total_val > 0:
            progress = max(0.9, min(0.98, draft / total_val))
        job_manager.update_stage(
            job,
            "content",
            {"status": "running", "detail": detail, "progress": progress},
        )
        return

    if "[大纲已保存]" in text or re.search(r"大纲已保存\s*:\s*", text):
        counters["finalized"] = True
        draft = counters.get("draft") or 0
        total_val = counters.get("total") or 0
        detail = f"初稿 {draft}/{total_val} · 已发布" if total_val > 0 else "已发布"
        job_manager.update_stage(
            job,
            "content",
            {"status": "running", "detail": detail, "progress": 1},
        )
        return

    m_report = re.search(r"报告已写出\s*:\s*(.+)$", text)
    if m_report:
        report_path = _normalize_path(m_report.group(1))
        job.output_path = report_path
        try:
            base = Path(report_path)
            slug_match = re.match(r"^pipeline_report_(.+)\.md$", base.name)
            if slug_match:
                slug = slug_match.group(1)
                publish_dir = REPO_ROOT / "web-learner" / "public" / "content" / slug
                log_path = REPO_ROOT / "output" / slug / "log.txt"
                job.log_path = str(log_path)
                job_manager.broadcast(
                    job,
                    "file",
                    {
                        "reportPath": report_path,
                        "publishDir": str(publish_dir),
                        "logPath": str(log_path),
                    },
                )
                _schedule_learn_data_refresh(slug)
            else:
                job_manager.broadcast(job, "file", {"reportPath": report_path})
        except Exception:
            job_manager.broadcast(job, "file", {"reportPath": report_path})
        job_manager.touch(job)
        return

    if "✅" in text and "完成" in text or "完成。无报告可显示。" in text:
        job_manager.update_stage(job, "content", {"status": "completed", "progress": 1, "detail": "完成"})


# ----------------------------
# 临时代码执行（后续可替换为 Docker 沙箱）
# ----------------------------

async def _execute_python_snippet(code: str, *, timeout: float = DEFAULT_EXECUTION_TIMEOUT) -> Dict[str, Any]:
    safe_timeout = max(1.0, min(float(timeout), MAX_EXECUTION_TIMEOUT))
    started_at = time.monotonic()
    timed_out = False
    exec_stdout = ""
    exec_stderr = ""
    exit_code: Optional[int] = None
    status = "success"

    payload = json.dumps({"code": code, "timeout": safe_timeout})
    docker_image = os.environ.get("SANDBOX_IMAGE", "platform-ide-python-sandbox")
    docker_cmd = [
        "docker",
        "run",
        "--rm",
        "--network=none",
        "--pids-limit=64",
        "--memory=512m",
        "--cpus=1.0",
        "-i",
        docker_image,
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *docker_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=_build_execution_env(),
        )
        assert process.stdin is not None
        assert process.stdout is not None
        assert process.stderr is not None

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(input=payload.encode("utf-8")),
                timeout=safe_timeout + 1.0,
            )
        except asyncio.TimeoutError:
            timed_out = True
            status = "timeout"
            process.kill()
            with suppress(Exception):
                await process.communicate()
            stdout_bytes, stderr_bytes = b"", b"[server] docker run timeout"

        exit_code = process.returncode
        try:
            parsed = json.loads(stdout_bytes.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            parsed = None

        if isinstance(parsed, dict) and "status" in parsed:
            status = parsed.get("status", "error")
            exec_stdout = _trim_output(str(parsed.get("stdout", "")))
            exec_stderr = _trim_output(str(parsed.get("stderr", "")))
            timed_out = bool(parsed.get("timedOut", False))
            exit_code = parsed.get("exitCode")
        else:
            status = "error"
            exec_stdout = _trim_output(stdout_bytes.decode("utf-8", errors="replace"))
            exec_stderr = _trim_output(stderr_bytes.decode("utf-8", errors="replace"))
    except Exception as exc:
        status = "error"
        exec_stdout = ""
        exec_stderr = f"[server] 执行失败: {exc}"
        exit_code = None

    duration = time.monotonic() - started_at
    return {
        "status": status,
        "stdout": exec_stdout,
        "stderr": exec_stderr,
        "exitCode": exit_code,
        "timedOut": timed_out,
        "duration": duration,
    }


# ----------------------------
# 任务执行器
# ----------------------------

async def _stream_process_output(job: JobRecord, stream: asyncio.StreamReader, parser) -> None:
    while True:
        line = await stream.readline()
        if not line:
            break
        text = line.decode("utf-8", errors="replace").rstrip("\n")
        if not text:
            continue
        job_manager.broadcast(job, "log", {"line": text})
        try:
            parser(job, text)
        except Exception as exc:  # 容忍解析失败
            logger.debug("解析日志失败: %s (%s)", text, exc)


async def _run_outline_job(
    subject: str,
    learning_style: str,
    expected_content: Optional[str],
    top_n: Optional[int],
    print_prompt: bool,
    debug: bool,
    gemini_key: Optional[str],
    kimi_key: Optional[str],
) -> JobRecord:
    job = job_manager.create_job(
        "outline",
        subject=subject,
        learning_style=learning_style,
        expected_content=expected_content,
    )

    args: List[str] = [
        PYTHON_BIN,
        "-u",
        str(OUTLINE_SCRIPT),
        "--subject",
        subject,
        "--learning-style",
        learning_style,
    ]
    if expected_content:
        args.extend(["--expected-content", expected_content])
    if isinstance(top_n, int) and top_n > 0:
        args.extend(["--top-n", str(top_n)])
    if print_prompt:
        args.append("--print-prompt")
    if debug:
        args.append("--debug")
    elif os.environ.get("PIPELINE_LOG") == "1":
        args.append("--log")
    if gemini_key:
        args.extend(["--gemini-llm-key", gemini_key])
    if kimi_key:
        args.extend(["--kimi-llm-key", kimi_key])

    env = os.environ.copy()
    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(REPO_ROOT),
        env=env,
    )

    job.process = process
    job.pid = process.pid
    job_manager.touch(job)

    job_manager.update_stage(job, "collect", {"status": "running", "detail": "启动脚本中…"})
    job_manager.broadcast(job, "log", {"line": f"[orchestrator] spawn: {' '.join(args)}"})
    job_manager.broadcast(job, "log", {"line": f"[orchestrator] cwd: {REPO_ROOT}"})

    async def monitor() -> None:
        stdout = process.stdout
        stderr = process.stderr
        if stdout is None or stderr is None:
            job_manager.finish(job, "error")
            job_manager.broadcast(job, "end", {"status": "error", "message": "子进程未提供输出流"})
            return

        tasks = [
            asyncio.create_task(_stream_process_output(job, stdout, _parse_outline_line)),
            asyncio.create_task(_stream_process_output(job, stderr, _parse_outline_line)),
        ]

        try:
            return_code = await process.wait()
        except Exception as exc:  # pragma: no cover - 容错
            logger.exception("outline 子进程执行异常: %s", exc)
            job_manager.finish(job, "error")
            job_manager.broadcast(job, "end", {"status": "error", "message": str(exc)})
            return
        finally:
            for task in tasks:
                task.cancel()
            for task in tasks:
                with suppress(asyncio.CancelledError):
                    await task

        if return_code == 0:
            job_manager.finish(job, "success")
            job_manager.broadcast(
                job,
                "end",
                {
                    "status": "success",
                    "outputPath": job.output_path,
                    "logPath": job.log_path,
                },
            )
        else:
            job_manager.finish(job, "error")
            job_manager.update_stage(job, "outline", {"status": "error", "detail": f"进程退出码 {return_code}"})
            job_manager.broadcast(
                job,
                "end",
                {"status": "error", "message": f"进程退出码 {return_code}"},
            )

    asyncio.create_task(monitor())
    return job


async def _run_content_job(
    input_path: Path,
    selected_chapters: Optional[str],
    debug: bool,
) -> JobRecord:
    subject, topic_slug = _derive_topic_meta(input_path)
    total, per_chapter = _compute_section_totals(input_path)

    job = job_manager.create_job("content", subject=subject)

    args: List[str] = [
        PYTHON_BIN,
        "-u",
        str(CHAPTER_SCRIPT),
        "--input",
        str(input_path),
        "--config",
        str(CONFIG_PATH),
    ]
    # Align with Next.js pipeline behaviour: skip content review by default.
    args.append("--skip-content-review")
    if selected_chapters:
        args.extend(["--selected-chapters", selected_chapters])
    if debug or os.environ.get("PIPELINE_LOG") == "1":
        args.append("--debug")

    log_dir = REPO_ROOT / "output" / topic_slug
    _ensure_exists(log_dir)
    job.log_path = str(log_dir / "log.txt")
    job_manager.touch(job)

    env = os.environ.copy()
    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(REPO_ROOT),
        env=env,
    )

    job.process = process
    job.pid = process.pid
    job_manager.touch(job)

    initial_detail = f"初稿 0/{total}" if total > 0 else "启动脚本中…"
    job_manager.update_stage(
        job,
        "content",
        {
            "status": "running",
            "detail": initial_detail,
            "progress": 0 if total > 0 else None,
        },
    )
    job_manager.broadcast(job, "log", {"line": f"[orchestrator] spawn: {' '.join(args)}"})
    job_manager.broadcast(job, "log", {"line": f"[orchestrator] cwd: {REPO_ROOT}"})
    if job.log_path:
        job_manager.broadcast(job, "file", {"logPath": job.log_path})

    counters = {
        "draft": 0,
        "total": total,
        "perChapter": per_chapter,
        "reviewStarted": False,
        "finalized": False,
    }

    async def monitor() -> None:
        stdout = process.stdout
        stderr = process.stderr
        if stdout is None or stderr is None:
            job_manager.finish(job, "error")
            job_manager.broadcast(job, "end", {"status": "error", "message": "子进程未提供输出流"})
            return

        tasks = [
            asyncio.create_task(_stream_process_output(job, stdout, lambda j, line: _parse_content_line(j, line, counters))),
            asyncio.create_task(_stream_process_output(job, stderr, lambda j, line: _parse_content_line(j, line, counters))),
        ]

        try:
            return_code = await process.wait()
        except Exception as exc:  # pragma: no cover - 容错
            logger.exception("content 子进程执行异常: %s", exc)
            job_manager.finish(job, "error")
            job_manager.broadcast(job, "end", {"status": "error", "message": str(exc)})
            return
        finally:
            for task in tasks:
                task.cancel()
            for task in tasks:
                with suppress(asyncio.CancelledError):
                    await task

        if return_code == 0:
            job_manager.finish(job, "success")
            job_manager.broadcast(
                job,
                "end",
                {
                    "status": "success",
                    "outputPath": job.output_path,
                    "logPath": job.log_path,
                },
            )
        else:
            job_manager.finish(job, "error")
            job_manager.update_stage(job, "content", {"status": "error", "detail": f"进程退出码 {return_code}"})
            job_manager.broadcast(
                job,
                "end",
                {"status": "error", "message": f"进程退出码 {return_code}"},
            )

    asyncio.create_task(monitor())
    return job


# ----------------------------
# SSE 输出
# ----------------------------

async def _event_stream(job: JobRecord, request: Request) -> AsyncIterator[bytes]:
    client_id, queue = job_manager.attach(job)
    try:
        yield _format_sse("hello", {"jobId": job.id, "snapshot": job.snapshot()})
        for stage in job.stages.values():
            yield _format_sse("stage", stage.to_dict())

        if job.status != "running":
            yield _format_sse(
                "end",
                {
                    "status": job.status,
                    "outputPath": job.output_path,
                    "logPath": job.log_path,
                },
            )
            return

        while True:
            if await request.is_disconnected():
                break
            try:
                event = await asyncio.wait_for(queue.get(), timeout=20.0)
            except asyncio.TimeoutError:
                yield b": ping\n\n"
                continue
            yield _format_sse(event["event"], event["data"])
    finally:
        job_manager.detach(job, client_id)


# ----------------------------
# FastAPI 路由
# ----------------------------

app = FastAPI(title="Platform IDE Python API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/pipeline/jobs")
async def pipeline_jobs() -> JSONResponse:
    jobs = [_job_payload(job) for job in job_manager.list_jobs()]
    jobs.sort(key=lambda item: item.get("startTs") or 0, reverse=True)
    return JSONResponse({"jobs": jobs})


@app.get("/api/pipeline/jobs/latest")
async def pipeline_jobs_latest(type: str) -> JSONResponse:
    job = job_manager.latest_job(type)
    if not job:
        return JSONResponse({"job": None})
    return JSONResponse({"job": _job_payload(job)})


@app.get("/api/pipeline/jobs/{job_id}")
async def pipeline_jobs_detail(job_id: str) -> JSONResponse:
    job = job_manager.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return JSONResponse({"job": _job_payload(job)})


@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "Platform IDE Python API server is running"}


@app.post("/api/execute/run")
async def execute_run(payload: Dict[str, Any]) -> Dict[str, Any]:
    language = str(payload.get("language") or "python").strip().lower()
    if language not in {"python", "py"}:
        raise HTTPException(status_code=400, detail="当前仅支持 language=python")
    code = payload.get("code")
    if not isinstance(code, str) or not code.strip():
        raise HTTPException(status_code=400, detail="请求体需提供非空的 code 字符串")

    timeout_raw = payload.get("timeout")
    timeout_val = DEFAULT_EXECUTION_TIMEOUT
    if timeout_raw is not None:
        try:
            timeout_val = float(timeout_raw)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="timeout 参数必须为数字") from None

    result = await _execute_python_snippet(code, timeout=timeout_val)
    return {
        "status": result["status"],
        "language": "python",
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "exitCode": result["exitCode"],
        "timedOut": result["timedOut"],
        "duration": result["duration"],
    }


@app.post("/api/outline/start")
async def outline_start(payload: Dict[str, Any]) -> Dict[str, Any]:
    subject = str(payload.get("subject") or "").strip()
    if not subject:
        raise HTTPException(status_code=400, detail="主题 subject 必填")

    learning_style_raw = str(payload.get("learningStyle") or "").strip()
    style_map = {
        "principles": "principles",
        "原理学习": "principles",
        "deep_preview": "deep_preview",
        "深度预习": "deep_preview",
    }
    learning_style = style_map.get(learning_style_raw.lower())
    if not learning_style:
        raise HTTPException(status_code=400, detail="学习风格必须为 principles/deep_preview（或中文）")

    expected_content = str(payload.get("expectedContent") or "").strip() or None
    top_n = _try_parse_int(payload.get("topN"))
    print_prompt = bool(payload.get("printPrompt", True))
    debug = bool(payload.get("debug", False))
    gemini_key = (payload.get("geminiKey") or None) and str(payload.get("geminiKey"))
    kimi_key = (payload.get("kimiKey") or None) and str(payload.get("kimiKey"))

    job = await _run_outline_job(
        subject=subject,
        learning_style=learning_style,
        expected_content=expected_content,
        top_n=top_n,
        print_prompt=print_prompt,
        debug=debug,
        gemini_key=gemini_key,
        kimi_key=kimi_key,
    )
    return {"jobId": job.id}


@app.get("/api/outline/stream")
async def outline_stream(jobId: str, request: Request) -> StreamingResponse:
    job = job_manager.get(jobId)
    if not job:
        raise HTTPException(status_code=404, detail=f"job not found: {jobId}")
    return StreamingResponse(
        _event_stream(job, request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.get("/api/outline/result")
async def outline_result(jobId: str) -> JSONResponse:
    job = job_manager.get(jobId)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    if not job.output_path:
        return JSONResponse({"error": "输出文件尚未确定", "status": job.status}, status_code=202)
    path = Path(job.output_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"结果文件不存在: {path}")
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"解析结果失败: {exc}") from exc
    return JSONResponse(data)


@app.post("/api/outline/cancel")
async def outline_cancel(jobId: str) -> Dict[str, Any]:
    job = job_manager.get(jobId)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    proc = job.process
    if proc and proc.returncode is None:
        try:
            proc.terminate()
        except ProcessLookupError:
            pass
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
    job_manager.finish(job, "cancelled")
    job_manager.broadcast(job, "end", {"status": "cancelled"})
    return {"ok": True}


@app.post("/api/content/start")
async def content_start(payload: Dict[str, Any]) -> Dict[str, Any]:
    ref_job_id = str(payload.get("refJobId") or "").strip() or None
    input_path_raw = payload.get("inputPath")
    selected_chapters = str(payload.get("selectedChapters") or "").strip() or None
    debug = bool(payload.get("debug", True))

    input_path: Optional[Path] = None
    if input_path_raw:
        candidate = Path(str(input_path_raw)).expanduser()
        input_path = candidate if candidate.is_absolute() else (REPO_ROOT / candidate).resolve()

    if not input_path and ref_job_id:
        ref_job = job_manager.get(ref_job_id)
        if ref_job and ref_job.output_path and ref_job.status == "success":
            input_path = Path(ref_job.output_path)

    if not input_path:
        raise HTTPException(status_code=400, detail="缺少 inputPath 或 refJobId")

    if not input_path.exists() or not input_path.is_file():
        raise HTTPException(status_code=400, detail=f"找不到集成大纲文件: {input_path}")

    job = await _run_content_job(input_path=input_path, selected_chapters=selected_chapters, debug=debug)
    return {"jobId": job.id}


@app.get("/api/content/stream")
async def content_stream(jobId: str, request: Request) -> StreamingResponse:
    job = job_manager.get(jobId)
    if not job:
        raise HTTPException(status_code=404, detail=f"job not found: {jobId}")
    return StreamingResponse(
        _event_stream(job, request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


def _infer_slug_from_report(report_path: Optional[str]) -> Optional[str]:
    if not report_path:
        return None
    base = Path(report_path).name
    m = re.match(r"^pipeline_report_(.+)\.md$", base)
    if not m:
        return None
    return m.group(1)


@app.get("/api/content/result")
async def content_result(jobId: str) -> JSONResponse:
    job = job_manager.get(jobId)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    slug = _infer_slug_from_report(job.output_path)
    publish_dir: Optional[Path] = None
    if slug:
        publish_dir = REPO_ROOT / "web-learner" / "public" / "content" / slug
    published_files: Optional[List[str]] = None
    if publish_dir and publish_dir.exists() and publish_dir.is_dir():
        published_files = []
        for entry in publish_dir.iterdir():
            if entry.is_file() and entry.suffix.lower() == ".md":
                rel = Path("web-learner") / "public" / "content" / slug / entry.name  # type: ignore[arg-type]
                published_files.append(str(rel))
    report_path = None
    if job.output_path:
        report_path = str(Path(job.output_path))
    payload = {
        "subject": job.subject,
        "reportPath": report_path,
        "logPath": job.log_path,
        "publishDir": str(publish_dir) if publish_dir else None,
        "publishedFiles": published_files,
        "status": job.status,
    }
    return JSONResponse(payload)


@app.post("/api/content/cancel")
async def content_cancel(jobId: str) -> Dict[str, Any]:
    job = job_manager.get(jobId)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    proc = job.process
    if proc and proc.returncode is None:
        try:
            proc.terminate()
        except ProcessLookupError:
            pass
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
    job_manager.finish(job, "cancelled")
    job_manager.broadcast(job, "end", {"status": "cancelled"})
    return {"ok": True}
