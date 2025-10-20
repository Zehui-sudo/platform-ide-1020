#!/usr/bin/env python3
"""
基于 LangGraph 的端到端知识生产工作流。

目标
- 适用于任意主题（不限于 LangGraph 相关内容）。
- 人在回路：生成大纲草案后接受人工反馈（同意或修改意见），LLM 根据反馈决定接受或继续修订，直到被接受再继续后续流程。
- 按知识点并行生成与并行审查，提高吞吐与质量稳定性。

主要特性
- 纯 LangGraph 编排（节点、条件边、可选检查点）。
- 节点内使用异步并发（asyncio + Semaphore）保障稳定与速率。
- 尽量复用现有脚本的约定与目录结构。

使用方式（示例）
  python run_full_langgraph_pipeline.py \
    --topic "现代前端测试体系" \
    --outline-feedback "需要更强调端到端测试覆盖率与Mock策略" \
    --provider openai_compat \
    --max-parallel 6

    - 默认安全自动应用（config.json 已设 safe）：- python run_full_langgraph_pipeline.py --topic "现代前端测试体系" --debug
    - 更激进（含 major 且置信度≥0.8 自动应用）：- python run_full_langgraph_pipeline.py --auto-apply-mode aggressive --auto-apply-threshold-major 0.8 --debug
    - 全自动（all，接受所有修改）：- python run_full_langgraph_pipeline.py --topic "现代前端测试体系" --auto-apply-mode all --debug

配置
- 优先读取同目录下的 config.json（否则回退到 config.example.json）。关键字段：
  - api_provider: openai_compat | deepseek | gemini 之一
  - deepseek_api_key / deepseek_base_url
  - openai_api_key / openai_base_url
  - gemini_api_key（或使用环境变量 GOOGLE_API_KEY）
  - model, temperature, max_tokens, retry_times, retry_delay, max_parallel_requests

输出
- 大纲与内容输出至 web-learner/public/
- 生成的知识点内容位于 web-learner/public/content/<topic_slug>/
- 终端打印最终报告，同时保存为 pipeline_report_<topic_slug>.md
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import sys
import unicodedata
from dataclasses import dataclass
from operator import add
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TypedDict, Annotated
from mermaid_sanitizer import sanitize_mermaid_in_markdown

# --- LangGraph imports (with helpful error) ---
try:
    from langgraph.graph import StateGraph, START, END
except Exception:
    sys.stderr.write(
        "[错误] 未找到 langgraph。请先安装：\n"
        "  python -m pip install -U langgraph\n"
    )
    raise

# Optional checkpointer (best-effort)
try:
    from langgraph.checkpoint.memory import MemorySaver  # type: ignore
except Exception:
    MemorySaver = None  # type: ignore


BASE_DIR = Path(__file__).parent.resolve()
PUBLIC_DIR = BASE_DIR / "web-learner" / "public"
CONTENT_ROOT = PUBLIC_DIR / "content"
CONFIG_JSON = BASE_DIR / "config.json"
CONFIG_EXAMPLE_JSON = BASE_DIR / "config.example.json"

LOG_FILE = BASE_DIR / "full_pipeline.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

def _enable_debug_logging(enable: bool, output_subdir: str = "") -> None:
    """开启调试日志。
    - 当 enable=True 时：
      1) 将 logger 级别提升为 DEBUG；
      2) 追加一个输出到 output/<output_subdir>/debug.log 的文件句柄（如有 output_subdir）。
    - 默认日志 full_pipeline.log 仍然保留。
    """
    if not enable:
        return
    try:
        logger.setLevel(logging.DEBUG)
        for h in logger.handlers:
            try:
                h.setLevel(logging.DEBUG)
            except Exception:
                pass
        # 追加一个每次运行独立的 debug 日志到 output/<subdir>/
        if output_subdir:
            dbg_dir = BASE_DIR / "output" / output_subdir
            ensure_dir(dbg_dir)
            dbg_path = dbg_dir / "pipeline.debug.log"
            fh = logging.FileHandler(dbg_path, encoding="utf-8")
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            logger.addHandler(fh)
            logger.debug(f"Debug 日志已启用，文件: {dbg_path}")
    except Exception as e:
        try:
            logger.warning(f"启用 Debug 日志失败: {e}")
        except Exception:
            pass


# ----------------------------
# Auto-apply policy defaults
# ----------------------------

AUTO_APPLY_DEFAULTS = {
    "auto_apply_mode": "off",  # off | safe | aggressive | all
    "auto_apply_threshold_major": 0.8,   # aggressive 档对 major 的置信度阈值
}


# ----------------------------
# Utilities
# ----------------------------

def _load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _load_config(config_path: Optional[str]) -> Dict[str, Any]:
    defaults = {
        "api_provider": "deepseek",  # or deepseek / gemini
        "openai_base_url": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "openai_api_key": os.environ.get("OPENAI_API_KEY", ""),
        "deepseek_base_url": os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        "deepseek_api_key": os.environ.get("DEEPSEEK_API_KEY", ""),
        "gemini_api_key": os.environ.get("GOOGLE_API_KEY", ""),
        "model": "deepseek-reasoner",  # sensible default; override as needed
        "temperature": 0.6,
        "max_tokens": 4096,
        "retry_times": 3,
        "retry_delay": 10,
        "max_parallel_requests": 8,
        "sanitize_mermaid": True,
    }

    path: Optional[Path] = Path(config_path) if config_path else (CONFIG_JSON if CONFIG_JSON.exists() else CONFIG_EXAMPLE_JSON)
    if path and path.exists():
        try:
            user = _load_json(path)
            defaults.update(user)
            logger.info(f"配置已加载: {path}")
        except Exception:
            logger.warning(f"配置文件读取失败，将使用默认配置: {path}")
    else:
        # create example to help users
        try:
            CONFIG_EXAMPLE_JSON.write_text(json.dumps(defaults, ensure_ascii=False, indent=2), encoding="utf-8")
            logger.info(f"已写出示例配置: {CONFIG_EXAMPLE_JSON}")
        except Exception:
            pass
    return defaults


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[\s/]+", "-", text)
    text = re.sub(r"[^a-z0-9\-_.]+", "", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "topic"


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def try_parse_json_array(text: str) -> List[Dict[str, Any]]:
    t = (text or "").strip()
    if not t:
        return []
    # try fenced blocks first
    if "```" in t:
        parts = t.split("```")
        for part in parts:
            s = part.strip()
            if s.startswith("[") and s.endswith("]"):
                try:
                    return json.loads(s)
                except Exception:
                    pass
    # fallback: bracket range
    try:
        i = t.index("[")
        j = t.rindex("]")
        return json.loads(t[i : j + 1])
    except Exception:
        return []


def try_parse_json_object(text: str) -> Dict[str, Any]:
    """尽力从文本中解析出一个 JSON 对象（支持代码围栏块）。"""
    t = (text or "").strip()
    if not t:
        return {}
    if "```" in t:
        parts = t.split("```")
        for part in parts:
            s = part.strip()
            if s.startswith("{") and s.endswith("}"):
                try:
                    return json.loads(s)
                except Exception:
                    pass
    try:
        i = t.index("{")
        j = t.rindex("}")
        return json.loads(t[i : j + 1])
    except Exception:
        return {}


# ----------------------------
"""
（已简化）旧的基于差异特征的自动应用启发式已移除；
保留的阈值策略见 _should_auto_apply/_should_auto_apply_by_review。
"""


def _issues_categories_and_confidence(review_obj: Dict[str, Any]) -> Tuple[List[str], float, bool]:
    """Extract categories list, min confidence across issues, and has_major flag.
    Backward-compatible: if no categories or confidence, make best-effort.
    """
    issues = review_obj.get("issues") if isinstance(review_obj.get("issues"), list) else []
    cats: List[str] = []
    min_conf = 1.0
    has_major = False
    for it in issues:
        if isinstance(it, dict):
            c = str(it.get("category", "")).strip()
            if c:
                cats.append(c)
            sev = str(it.get("severity", "")).strip().lower()
            if sev == "major":
                has_major = True
            try:
                conf = float(it.get("confidence", 1))
            except Exception:
                conf = 1.0 if sev != "major" else 0.5
            min_conf = min(min_conf, conf)
    # Fallbacks
    if not cats:
        # no categories provided
        cats = ["uncategorized"]
    if min_conf == 1.0 and not issues:
        # is_perfect or unknown -> treat as high confidence
        min_conf = 1.0
    return cats, min_conf, has_major


def _should_auto_apply(
    cfg: Dict[str, Any],
    current_md: str,
    revised_md: str,
    review_obj: Dict[str, Any],
) -> Tuple[bool, str]:
    mode = str(cfg.get("auto_apply_mode") or AUTO_APPLY_DEFAULTS["auto_apply_mode"]).strip().lower()
    # all: 接受所有修改
    if mode == "all":
        return True, "mode=all"
    if mode == "off":
        return False, "auto_apply_mode=off"

    # 基于阈值的简化判定（不依赖类别/差异），只看 severity + confidence
    issues = review_obj.get("issues") if isinstance(review_obj.get("issues"), list) else []
    if review_obj.get("is_perfect", False) and not issues:
        return False, "is_perfect"
    majors = []
    for it in issues:
        if not isinstance(it, dict):
            continue
        if str(it.get("severity", "")).lower() == "major":
            try:
                majors.append(float(it.get("confidence", 1)))
            except Exception:
                majors.append(0.0)

    if mode == "safe":
        if not majors:  # 只有 minor
            return True, "safe: all minor"
        return False, "safe: has major"

    if mode == "aggressive":
        if not majors:
            return True, "aggressive: all minor"
        thr = float(cfg.get("auto_apply_threshold_major", AUTO_APPLY_DEFAULTS["auto_apply_threshold_major"]))
        if majors and min(majors) >= thr:
            return True, f"aggressive: majors_conf>={thr}"
        return False, f"aggressive: majors_conf<{thr}"

    # fallback
    return False, f"unknown_mode:{mode}"


def _precheck_auto_possible(cfg: Dict[str, Any], review_obj: Dict[str, Any]) -> bool:
    """轻量预检的简化版：仅看 severity + confidence。
    - safe: 若存在major则返回False；
    - aggressive: 若存在major且最低confidence<threshold则返回False；
    - all: True； off: False。
    其余情况 True。
    """
    mode = str(cfg.get("auto_apply_mode") or AUTO_APPLY_DEFAULTS["auto_apply_mode"]).strip().lower()
    if mode == "off":
        return False
    if mode == "all":
        return True

    issues = review_obj.get("issues") if isinstance(review_obj.get("issues"), list) else []
    majors_conf: List[float] = []
    for it in issues:
        if isinstance(it, dict) and str(it.get("severity", "")).lower() == "major":
            try:
                majors_conf.append(float(it.get("confidence", 1)))
            except Exception:
                majors_conf.append(0.0)

    if mode == "safe":
        return len(majors_conf) == 0

    if mode == "aggressive":
        if not majors_conf:
            return True
        thr = float(cfg.get("auto_apply_threshold_major", AUTO_APPLY_DEFAULTS["auto_apply_threshold_major"]))
        return min(majors_conf) >= thr

    return False


def _should_auto_apply_by_review(cfg: Dict[str, Any], review_obj: Dict[str, Any]) -> Tuple[bool, str]:
    """仅基于审查结果进行判定（阈值语义）。
    - safe: 所有 issues 为 minor 才自动；
    - aggressive: 若存在 major，需所有 major 的 confidence >= threshold；
    - all: 全部自动； off: 全部不自动。
    返回 (bool, reason)。
    """
    mode = str(cfg.get("auto_apply_mode") or AUTO_APPLY_DEFAULTS["auto_apply_mode"]).strip().lower()
    if mode == "off":
        return False, "off"
    if mode == "all":
        return True, "all"
    issues = review_obj.get("issues") if isinstance(review_obj.get("issues"), list) else []
    if review_obj.get("is_perfect", False) and not issues:
        return False, "is_perfect"
    majors_conf: List[float] = []
    for it in issues:
        if isinstance(it, dict) and str(it.get("severity", "")).lower() == "major":
            try:
                majors_conf.append(float(it.get("confidence", 1)))
            except Exception:
                majors_conf.append(0.0)

    if mode == "safe":
        ok = len(majors_conf) == 0
        return ok, "safe: all minor" if ok else "safe: has major"

    if mode == "aggressive":
        if not majors_conf:
            return True, "aggressive: all minor"
        thr = float(cfg.get("auto_apply_threshold_major", AUTO_APPLY_DEFAULTS["auto_apply_threshold_major"]))
        ok = min(majors_conf) >= thr
        return ok, (f"aggressive: majors_conf>={thr}" if ok else f"aggressive: majors_conf<{thr}")

    return False, f"unknown_mode:{mode}"
# Interactive helpers (TTY-aware)
# ----------------------------

def _isatty() -> bool:
    try:
        return sys.stdin.isatty()
    except Exception:
        return False


def ask(prompt: str, default: Optional[str] = None) -> str:
    """Ask for single-line input. Falls back to default if non-interactive or EOF."""
    if not _isatty():
        return default or ""
    try:
        s = input(f"{prompt}{f' [默认: {default}]' if default else ''}: ").strip()
        return s if s else (default or "")
    except EOFError:
        return default or ""


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    """Ask for yes/no. Falls back to default if non-interactive or EOF."""
    if not _isatty():
        return default
    suffix = "[Y/n]" if default else "[y/N]"
    try:
        s = input(f"{prompt} {suffix}: ").strip().lower()
        if not s:
            return default
        return s in {"y", "yes", "true", "1"}
    except EOFError:
        return default


def ask_multiline(prompt: str, end_marker: str = "END") -> str:
    """Ask for multi-line input. Finish by typing the end_marker alone on a line.
    Returns empty string if non-interactive or EOF.
    """
    if not _isatty():
        return ""
    print(f"{prompt}\n(以单独一行输入 {end_marker} 结束)")
    lines: List[str] = []
    try:
        while True:
            line = input()
            # Normalize to handle full-width characters and odd spaces
            norm = unicodedata.normalize("NFKC", line).strip()
            # Accept several common terminators, case-insensitively
            if norm.lower() in {end_marker.lower(), "end", "done", "eof", "eod", "结束", "完成"}:
                break
            lines.append(line)
    except EOFError:
        pass
    return "\n".join(lines).strip()


# ----------------------------
# LLM client wrappers (best-effort)
# ----------------------------

class _AsyncLLM:
    async def ainvoke(self, prompt: str) -> str:
        raise NotImplementedError


class OpenAICompatClient(_AsyncLLM):
    def __init__(self, api_key: str, base_url: str, model: str, temperature: float, max_tokens: int) -> None:
        self._ok = False
        try:
            from openai import AsyncOpenAI  # type: ignore
        except Exception as e:
            logger.error("缺少 openai 库，请安装: pip install openai")
            self._client = None
            self._ok = False
            return
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._ok = True

    async def ainvoke(self, prompt: str) -> str:
        if not self._ok:
            raise RuntimeError("OpenAI 兼容客户端未正确初始化")
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": "你是一位严谨的技术写作与编辑助手。"},
                {"role": "user", "content": prompt},
            ],
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        return (resp.choices[0].message.content or "") if (resp and resp.choices) else ""


class GeminiClient(_AsyncLLM):
    def __init__(self, api_key: str, model: str) -> None:
        self._ok = False
        try:
            import google.generativeai as genai  # type: ignore
        except Exception as e:
            logger.error("缺少 google-generativeai，请安装: pip install -U google-generativeai")
            self._model = None
            return
        if not api_key:
            logger.error("缺少 GOOGLE_API_KEY / gemini_api_key 配置")
            return
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model)
        self._ok = True

    async def ainvoke(self, prompt: str) -> str:
        if not self._ok:
            raise RuntimeError("Gemini 客户端未正确初始化")
        # offload to thread pool
        def _sync_call() -> str:
            resp = self._model.generate_content(prompt)
            # attempt robust text extraction
            txt = getattr(resp, "text", "")
            if txt:
                return txt
            try:
                cands = getattr(resp, "candidates", [])
                if cands:
                    parts = getattr(getattr(cands[0], "content", None), "parts", [])
                    if parts and hasattr(parts[0], "text"):
                        return parts[0].text or ""
            except Exception:
                pass
            return ""

        return await asyncio.to_thread(_sync_call)


def init_llm(cfg: Dict[str, Any]) -> _AsyncLLM:
    provider = str(cfg.get("api_provider", "openai_compat")).lower()
    model = cfg.get("model", "gpt-4o-mini")
    temperature = float(cfg.get("temperature", 0.6))
    max_tokens = int(cfg.get("max_tokens", 4096))
    if provider in {"openai_compat", "deepseek", "openai"}:
        # Support DeepSeek via base_url + key
        api_key = cfg.get("openai_api_key") or cfg.get("deepseek_api_key") or os.environ.get("OPENAI_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
        base_url = cfg.get("openai_base_url") or cfg.get("deepseek_base_url") or os.environ.get("OPENAI_BASE_URL") or os.environ.get("DEEPSEEK_BASE_URL") or "https://api.openai.com/v1"
        return OpenAICompatClient(api_key=api_key or "", base_url=base_url, model=model, temperature=temperature, max_tokens=max_tokens)
    elif provider in {"gemini", "google"}:
        api_key = cfg.get("gemini_api_key") or os.environ.get("GOOGLE_API_KEY") or ""
        return GeminiClient(api_key=api_key, model=model)
    else:
        raise SystemExit(f"未知的 api_provider: {provider}")


def _resolve_provider(entry: Dict[str, Any], fallback: Dict[str, Any]) -> str:
    p = entry.get("provider") or entry.get("api_provider") or fallback.get("api_provider") or "openai_compat"
    return str(p).lower()


def _make_llm_from_entry(entry: Dict[str, Any], fallback: Dict[str, Any]) -> _AsyncLLM:
    provider = _resolve_provider(entry, fallback)
    model = entry.get("model") or fallback.get("model", "gpt-4o-mini")
    temperature = float(entry.get("temperature", fallback.get("temperature", 0.6)))
    max_tokens = int(entry.get("max_tokens", fallback.get("max_tokens", 4096)))
    if provider in {"openai_compat", "deepseek", "openai"}:
        api_key = (
            entry.get("api_key")
            or entry.get("openai_api_key")
            or entry.get("deepseek_api_key")
            or fallback.get("openai_api_key")
            or fallback.get("deepseek_api_key")
            or os.environ.get("OPENAI_API_KEY")
            or os.environ.get("DEEPSEEK_API_KEY")
            or ""
        )
        base_url = (
            entry.get("base_url")
            or entry.get("openai_base_url")
            or entry.get("deepseek_base_url")
            or fallback.get("openai_base_url")
            or fallback.get("deepseek_base_url")
            or os.environ.get("OPENAI_BASE_URL")
            or os.environ.get("DEEPSEEK_BASE_URL")
            or "https://api.openai.com/v1"
        )
        return OpenAICompatClient(api_key=api_key, base_url=base_url, model=model, temperature=temperature, max_tokens=max_tokens)
    elif provider in {"gemini", "google"}:
        api_key = entry.get("api_key") or entry.get("gemini_api_key") or fallback.get("gemini_api_key") or os.environ.get("GOOGLE_API_KEY") or ""
        return GeminiClient(api_key=api_key, model=str(model))
    else:
        raise SystemExit(f"未知的 api_provider: {provider}")


def build_llm_registry(cfg: Dict[str, Any]) -> Dict[str, _AsyncLLM]:
    """Construct a name -> LLM registry from cfg['llms'] with a 'default' fallback."""
    reg: Dict[str, _AsyncLLM] = {}
    # default
    reg["default"] = init_llm(cfg)
    entries = cfg.get("llms", {}) or {}
    if isinstance(entries, dict):
        for name, entry in entries.items():
            try:
                if not isinstance(entry, dict):
                    continue
                reg[name] = _make_llm_from_entry(entry, cfg)
            except Exception as e:
                logger.warning(f"LLM 注册失败: {name}: {e}")
    return reg


def select_llm_for_node(cfg: Dict[str, Any], registry: Dict[str, _AsyncLLM], node_key: str, subrole: Optional[str] = None) -> _AsyncLLM:
    """Select LLM by node key with sensible fallbacks.

    Fallback order:
    1) node_llm["{node_key}.{subrole}"]
    2) node_llm["{node_key}"]
    3) Backward-compat alias: if node_key == "generate_and_review_by_chapter",
       also try keys under "generate_and_review_parallel".
    4) node_llm["default"] if present and valid in registry.
    5) registry["default"].
    """
    mapping = cfg.get("node_llm", {}) or {}

    def _resolve_name(nk: str, sr: Optional[str]) -> Optional[str]:
        if sr:
            return mapping.get(f"{nk}.{sr}") or mapping.get(nk)
        return mapping.get(nk)

    # 1/2: direct match
    name: Optional[str] = _resolve_name(node_key, subrole)

    # 3: alias support for older configs
    if not name and node_key == "generate_and_review_by_chapter":
        name = _resolve_name("generate_and_review_parallel", subrole)

    # Return if valid
    if name and name in registry:
        return registry[name]

    # 4: mapping-provided default
    map_default = mapping.get("default")
    if map_default and map_default in registry:
        return registry[map_default]

    # 5: registry default
    return registry.get("default")  # type: ignore


# ----------------------------
# Data structures
# ----------------------------

@dataclass
class Point:
    id: str
    title: str
    chapter: str
    section: str


class WorkState(TypedDict, total=False):
    # Inputs / meta
    topic: str
    topic_meta: Dict[str, Any]
    topic_slug: str
    config: Dict[str, Any]
    # Outline
    outline_final_md: str
    # Structured
    outline_struct: Dict[str, Any]
    points: List[Point]
    # Prompting
    prompts: Annotated[List[Dict[str, str]], add]  # {id, prompt}
    # Generation / review artefacts
    drafts: Annotated[List[Dict[str, str]], add]   # {id, content}
    reviews: Annotated[List[Dict[str, Any]], add]  # review json per id
    publish_paths: Annotated[List[str], add]
    failures: Annotated[List[Dict[str, Any]], add]
    report_md: str
    # Fix proposals and application results
    fix_proposals: Annotated[List[Dict[str, Any]], add]
    fix_applied: Annotated[List[str], add]
    fix_skipped: Annotated[List[str], add]
    fix_iterations: Annotated[List[Dict[str, Any]], add]  # {id, iterations}
    # Runtime
    output_subdir: str
    # Chapter control
    selected_chapters: List[str]
    # Auto-apply metrics (optional, for reporting)
    auto_apply_stats: Dict[str, Any]


def _parse_indices_from_id(pid: str) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    try:
        m = re.match(r"^.*?-sec-(\d+)-(\d+)-(\d+)-.*$", pid)
        if not m:
            return None, None, None
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    except Exception:
        return None, None, None


def _make_filename(pid: str, title: str, style: str = "id") -> str:
    if style == "id":
        return f"{pid}.md"
    ci, gi, si = _parse_indices_from_id(pid)
    # title-based slug (best effort)
    title_slug = slugify(title)
    if style == "structured":
        if ci and gi and si:
            base = f"sec-{ci}-{gi}-{si}-{title_slug or 'section'}"
        else:
            base = title_slug or pid
        return f"{base}.md"
    # fallback to id
    return f"{pid}.md"


"""
大纲与模板整合（新版）
- 移除旧版大纲提示词/正则解析/人工反馈等逻辑。
- 直接复用 scripts/generate_outline_pipeline.py 的四阶段流水线能力，得到结构化大纲与 Markdown 大纲。
- 生成阶段采用“上下文驱动 + primary_goal + suggested_modules”的统一 Prompt，不再依赖 archetype 模板库。
"""

# 将 scripts/ 目录加入导入路径，便于直接 import 脚本函数
SCRIPTS_DIR = BASE_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

try:
    # 仅导入必要函数，避免耦合过多实现细节
    from generate_outline_pipeline import (
        LLMCaller as _PipelineLLMCaller,
        choose_llm as _pipeline_choose_llm,
        stage1_brainstorm as _pipeline_stage1,
        stage2_structure as _pipeline_stage2,
        stage3_detail_and_classify as _pipeline_stage3,
        apply_defaults_and_ids as _pipeline_apply_defaults_and_ids,
        render_markdown as _pipeline_render_markdown,
        stage4_llm_global_review as _pipeline_stage4_llm_review,
    )
except Exception as e:
    logger.error(f"导入四阶段大纲流水线失败，将无法生成结构化大纲：{e}")
    # 兼容占位：不再依赖 archetype

def _coerce_depth(value: str) -> str:
    """将 depth 统一映射到 overview|core|advanced。"""
    v = (value or "").strip().lower()
    mapping = {
        "overview": "overview",
        "概览": "overview",
        "core": "core",
        "中等": "core",
        "advanced": "advanced",
        "高级": "advanced",
        "深入": "advanced",
    }
    return mapping.get(v, "core")

def _run_outline_pipeline(topic: str, cfg: Dict[str, Any], topic_slug: str, topic_meta: Dict[str, Any]) -> Tuple[Dict[str, Any], str, Dict[str, Any]]:
    """执行四阶段大纲流水线，返回三元组：
    (outline_struct, learning_path_md, review_report)
    - outline_struct: 含 meta/topic_slug 与 chapters/groups/sections（每个 section 含 primary_goal 与 suggested_modules）
    - learning_path_md: 渲染后的 Markdown 大纲
    - review_report: 审阅阶段产物（若未启用，则给出占位信息）
    """
    node_llm = cfg.get("node_llm", {}) or {}

    # 选择阶段模型
    # Stage-specific configs for fine-grained control
    try:
        s1_cfg = _pipeline_choose_llm(
            cfg,
            node_llm.get("generate_outline.stage1") or node_llm.get("generate_outline"),
            "generate_outline",
        )
    except Exception:
        s1_cfg = _pipeline_choose_llm(cfg, node_llm.get("default"), "generate_outline")

    try:
        s2_cfg = _pipeline_choose_llm(
            cfg,
            node_llm.get("generate_outline.stage2") or node_llm.get("generate_outline"),
            "generate_outline",
        )
    except Exception:
        s2_cfg = s1_cfg

    try:
        s3_cfg = _pipeline_choose_llm(
            cfg,
            node_llm.get("generate_outline.stage3")
            or node_llm.get("generate_prompt_template")
            or node_llm.get("generate_outline"),
            "generate_prompt_template",
        )
    except Exception:
        s3_cfg = s1_cfg

    # 审阅模型（Stage 4 大纲审阅）：
    # 可显式跳过；否则优先 generate_outline.review；若未配置则回退到 generate_outline；再回退到 default。
    review_cfg = None
    try:
        if not cfg.get("skip_outline_review", False):
            rk = (
                node_llm.get("generate_outline.review")
                or node_llm.get("generate_outline")
                or node_llm.get("default")
            )
            if rk:
                review_cfg = _pipeline_choose_llm(cfg, rk, "generate_outline")
    except Exception:
        review_cfg = None

    gen_stage1_caller = _PipelineLLMCaller(s1_cfg)
    gen_stage2_caller = _PipelineLLMCaller(s2_cfg)
    stage3_caller = _PipelineLLMCaller(s3_cfg)
    review_caller = _PipelineLLMCaller(review_cfg) if review_cfg else None

    out_dir = BASE_DIR / "output" / topic_slug
    ensure_dir(out_dir)
    basename = topic_slug

    max_parallel = int(cfg.get("max_parallel_requests", 5)) or 1
    if max_parallel <= 0:
        max_parallel = 1
    max_tokens = int(cfg.get("max_tokens", 4096))
    depth = _coerce_depth(str(topic_meta.get("depth", "core")))
    language = str(topic_meta.get("lang", "zh")).strip() or "zh"

    debug = bool(cfg.get("debug", False))
    if debug:
        logger.debug(f"[大纲] 主题='{topic}', depth='{depth}', language='{language}', 并发={max_parallel}, tokens={max_tokens}")
        try:
            logger.debug(
                f"[大纲] S1={getattr(s1_cfg,'key',None)}, S2={getattr(s2_cfg,'key',None)}, S3={getattr(s3_cfg,'key',None)}, REVIEW={getattr(review_cfg,'key',None) if review_cfg else None}"
            )
        except Exception:
            pass

    # 阶段 1/4：脑暴（多视角并行）
    if debug:
        logger.debug("[大纲] 阶段1：开始脑暴 seeds …")
    professor_seeds, engineer_seeds = _pipeline_stage1(
        gen_stage1_caller, topic, language, out_dir, basename, max_tokens, max_parallel
    )
    seeds_path = out_dir / f"{basename}.seeds.json"
    try:
        seeds_for_downstream = json.loads(seeds_path.read_text(encoding="utf-8"))
    except Exception:
        # 退化合并：仅在文件读取失败时使用内存集合
        merged = (professor_seeds or []) + (engineer_seeds or [])
        seeds_for_downstream = {"seeds": merged}
    if debug:
        logger.debug(
            f"[大纲] 阶段1完成：教授={len(professor_seeds)}, 工程师={len(engineer_seeds)}, 合并={len(seeds_for_downstream.get('seeds', []))}"
        )

    # 阶段 2/4：结构骨架
    if debug:
        logger.debug("[大纲] 阶段2：开始聚类与排序 skeleton …")
    skeleton = _pipeline_stage2(
        gen_stage2_caller,
        topic,
        professor_seeds,
        engineer_seeds,
        depth,
        language,
        out_dir,
        basename,
        max_tokens,
    )
    if debug:
        logger.debug(f"[大纲] 阶段2完成：chapters={len(skeleton.get('chapters', []))}")

    # 阶段 3/4：细化 + 原型分类
    if debug:
        logger.debug("[大纲] 阶段3：章节细化 + 原型分类 …")
    stage3 = _pipeline_stage3(
        caller=stage3_caller,
        topic=topic,
        skeleton=skeleton,
        seeds=seeds_for_downstream,
        out_dir=out_dir,
        basename=basename,
        max_tokens=max_tokens,
        max_parallel=max_parallel,
    )
    if debug:
        try:
            chs = stage3.get("chapters") or []
            secs = sum(len(gr.get("sections") or []) for ch in chs for gr in (ch.get("groups") or []))
            logger.debug(f"[大纲] 阶段3完成：chapters={len(chs)}, sections={secs}")
        except Exception:
            pass

    # 统一补默认 + 稳定 ID（使用外部已生成的 topic_slug 以避免退化）
    outline_struct = _pipeline_apply_defaults_and_ids(
        topic, {"meta": {"topic_slug": topic_slug}, "chapters": stage3.get("chapters") or []}
    )

    review_report: Dict[str, Any] = {"mode": "none"}

    # 可选：LLM 全局审阅（若配置了审阅模型）
    if review_caller is not None:
        try:
            review_json, modified_outline = _pipeline_stage4_llm_review(
                caller_review=review_caller,
                topic=topic,
                data_with_ids=outline_struct,
                max_tokens=max_tokens,
            )
            outline_struct = modified_outline or outline_struct
            review_report = review_json or {"mode": "llm_review_and_apply"}
        except Exception as e:
            logger.warning(f"Stage4 LLM 审阅失败，保留 Stage3 结果：{e}")
            review_report = {"mode": "llm_review_and_apply", "error": str(e)}
    elif cfg.get("skip_outline_review", False):
        review_report = {"mode": "skipped"}

    # 最终渲染 Markdown
    md_text = _pipeline_render_markdown(outline_struct)

    # 将最终产物也写入 output/<topic_slug>/ 便于调试/复查
    try:
        (out_dir / f"{basename}.outline.json").write_text(
            json.dumps(outline_struct, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (out_dir / f"{basename}.learning-path.md").write_text(md_text, encoding="utf-8")
        (out_dir / f"{basename}.review.json").write_text(
            json.dumps(review_report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception as e:
        logger.debug(f"[大纲] 写出最终产物到 output 失败: {e}")

    if debug:
        try:
            chs = outline_struct.get("chapters") or []
            secs = sum(
                len(gr.get("sections") or []) for ch in chs for gr in (ch.get("groups") or [])
            )
            logger.debug(f"[大纲] 最终大纲就绪：chapters={len(chs)}, sections={secs}")
        except Exception:
            pass

    return outline_struct, md_text, review_report


# ----------------------------
# 兼容保留：模板渲染工具（当前流程未使用）
# ----------------------------

_ARCHETYPE_TEMPLATES_CACHE: Optional[Dict[str, str]] = None

def _load_archetype_templates() -> Dict[str, str]:
    """（已废弃）保留空实现以兼容老代码路径，不再加载模板。"""
    return {}


def _render_template_variables(tpl: str, variables: Dict[str, str]) -> str:
    out = tpl
    for k, v in (variables or {}).items():
        out = out.replace("{{" + k + "}}", str(v))
    return out

    


# ----------------------------
# Node implementations
# ----------------------------

async def generate_slug_node(state: WorkState, llm: _AsyncLLM) -> WorkState:
    topic = state.get("topic", "")
    if not topic:
        return {**state, "topic_slug": "topic"}

    prompt = (
        "你的任务是为一个给定的主题生成一个简洁、全小写、URL友好、用连字符分隔（kebab-case）的英文slug。\n\n"
        "约束：\n"
        "1. 只包含英文字母、数字和连字符'-'。\n"
        "2. 如果主题是中文或其他语言，请先将其翻译或音译为有意义的英文。\n"
        "3. 结果必须简短且具有描述性。\n\n"
        "主题: \"计算机网络原理\"\n"
        "Slug: computer-network-principles\n\n"
        "主题: \"八字算命\"\n"
        "Slug: bazi-divination\n\n"
        f"主题: \"{topic}\"\n"
        "Slug:"
    )
    # helper to clean
    def _clean(s: str) -> str:
        s = (s or "").strip().lower()
        s = re.sub(r'[^a-z0-9\-]+', '', s)
        s = re.sub(r'-+', '-', s).strip('-')
        return s

    # initial try
    try:
        slug = await llm.ainvoke(prompt)
        final_slug = _clean(slug) or slugify(topic)
    except Exception as e:
        logger.error(f"生成 slug 失败: {e}, 将使用旧版 slugify 方法")
        final_slug = slugify(topic)

    logger.info(f"生成 Slug: {topic} -> {final_slug}")

    # Interactive confirmation with feedback-driven retry
    if _isatty():
        tries = 0
        while True:
            use_it = ask_yes_no(f"是否使用该 slug: '{final_slug}'?", default=True)
            if use_it:
                break
            fb = ask_multiline("请输入修改意见（留空则转为手动输入）", end_marker="END").strip()
            if not fb:
                custom = ask("请输入自定义 slug (kebab-case)", default=final_slug).strip().lower()
                final_slug = _clean(custom) or final_slug
                break
            prompt_fb = (
                "根据以下主题与上一版候选slug，结合反馈，生成一个更合适的英文kebab-case slug。\n\n"
                f"主题: {topic}\n"
                f"上一版: {final_slug}\n"
                f"反馈: {fb}\n\n"
                "只输出 slug 本身："
            )
            try:
                new_slug = await llm.ainvoke(prompt_fb)
                final_slug = _clean(new_slug) or final_slug
            except Exception:
                pass
            tries += 1
            if tries >= 3:
                break

    return {**state, "topic_slug": final_slug}


## 旧版 Prompt 模板生成节点已删除：不再预先按模板派生 Prompt


def topic_input_node(state: WorkState) -> WorkState:
    # Prefer interactive entry/confirmation
    current = state.get("topic") or os.environ.get("TOPIC", "")
    default_topic = current or "示例主题"
    topic = ask("请输入主题", default=default_topic) if _isatty() else default_topic
    if not topic:
        topic = "示例主题"
    return {**state, "topic": topic, "topic_slug": slugify(topic)}


async def generate_outline_node(state: WorkState, llm: _AsyncLLM) -> WorkState:
    """使用四阶段流水线生成结构化大纲与 Markdown 大纲。
    说明：旧版基于提示词的一次性生成已移除。
    """
    topic = state.get("topic", "")
    cfg = state.get("config", {}) or {}
    topic_slug = state.get("topic_slug") or slugify(topic)
    meta = state.get("topic_meta", {}) or {}

    try:
        outline_struct, md_text, review_report = _run_outline_pipeline(topic, cfg, topic_slug, meta)
        # 若流水线内生成的 meta.topic_slug 与现有不同，以流水线为准
        try:
            topic_slug2 = (outline_struct.get("meta") or {}).get("topic_slug")
            if topic_slug2:
                topic_slug = topic_slug2
        except Exception:
            pass

        # 将结构化大纲转为 points（一个 section 即一个知识点）
        def _points_from_struct(data: Dict[str, Any]) -> List[Point]:
            pts: List[Point] = []
            chapters = data.get("chapters") or []
            for ch in chapters:
                ch_title = ch.get("title", "")
                for gr in (ch.get("groups") or []):
                    gr_title = gr.get("title", "")
                    for sec in (gr.get("sections") or []):
                        pid = sec.get("id") or ""
                        ptitle = sec.get("title") or ""
                        if pid and ptitle:
                            pts.append(Point(id=str(pid), title=str(ptitle), chapter=str(ch_title), section=str(gr_title)))
            return pts

        points = _points_from_struct(outline_struct)
        logger.info(f"大纲就绪：章节数={len(outline_struct.get('chapters') or [])}，知识点数={len(points)}")
        return {
            **state,
            "topic_slug": topic_slug,
            "outline_struct": outline_struct,
            "outline_final_md": md_text,
            "points": points,
        }
    except Exception as e:
        logger.error(f"四阶段流水线生成大纲失败：{e}")
        # 失败时返回原 state，不再回退旧流程（按需求移除旧兼容路径）
        return state


# 已废弃：不再预先按 archetype 生成静态 Prompt


# ----------------------------
# Generation prompt builder (context-aware, unified)
# ----------------------------

def _build_contextual_content_prompt(
    *,
    topic: str,
    language: str,
    path: str,
    section_title: str,
    primary_goal: str = "",
    suggested_modules: Optional[List[str]] = None,
    structure_type: str = "pipeline",
    relation_to_previous: str = "",
    prior_context: str = "",
) -> str:
    """Construct a flexible, context-driven prompt for content generation.

    - For pipeline: treat as continuation; inject prior_context as the completed part of the same group.
    - For toolbox: generate an independent or hybrid prompt; if relation indicates dependency, inject prior_context as parent context.
    """
    lang = (language or "zh").strip().lower()
    role = "你是一位资深的教育作者，擅长连贯写作与教学取舍。"
    head = f"# 课程内容生成任务\n\n{role}\n"
    if path:
        head += f"\n【定位】{path}\n"

    goal_part = f"\n【教学目标】{primary_goal}\n" if primary_goal else "\n【教学目标】围绕当前知识点展开，高质量解释并给出必要示例。\n"
    mods = suggested_modules or []
    if mods:
        mods_part = "\n【建议内容模块（酌情采用）】" + ", ".join(mods) + "\n"
    else:
        mods_part = "\n【建议内容模块（酌情采用）】summary, code_example（如适合）, common_mistake_warning（如有）, diagram（如有因果/流程）\n"

    if structure_type == "pipeline":
        ctx_part = (f"\n【已完成的小节内容（Context）】\n> " + prior_context.replace("\n", "\n> ") + "\n") if prior_context else "\n"
        task = (
            f"\n【你的任务】请紧接上述内容，围绕“{section_title}”自然过渡并续写下一段，保持叙事连贯，避免重复。\n"
        )
    else:  # toolbox
        # Hybrid: independent instruction with optional parent context
        dep = relation_to_previous.strip().lower()
        if prior_context and dep in {"builds_on", "deep_dive_into"}:
            ctx_part = f"\n【父级知识点（Parent Context）】\n> " + prior_context.replace("\n", "\n> ") + "\n"
            if dep == "deep_dive_into":
                task = f"\n【你的任务】基于上面的父级知识点，深入讲解“{section_title}”，突出与父主题的内在联系与扩展。\n"
            else:
                task = f"\n【你的任务】在父主题基础上，推进并完善“{section_title}”，说明改进之处或新增能力。\n"
        else:
            ctx_part = "\n"
            task = f"\n【你的任务】请撰写一篇关于“{section_title}”的独立教学段落，内容完整、清晰、可读。\n"

    constraints = (
        "\n【输出约束】\n"
        "- 使用 Markdown；结构清晰，标题层级合理；\n"
        "- 叙事连贯：避免与已给上下文重复；必要时用一句话承接；\n"
        "- 如引用数学/图表/流程，请使用适当的模块；\n"
        "- 如 Markdown 中涉及代码示例，请用代码块进行声明包裹；\n"
        "- 表格中不要出现代码格式的内容；\n"
        "- 结尾含简短总结或要点回顾。\n"
    )
    lang_line = f"\n【语言】{('中文' if lang.startswith('zh') else 'English')}\n"

    return head + goal_part + mods_part + ctx_part + task + constraints + lang_line


# ----------------------------
# Generation + review (parallel inside node)
# ----------------------------

async def _gen_one_point(llm: _AsyncLLM, prompt: str, retries: int, delay: int) -> str:
    last = ""
    for _ in range(max(1, retries)):
        try:
            last = await llm.ainvoke(prompt)
            if last:
                return last
        except Exception as e:
            logger.error(f"生成调用失败: {e}")
        await asyncio.sleep(max(1, delay))
    return last


async def _review_one_point(llm: _AsyncLLM, point_id: str, content_md: str) -> Dict[str, Any]:
    instr = (
        "你是严格的技术编辑，请仅输出 JSON 数组（单元素），包含：\n"
        "file_id, topic_adherence_score, topic_adherence_comment, uniqueness_score, uniqueness_comment, quality_score, quality_comment。\n"
        "分值仅能为: 'OK', 'Warning', 'Critical Error'。"
    )
    prompt = (
        f"{instr}\n\n[文件ID] {point_id}\n\n[内容]\n{content_md}\n"
        "请输出 JSON 数组，且不包含任何额外文本。"
    )
    try:
        text = await llm.ainvoke(prompt)
        arr = try_parse_json_array(text)
        if arr:
            item = arr[0]
            item.setdefault("file_id", point_id)
            try:
                logger.debug(
                    f"[Review] {point_id} parsed: is_perfect={item.get('is_perfect')} issues_cnt={len(item.get('issues', [])) if isinstance(item.get('issues'), list) else 'n/a'}"
                )
            except Exception:
                pass
            return item
    except Exception as e:
        logger.error(f"审查失败: {e}")
    return {
        "file_id": point_id,
        "topic_adherence_score": "Warning",
        "topic_adherence_comment": "解析失败，默认 Warning",
        "uniqueness_score": "Warning",
        "uniqueness_comment": "解析失败，默认 Warning",
        "quality_score": "Warning",
        "quality_comment": "解析失败，默认 Warning",
    }


async def _review_one_point_with_context(
    llm: _AsyncLLM,
    point_id: str,
    content_md: str,
    peer_points: List[Dict[str, str]],
) -> Dict[str, Any]:
    """Review a single point with awareness of other points in the same chapter."""
    review_prompt_template = '''你是资深的技术编辑，你的任务是审查下面的草稿，并以JSON格式提供具体的、可操作的反馈。

【审查维度】
1. 准确性: 内容与代码是否技术上准确？
2. 清晰度: 解释是否易懂？示例是否清晰？
3. 完整性: 是否遗漏关键概念或步骤？
4. 一致性: 是否与标题及其在课程大纲中的定位相符？

【分类要求（非常重要）】
对每个问题进行分类，并估计信心度(confidence: 0~1)。分类category仅能取以下值之一：
- formatting, typo, heading, link_fix, reference, style, redundancy, minor_clarity, minor_structure, example_polish,
- factual_error, code_bug, algorithm_logic, security, api_breaking_change

【输出格式（仅输出一个JSON对象，无任何额外文本）】
顶层键：
- is_perfect: 布尔；若无需任何修改则为 true。
- issues: 数组；若 is_perfect=true 则为空数组。

每个 issue 必须包含：
- severity: 'major' | 'minor'
- category: 上述分类之一
- confidence: 0~1 之间的小数
- description: 字符串，问题描述
- suggestion: 字符串，具体且可执行的修复建议

【上下文】
[文件ID] {point_id}
[同章节其他知识点]
{peers_lines}

【当前内容】
{content_md}

【你的JSON输出】
'''
    peers_lines = "\n".join([f"- {p.get('id', '')}: {p.get('title', '')}" for p in peer_points])
    prompt = review_prompt_template.format(
        point_id=point_id,
        peers_lines=peers_lines if peers_lines else '(无)',
        content_md=content_md
    )
    try:
        text = await llm.ainvoke(prompt)
        obj = try_parse_json_object(text)
        if obj:
            obj.setdefault("file_id", point_id)
            try:
                logger.debug(
                    f"[Review.cx] {point_id} parsed: is_perfect={obj.get('is_perfect')} issues_cnt={len(obj.get('issues', [])) if isinstance(obj.get('issues'), list) else 'n/a'}"
                )
            except Exception:
                pass
            return obj
    except Exception as e:
        logger.error(f"带上下文审查失败: {e}")
    
    # Fallback response
    return {
        "file_id": point_id,
        "is_perfect": False,
        "issues": [{
            "severity": "major",
            "description": "审查节点执行或JSON解析失败。",
            "suggestion": "请检查上游内容或审查模型的输出是否稳定。"
        }]
    }


def _severity_score(item: Dict[str, Any]) -> int:
    # map severity strings to numeric for thresholding
    # This function might need adjustment or could be deprecated if we only use `_has_non_ok`
    # For now, let's make it compatible. It will count the number of major issues.
    if item.get("is_perfect", False):
        return 0
    
    score = 0
    for issue in item.get("issues", []):
        if issue.get("severity") == "major":
            score += 2
        else:
            score += 1
    return score


def _has_non_ok(item: Dict[str, Any]) -> bool:
    """如果 is_perfect 为 false 或 issues 列表不为空，则视为需要修复。"""
    if item.get("is_perfect", False):
        return False
    if item.get("issues"):
        return True
    return False



def _render_unified_diff(old: str, new: str, context_lines: int = 3, max_output_lines: int = 120) -> str:
    import difflib
    old_lines = (old or "").splitlines()
    new_lines = (new or "").splitlines()
    diff = list(difflib.unified_diff(old_lines, new_lines, fromfile="原稿", tofile="修订", lineterm="", n=context_lines))
    if len(diff) > max_output_lines:
        head = diff[: max_output_lines // 2]
        tail = diff[-max_output_lines // 2 :]
        diff = head + ["...（diff 省略）..."] + tail
    return "\n".join(diff)


async def _propose_fix(
    llm: _AsyncLLM,
    point_id: str,
    point_title: str,
    topic: str,
    outline_md: str,
    current_md: str,
    review: Dict[str, Any],
    prior_proposal: Optional[Dict[str, Any]] = None,
    user_feedback: str = "",
) -> Dict[str, Any]:
    """向 LLM 请求修复方案：输出 JSON 对象，包含 summary 与 revised_content。"""
    constraints = (
        "请仅输出一个 JSON 对象，不要任何额外文字；键：\n"
        "- summary: 对需要修改点与改动的简要说明（中文，100-200字）；\n"
        "- revised_content: 修订后的完整 Markdown 内容（必须是完整替换稿而非片段）；\n"
        "- risk (可选): 'low'|'medium'|'high'；\n"
        "- change_categories (可选): 数组，参考审查分类（formatting/typo/...）；\n"
        "- notes (可选): 对修复范围的简短说明。"
    )
    feedback_part = f"\n[用户反馈]\n{user_feedback}\n" if user_feedback else ""
    prior_part = f"\n[上一版修复方案]\n{json.dumps(prior_proposal, ensure_ascii=False)}\n" if prior_proposal else ""
    prompt = (
        "你是严谨的技术编辑与作者。基于以下上下文，提出修复提案并给出修订后完整内容。\n\n"
        f"[主题]\n{topic}\n\n"
        f"[知识点]\n{point_title} (ID: {point_id})\n\n"
        f"[大纲]\n{outline_md}\n\n"
        f"[当前内容]\n{current_md}\n\n"
        f"[审查结果]\n{json.dumps(review, ensure_ascii=False)}\n"
        f"{prior_part}{feedback_part}\n"
        f"{constraints}\n"
    )
    try:
        text = await llm.ainvoke(prompt)
        obj = try_parse_json_object(text)
        if isinstance(obj, dict) and obj.get("revised_content"):
            return obj
    except Exception as e:
        logger.error(f"生成修复方案失败: {e}")
    # fallback：保持原稿，给出默认摘要
    return {
        "summary": "自动生成修复方案失败，建议人工检查并完善。",
        "revised_content": current_md or "",
    }


async def generate_and_review_parallel_node(state: WorkState, llm_generate: _AsyncLLM, llm_review: _AsyncLLM) -> WorkState:
    cfg = state.get("config", {})
    max_parallel = int(cfg.get("max_parallel_requests", 8))
    retries = int(cfg.get("retry_times", 3))
    delay = int(cfg.get("retry_delay", 10))
    sem = asyncio.Semaphore(max_parallel)

    prompts = {p["id"]: p["prompt"] for p in (state.get("prompts") or [])}
    ids = list(prompts.keys())

    drafts: List[Dict[str, str]] = []
    reviews: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []

    async def _one(pid: str):
        nonlocal drafts, reviews, failures
        async with sem:
            content = await _gen_one_point(llm_generate, prompts[pid], retries, delay)
            drafts.append({"id": pid, "content": content})
        # review outside semaphore to decouple a bit
        async with sem:
            review = await _review_one_point(llm_review, pid, content)
            reviews.append(review)
            if _severity_score(review) >= 3:  # any Warning or higher across dimensions
                failures.append({"id": pid, "review": review})

    await asyncio.gather(*[_one(pid) for pid in ids])
    return {**state, "drafts": drafts, "reviews": reviews, "failures": failures}


def _collect_chapters_in_order(state: WorkState) -> List[Dict[str, Any]]:
    """Collect chapter info list preserving outline order.
    Returns list of {title, id, count}.
    """
    struct = state.get("outline_struct", {}) or {}
    points: List[Point] = state.get("points", []) or []
    # Count points per chapter title
    cnt_by_title: Dict[str, int] = {}
    for p in points:
        cnt_by_title[p.chapter] = cnt_by_title.get(p.chapter, 0) + 1
    out: List[Dict[str, Any]] = []
    try:
        for ch in struct.get("chapters", []) or []:
            title = ch.get("title", "")
            out.append({"title": title, "id": ch.get("id", ""), "count": cnt_by_title.get(title, 0)})
    except Exception:
        pass
    # Fallback if struct missing
    if not out:
        seen = set()
        for p in points:
            if p.chapter not in seen:
                out.append({"title": p.chapter, "id": "", "count": cnt_by_title.get(p.chapter, 0)})
                seen.add(p.chapter)
    return out


def _group_points_by_chapter(points: List[Point]) -> Dict[str, List[Point]]:
    by: Dict[str, List[Point]] = {}
    for p in points or []:
        by.setdefault(p.chapter, []).append(p)
    return by


def select_chapters_node(state: WorkState) -> WorkState:
    chapters = _collect_chapters_in_order(state)
    titles = [c.get("title", "") for c in chapters]
    selected: List[str] = titles[:]  # default all
    if _isatty() and chapters:
        print("\n—— 可生成章节 ——")
        for i, ch in enumerate(chapters, 1):
            print(f"  {i}. {ch.get('title','')}  (知识点: {ch.get('count',0)})")
        s = ask("请输入要生成的章节编号(逗号分隔，留空为全部)", default="")
        s = (s or "").strip()
        if s:
            try:
                idxs = [int(x.strip()) for x in s.split(',') if x.strip().isdigit()]
                selected = [chapters[i-1]["title"] for i in idxs if 1 <= i <= len(chapters)]
                if not selected:
                    selected = titles[:]
            except Exception:
                selected = titles[:]
    return {**state, "selected_chapters": selected}


async def generate_and_review_by_chapter_node(state: WorkState, llm_generate: _AsyncLLM, llm_review: _AsyncLLM) -> WorkState:
    """结构感知的生成与审查（外层并行）：
    - 章节：并行处理（仅受全局并发限流影响）；章节之间不共享正文上下文。
    - 小节：同章内并行处理；小节之间不共享正文上下文。
    - 组内（小节内）：
        * pipeline：严格串行，使用“续写式”Prompt，注入组内累积上下文。
        * toolbox：分阶段并行（根→派生），派生节点注入父级上下文；独立节点使用模板Prompt。
    - 审查：按小节并行审查，同小节内部提供 peers 列表，不跨小节/章节传递。
    """
    cfg = state.get("config", {})
    max_parallel = int(cfg.get("max_parallel_requests", 8))
    retries = int(cfg.get("retry_times", 3))
    delay = int(cfg.get("retry_delay", 10))
    sem = asyncio.Semaphore(max_parallel)

    outline = state.get("outline_struct", {}) or {}
    topic = state.get("topic", "")
    language = str((state.get("topic_meta", {}) or {}).get("lang", "zh"))

    # Build path mapping id -> readable breadcrumb path
    path_by_id: Dict[str, str] = {}
    chapters_struct = outline.get("chapters") or []
    for ci, ch in enumerate(chapters_struct, start=1):
        ch_title = ch.get("title", f"第{ci}章")
        for gi, gr in enumerate(ch.get("groups") or [], start=1):
            gr_title = gr.get("title", f"{ci}.{gi} 小节")
            for si, sec in enumerate(gr.get("sections") or [], start=1):
                sid = sec.get("id") or ""
                stitle = sec.get("title") or f"{ci}.{gi}.{si}"
                if sid:
                    path_by_id[sid] = f"{topic} / 第{ci}章：{ch_title} / {gr_title} / {stitle}"

    # Selection handling
    chapters_ordered = _collect_chapters_in_order(state)
    selected_titles = state.get("selected_chapters") or [c.get("title", "") for c in chapters_ordered]

    # Autosave dirs
    topic_slug = state.get("topic_slug", "topic")
    out_dir = BASE_DIR / "output" / topic_slug
    drafts_dir = out_dir / "drafts"
    reviews_dir = out_dir / "reviews"
    ensure_dir(drafts_dir)
    ensure_dir(reviews_dir)

    drafts_all: List[Dict[str, str]] = []
    reviews_all: List[Dict[str, Any]] = []
    failures_all: List[Dict[str, Any]] = []

    async def _process_one_group(ci: int, gi: int, ch: Dict[str, Any], gr: Dict[str, Any]) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        ch_title = ch.get("title", f"第{ci}章")
        gr_title = gr.get("title", f"{ci}.{gi} 小节")
        stype = str(gr.get("structure_type", "toolbox")).strip().lower()
        sections = gr.get("sections") or []
        if not sections:
            return [], [], []

        logger.info(f"  └─ 小节：{gr_title} 结构={stype}，知识点={len(sections)}")

        group_drafts: Dict[str, str] = {}
        # Generation
        if stype == "pipeline":
            group_context = ""
            for si, sec in enumerate(sections, start=1):
                sid = sec.get("id") or ""
                stitle = sec.get("title") or f"{ci}.{gi}.{si}"
                primary_goal = sec.get("primary_goal") or sec.get("goal") or ""
                mods = sec.get("suggested_modules") if isinstance(sec.get("suggested_modules"), list) else []
                prompt = _build_contextual_content_prompt(
                    topic=topic,
                    language=language,
                    path=path_by_id.get(sid, ""),
                    section_title=stitle,
                    primary_goal=str(primary_goal),
                    suggested_modules=mods if isinstance(mods, list) else [],
                    structure_type="pipeline",
                    relation_to_previous=str(sec.get("relation_to_previous") or ""),
                    prior_context=group_context,
                )
                async with sem:
                    txt = await _gen_one_point(llm_generate, prompt, retries, delay)
                # Sanitize Mermaid blocks if enabled
                if cfg.get("sanitize_mermaid", True):
                    txt_s, _issues = sanitize_mermaid_in_markdown(txt or "")
                    try:
                        changed_blocks = sum(int(x.get("changed", 0)) for x in _issues)
                        if changed_blocks:
                            logger.debug(f"[Sanitize] {sid}: fixed {changed_blocks} mermaid block(s) before review (pipeline)")
                    except Exception:
                        pass
                else:
                    txt_s = txt or ""
                group_drafts[sid] = txt_s
                if txt_s:
                    group_context = (group_context + "\n\n" + txt_s).strip()
                try:
                    (drafts_dir / f"{sid}.md").write_text(txt_s, encoding="utf-8")
                except Exception:
                    pass
        else:
            indices = list(range(len(sections)))
            def _rel(i: int) -> str:
                return str((sections[i] or {}).get("relation_to_previous", "")).strip().lower()

            roots = [i for i in indices if _rel(i) in {"first_in_sequence", "tool_in_toolbox", "alternative_to", ""}]
            pending = [i for i in indices if i not in roots]

            async def _gen_root(i: int):
                sec = sections[i]
                sid = sec.get("id") or ""
                stitle = sec.get("title") or ""
                primary_goal = sec.get("primary_goal") or sec.get("goal") or ""
                mods = sec.get("suggested_modules") if isinstance(sec.get("suggested_modules"), list) else []
                base = _build_contextual_content_prompt(
                    topic=topic,
                    language=language,
                    path=path_by_id.get(sid, ""),
                    section_title=stitle,
                    primary_goal=str(primary_goal),
                    suggested_modules=mods,
                    structure_type="toolbox",
                    prior_context="",
                )
                async with sem:
                    txt = await _gen_one_point(llm_generate, base, retries, delay)
                if cfg.get("sanitize_mermaid", True):
                    txt_s, _issues = sanitize_mermaid_in_markdown(txt or "")
                    try:
                        changed_blocks = sum(int(x.get("changed", 0)) for x in _issues)
                        if changed_blocks:
                            logger.debug(f"[Sanitize] {sid}: fixed {changed_blocks} mermaid block(s) before review (root)")
                    except Exception:
                        pass
                else:
                    txt_s = txt or ""
                group_drafts[sid] = txt_s
                try:
                    (drafts_dir / f"{sid}.md").write_text(txt_s, encoding="utf-8")
                except Exception:
                    pass

            if roots:
                await asyncio.gather(*[_gen_root(i) for i in roots])

            produced_set = set([sections[i].get("id") for i in roots])
            loop_guard = 0
            while pending and loop_guard < len(sections) * 2:
                ready: List[int] = []
                for i in list(pending):
                    dep = _rel(i)
                    if dep not in {"builds_on", "deep_dive_into"}:
                        ready.append(i)
                        continue
                    parent_idx = i - 1
                    if parent_idx >= 0:
                        parent_id = sections[parent_idx].get("id")
                        if parent_id in produced_set:
                            ready.append(i)
                if not ready:
                    ready = pending[:]

                async def _gen_dep(i: int):
                    sec = sections[i]
                    sid = sec.get("id") or ""
                    stitle = sec.get("title") or ""
                    primary_goal = sec.get("primary_goal") or sec.get("goal") or ""
                    mods = sec.get("suggested_modules") if isinstance(sec.get("suggested_modules"), list) else []
                    parent_txt = ""
                    if i - 1 >= 0:
                        parent_id = sections[i-1].get("id") or ""
                        parent_txt = group_drafts.get(parent_id, "")
                    prompt = _build_contextual_content_prompt(
                        topic=topic,
                        language=language,
                        path=path_by_id.get(sid, ""),
                        section_title=stitle,
                        primary_goal=str(primary_goal),
                        suggested_modules=mods,
                        structure_type="toolbox",
                        relation_to_previous=_rel(i),
                        prior_context=parent_txt,
                    )
                    async with sem:
                        txt = await _gen_one_point(llm_generate, prompt, retries, delay)
                    if cfg.get("sanitize_mermaid", True):
                        txt_s, _issues = sanitize_mermaid_in_markdown(txt or "")
                        try:
                            changed_blocks = sum(int(x.get("changed", 0)) for x in _issues)
                            if changed_blocks:
                                logger.debug(f"[Sanitize] {sid}: fixed {changed_blocks} mermaid block(s) before review (dep)")
                        except Exception:
                            pass
                    else:
                        txt_s = txt or ""
                    group_drafts[sid] = txt_s
                    try:
                        (drafts_dir / f"{sid}.md").write_text(txt_s, encoding="utf-8")
                    except Exception:
                        pass

                await asyncio.gather(*[_gen_dep(i) for i in ready])
                for i in ready:
                    produced_set.add(sections[i].get("id"))
                    if i in pending:
                        pending.remove(i)
                loop_guard += 1

        # Reviews for this group (optional)
        group_reviews: List[Dict[str, Any]] = []
        if not cfg.get("skip_content_review", False):
            peer_meta = [{"id": sec.get("id"), "title": sec.get("title")} for sec in sections if sec.get("id")]
            async def _review_one_for_group(sec: Dict[str, Any]) -> Dict[str, Any]:
                pid = sec.get("id") or ""
                peers = [pm for pm in peer_meta if (pm.get("id") or "") != pid]
                content = group_drafts.get(pid, "")
                async with sem:
                    rv = await _review_one_point_with_context(llm_review, pid, content, peers)
                try:
                    (reviews_dir / f"{pid}.json").write_text(json.dumps(rv, ensure_ascii=False, indent=2), encoding="utf-8")
                except Exception:
                    pass
                return rv

            group_reviews = await asyncio.gather(*[_review_one_for_group(sec) for sec in sections if sec.get("id")])
        # Collect for this group
        drafts_list = []
        for sec in sections:
            sid = sec.get("id") or ""
            if sid:
                drafts_list.append({"id": sid, "content": group_drafts.get(sid, "")})
        failures_list = []
        for rv in group_reviews:
            if _severity_score(rv) >= 3:
                failures_list.append({"id": rv.get("file_id"), "review": rv})
        return drafts_list, group_reviews, failures_list

    async def _process_one_chapter(ci: int, ch: Dict[str, Any]) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        ch_title = ch.get("title", f"第{ci}章")
        if selected_titles and ch_title not in selected_titles:
            return [], [], []
        logger.info(f"[结构感知] 处理章节：《{ch_title}》 …")
        groups = ch.get("groups") or []
        tasks = [
            _process_one_group(ci, gi, ch, gr)
            for gi, gr in enumerate(groups, start=1)
            if (gr.get("sections") or [])
        ]
        if not tasks:
            return [], [], []
        results = await asyncio.gather(*tasks)
        drafts_list: List[Dict[str, str]] = []
        reviews_list: List[Dict[str, Any]] = []
        failures_list: List[Dict[str, Any]] = []
        for d, r, f in results:
            drafts_list.extend(d)
            reviews_list.extend(r)
            failures_list.extend(f)
        return drafts_list, reviews_list, failures_list

    # Fire all chapters in parallel (filtered by selection)
    chapter_tasks = [
        _process_one_chapter(ci, ch)
        for ci, ch in enumerate(chapters_struct, start=1)
    ]
    if chapter_tasks:
        chapter_results = await asyncio.gather(*chapter_tasks)
        for d, r, f in chapter_results:
            drafts_all.extend(d)
            reviews_all.extend(r)
            failures_all.extend(f)

    return {**state, "drafts": drafts_all, "reviews": reviews_all, "failures": failures_all}


async def propose_and_apply_fixes_node(state: WorkState, llm: _AsyncLLM) -> WorkState:
    """在审查后针对非 OK 知识点生成修复提案。
    - 支持根据分类与改动特征自动应用安全更改（可配置）。
    - 对其余项目在交互环境中逐条征询；非交互环境下仅记录提案。
    """
    cfg_in = state.get("config", {}) or {}
    if cfg_in.get("skip_fixes", False):
        logger.info("已跳过修复提案与自动应用（--skip-fixes）")
        return {**state, "fix_proposals": [], "fix_applied": [], "fix_skipped": [], "fix_iterations": []}
    # 合并自动应用默认配置
    cfg: Dict[str, Any] = {**AUTO_APPLY_DEFAULTS, **cfg_in}
    max_rounds = int(cfg.get("max_fix_rounds", 3))

    topic = state.get("topic", "")
    outline_md = state.get("outline_final_md", "")

    # 索引 drafts 与 reviews
    draft_by_id: Dict[str, str] = {d.get("id", ""): d.get("content", "") for d in (state.get("drafts") or [])}
    reviews_in = state.get("reviews", []) or []
    reviews_by_id: Dict[str, Dict[str, Any]] = {}
    for rv in reviews_in:
        rid = str(rv.get("file_id") or rv.get("id") or "").strip()
        if not rid:
            continue
        reviews_by_id[rid] = rv

    # 用于展示标题
    title_by_id: Dict[str, str] = {p.id: p.title for p in (state.get("points") or [])}

    fix_proposals: List[Dict[str, Any]] = []
    fix_applied: List[str] = []
    fix_skipped: List[str] = []
    fix_iterations: List[Dict[str, Any]] = []
    auto_stats = {
        "mode": cfg.get("auto_apply_mode"),
        "applied": 0,
        "skipped": 0,
        "reasons": [],  # list of strings for debugging
    }

    # 非 OK 的目标集合
    target_ids = [pid for pid, rv in reviews_by_id.items() if _has_non_ok(rv)]
    # Debug：统计非OK原因分布（is_perfect=false / issues内容）
    try:
        non_ok_details = []
        for pid in target_ids:
            rv = reviews_by_id.get(pid, {})
            perf = rv.get('is_perfect')
            issues = rv.get('issues') if isinstance(rv.get('issues'), list) else []
            non_ok_details.append({
                'id': pid,
                'is_perfect': perf,
                'issues_cnt': len(issues),
                'sample': (issues[0] if issues else {})
            })
        logger.debug(f"[Fix.scan] 非OK统计: total={len(target_ids)} examples={non_ok_details[:3]}")
    except Exception:
        pass
    if not target_ids:
        return {**state, "fix_proposals": [], "fix_applied": [], "fix_skipped": [], "fix_iterations": []}

    logger.info(f"发现 {len(target_ids)} 个需要修复的知识点（任一维度非 OK）。")
    if (cfg.get("auto_apply_mode") or "off") != "off":
        logger.info(
            f"自动应用策略开启: mode={cfg.get('auto_apply_mode')} | major_threshold={cfg.get('auto_apply_threshold_major', 0.8)}"
        )

    # 一次性划分：自动应用集合 vs 待批量确认集合
    auto_ids: List[str] = []
    pending_ids: List[str] = []
    auto_reasons: Dict[str, str] = {}
    for pid in target_ids:
        rv = reviews_by_id.get(pid, {})
        ok, why = _should_auto_apply_by_review(cfg, rv)
        if ok:
            auto_ids.append(pid)
            auto_reasons[pid] = why
        else:
            pending_ids.append(pid)

    logger.info(f"自动应用候选: {len(auto_ids)}；待确认: {len(pending_ids)}")

    # 并发生成修复并自动应用
    sem_apply = asyncio.Semaphore(int(cfg.get("max_parallel_requests", 8)))

    async def _gen_and_apply(pid: str, auto_flag: bool, reason: str = ""):
        title = title_by_id.get(pid, pid)
        current = draft_by_id.get(pid, "")
        review = reviews_by_id.get(pid, {})
        async with sem_apply:
            proposal = await _propose_fix(llm, pid, title, topic, outline_md, current, review)
        new_md = proposal.get("revised_content", current)
        draft_by_id[pid] = new_md
        fix_applied.append(pid)
        fix_iterations.append({"id": pid, "iterations": 1})
        if auto_flag:
            auto_stats["applied"] += 1
            auto_stats["reasons"].append(f"{pid}: {reason}")
        fix_proposals.append({"id": pid, "title": title, **proposal, "applied": True, "iterations": 1, "auto_applied": auto_flag, **({"auto_reason": reason} if auto_flag else {})})

    if auto_ids:
        await asyncio.gather(*[_gen_and_apply(pid, True, auto_reasons.get(pid, "")) for pid in auto_ids])

    # 待确认部分：一次性展示并批量确认
    if pending_ids:
        print("\n—— 待确认的审查项（批量）——")
        for pid in pending_ids[:200]:
            title = title_by_id.get(pid, pid)
            issues = reviews_by_id.get(pid, {}).get("issues")
            cnt = len(issues) if isinstance(issues, list) else 0
            # 汇总 severities
            majors = sum(1 for it in (issues or []) if isinstance(it, dict) and str(it.get("severity", "")).lower()=="major") if isinstance(issues, list) else 0
            print(f"- {pid} | {title} | 问题数: {cnt} | major: {majors}")

        apply_pending = False
        if _isatty():
            apply_pending = ask_yes_no(f"是否对以上 {len(pending_ids)} 个条目批量应用 AI 修复?", default=True)
        if apply_pending:
            await asyncio.gather(*[_gen_and_apply(pid, False) for pid in pending_ids])
        else:
            fix_skipped.extend(pending_ids)

    # 将 draft_by_id 写回 drafts 列表
    out_drafts = []
    for d in (state.get("drafts") or []):
        pid = d.get("id", "")
        if pid in draft_by_id:
            out_drafts.append({"id": pid, "content": draft_by_id[pid]})
        else:
            out_drafts.append(d)

    return {
        **state,
        "drafts": out_drafts,
        "fix_proposals": fix_proposals,
        "fix_applied": fix_applied,
        "fix_skipped": fix_skipped,
        "fix_iterations": fix_iterations,
        "auto_apply_stats": auto_stats,
    }

def save_and_publish_node(state: WorkState) -> WorkState:
    topic_slug = state.get("topic_slug", "topic")
    out_dir = CONTENT_ROOT / topic_slug
    ensure_dir(out_dir)
    publish_paths: List[str] = []
    cfg = state.get("config", {}) or {}
    fname_style = str(cfg.get("filename_style", "id")).strip().lower()
    title_by_id: Dict[str, str] = {p.id: p.title for p in (state.get("points") or [])}
    for item in state.get("drafts", []) or []:
        pid = item.get("id", "")
        content = item.get("content", "")
        if cfg.get("sanitize_mermaid", True):
            content, _issues = sanitize_mermaid_in_markdown(content)
            try:
                changed_blocks = sum(int(x.get("changed", 0)) for x in _issues)
                if changed_blocks:
                    logger.debug(f"[Sanitize] {pid}: fixed {changed_blocks} mermaid block(s) before publish")
            except Exception:
                pass
        name = _make_filename(pid, title_by_id.get(pid, ""), fname_style)
        p = out_dir / name
        try:
            p.write_text(content, encoding="utf-8")
            publish_paths.append(str(p.relative_to(BASE_DIR)))
            logger.info(f"已保存: {p}")
        except Exception as e:
            logger.error(f"保存失败 {p}: {e}")
    # 另外保存大纲 Markdown 到 /public/content/<topic_slug>/ 下，命名为 <topic_slug>-learning-path.md
    outline_md = state.get("outline_final_md", "")
    if outline_md:
        outline_dir = CONTENT_ROOT / topic_slug
        ensure_dir(outline_dir)
        outline_path = outline_dir / f"{topic_slug}-learning-path.md"
        try:
            outline_path.write_text(outline_md, encoding="utf-8")
            publish_paths.append(str(outline_path.relative_to(BASE_DIR)))
            logger.info(f"大纲已保存: {outline_path}")
        except Exception as e:
            logger.error(f"保存大纲失败 {outline_path}: {e}")
    return {**state, "publish_paths": publish_paths}

def gather_and_report_node(state: WorkState) -> WorkState:
    # 去重：保留每个文件ID的最后一次审查结果
    reviews_in = state.get("reviews", []) or []
    reviews_by_id: Dict[str, Dict[str, Any]] = {}
    for rv in reviews_in:
        rid = str(rv.get("file_id") or rv.get("id") or "").strip()
        if not rid:
            continue
        reviews_by_id[rid] = rv

    # 统计：严格失败（旧逻辑）与“任一维度非 OK”的数量
    failures_unique: List[Dict[str, Any]] = []
    non_ok_ids: List[str] = []
    for rid, rv in reviews_by_id.items():
        if _severity_score(rv) >= 3:
            failures_unique.append({"id": rid, "review": rv})
        if _has_non_ok(rv):
            non_ok_ids.append(rid)

    ok_cnt = len(reviews_by_id) - len(non_ok_ids)
    topic_slug = state.get("topic_slug", "topic")

    # 汇总修复提案与处理情况
    fix_proposals = state.get("fix_proposals", []) or []
    fix_applied = set(state.get("fix_applied", []) or [])
    fix_skipped = set(state.get("fix_skipped", []) or [])
    title_by_id: Dict[str, str] = {p.id: p.title for p in (state.get("points") or [])}

    report = [
        f"# 生成与审查报告（{topic_slug}）",
        "",
        f"- 总计生成: {len(reviews_by_id)}",
        f"- 通过（全OK）: {ok_cnt}",
        f"- 需修复（任一维度非OK）: {len(non_ok_ids)}",
        "",
        "## 失败项（旧阈值，供参考）",
    ]
    for f in failures_unique:
        rid = f.get("id")
        rv = f.get("review", {})
        report.append(f"- {rid}: {json.dumps(rv, ensure_ascii=False)}")

    # 修复与处理情况
    if fix_proposals:
        report.append("")
        report.append("## 修复与处理情况")
        for fp in fix_proposals:
            rid = fp.get("id", "")
            title = fp.get("title", "")
            applied = fp.get("applied", False)
            iterations = fp.get("iterations", 1)
            summary = fp.get("summary", "")
            status = "已应用" if applied else ("已跳过" if rid in fix_skipped else "未应用")
            auto_flag = "(自动)" if fp.get("auto_applied") else ""
            report.append(f"- {rid} | {title} | {status}{auto_flag} | 轮次: {iterations} | 摘要: {summary}")

    # 待处理项（未生成提案但标记为跳过）
    if fix_skipped:
        proposed_ids = {fp.get("id", "") for fp in fix_proposals}
        skipped_only = [rid for rid in fix_skipped if rid not in proposed_ids]
        if skipped_only:
            report.append("")
            report.append("## 待处理项（未应用）")
            for rid in skipped_only:
                title = title_by_id.get(rid, rid)
                report.append(f"- {rid} | {title}")

    # 自动应用统计
    auto_stats = state.get("auto_apply_stats", {}) or {}
    if auto_stats:
        report.append("")
        report.append("## 自动应用统计")
        report.append(f"- 模式: {auto_stats.get('mode')}")
        report.append(f"- 自动应用: {auto_stats.get('applied', 0)}")
        report.append(f"- 自动跳过: {auto_stats.get('skipped', 0)}")
        reasons = auto_stats.get("reasons") or []
        if reasons:
            report.append("")
            report.append("<details><summary>调试原因（前10条）</summary>")
            for r in reasons[:10]:
                report.append(f"- {r}")
            report.append("</details>")

    report_md = "\n".join(report)
    # 写出报告
    out = BASE_DIR / f"pipeline_report_{topic_slug}.md"
    try:
        out.write_text(report_md, encoding="utf-8")
        logger.info(f"报告已写出: {out}")
    except Exception:
        pass
    return {**state, "report_md": report_md}


# ----------------------------
# Build graph
# ----------------------------

def build_graph(default_llm: _AsyncLLM, cfg: Dict[str, Any], registry: Dict[str, _AsyncLLM], args: argparse.Namespace):
    graph = StateGraph(WorkState)

    # Wrap nodes that need external params
    graph.add_node("topic_input", topic_input_node)

    def _pick(node: str, subrole: Optional[str] = None) -> _AsyncLLM:
        return select_llm_for_node(cfg, registry, node, subrole) or default_llm

    async def _gen_slug(s: WorkState) -> WorkState:
        return await generate_slug_node(s, _pick("generate_slug"))
    graph.add_node("generate_slug", _gen_slug)

    async def _gen_outline(s: WorkState) -> WorkState:
        return await generate_outline_node(s, _pick("generate_outline"))
    graph.add_node("generate_outline", _gen_outline)

    # Chapter selection and chapter-wise generation+review
    graph.add_node("select_chapters", select_chapters_node)

    async def _gen_review_by_chapter(s: WorkState) -> WorkState:
        return await generate_and_review_by_chapter_node(
            s,
            _pick("generate_and_review_by_chapter", "generate"),
            _pick("generate_and_review_by_chapter", "review"),
        )
    graph.add_node("generate_and_review_by_chapter", _gen_review_by_chapter)

    async def _propose_and_apply(s: WorkState) -> WorkState:
        return await propose_and_apply_fixes_node(s, _pick("propose_and_apply_fixes", "propose"))
    graph.add_node("propose_and_apply_fixes", _propose_and_apply)

    graph.add_node("save_and_publish", save_and_publish_node)
    graph.add_node("gather_and_report", gather_and_report_node)

    # Edges
    graph.add_edge(START, "topic_input")
    graph.add_edge("topic_input", "generate_slug")
    graph.add_edge("generate_slug", "generate_outline")
    graph.add_edge("generate_outline", "select_chapters")
    graph.add_edge("select_chapters", "generate_and_review_by_chapter")
    graph.add_edge("generate_and_review_by_chapter", "propose_and_apply_fixes")
    graph.add_edge("propose_and_apply_fixes", "save_and_publish")
    graph.add_edge("save_and_publish", "gather_and_report")
    graph.add_edge("gather_and_report", END)

    # Optional checkpointer for future interactive runs
    if MemorySaver is not None:
        try:
            return graph.compile(checkpointer=MemorySaver())
        except Exception:
            pass
    return graph.compile()



# ----------------------------
# CLI
# ----------------------------

def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Full LangGraph knowledge pipeline")
    ap.add_argument("--topic", type=str, help="主题（泛化到任意知识领域）", default=os.environ.get("TOPIC", ""))
    ap.add_argument("--topic-meta", type=str, help="JSON 字符串，包含 audience/depth/lang/extra", default=os.environ.get("TOPIC_META", ""))
    ap.add_argument("--config", type=str, help="配置文件路径", default=str(CONFIG_JSON if CONFIG_JSON.exists() else CONFIG_EXAMPLE_JSON))
    ap.add_argument("--provider", type=str, help="API 提供方: openai_compat|deepseek|gemini", default="openai_compat")
    ap.add_argument("--max-parallel", type=int, help="并行上限（覆盖配置）", default=None)
    ap.add_argument("--output-subdir", type=str, help="输出子目录（默认 topic slug）", default=None)
    ap.add_argument("--debug", action="store_true", help="开启调试模式（输出极其详细的日志，并写入 output/<slug>/pipeline.debug.log）")
    # Auto-apply controls
    ap.add_argument("--auto-apply-mode", type=str, choices=["off", "safe", "aggressive", "all"], default=None, help="自动应用模式：off|safe|aggressive|all")
    # 旧参数已移除：categories/allow-code/max-added/min-confidence
    ap.add_argument("--auto-apply-threshold-major", type=float, default=None, help="aggressive 模式下对 major 的最低信心阈值（默认 0.8）")

    # Skips
    ap.add_argument("--skip-outline-review", action="store_true", help="跳过大纲 Stage4 LLM 审阅")
    ap.add_argument("--skip-content-review", action="store_true", help="跳过知识点审查（更快）")
    ap.add_argument("--skip-fixes", action="store_true", help="跳过修复提案与自动应用")
    ap.add_argument("--no-sanitize-mermaid", action="store_true", help="禁用 Mermaid 语法规范化修复（默认开启）")
    return ap.parse_args()


def main() -> None:
    args = _parse_args()
    cfg = _load_config(args.config)
    # debug 开关：通过参数触发，也可在 config.json 中覆盖（args 优先）
    cfg["debug"] = bool(getattr(args, "debug", False) or cfg.get("debug", False))
    if args.provider:
        cfg["api_provider"] = args.provider
    if args.max_parallel:
        cfg["max_parallel_requests"] = int(args.max_parallel)
    # Auto-apply config overrides
    if getattr(args, "auto_apply_mode", None) is not None:
        cfg["auto_apply_mode"] = args.auto_apply_mode
    if getattr(args, "auto_apply_threshold_major", None) is not None:
        cfg["auto_apply_threshold_major"] = float(args.auto_apply_threshold_major)

    # Skips
    if getattr(args, "skip_outline_review", False):
        cfg["skip_outline_review"] = True
    if getattr(args, "skip_content_review", False):
        cfg["skip_content_review"] = True
    if getattr(args, "skip_fixes", False):
        cfg["skip_fixes"] = True
    if getattr(args, "no_sanitize_mermaid", False):
        cfg["sanitize_mermaid"] = False

    # Build LLM registry
    default_llm = init_llm(cfg)
    registry = build_llm_registry(cfg)

    # Initial state
    topic_slug = slugify(args.topic) if args.topic else "topic"
    output_subdir = args.output_subdir or topic_slug
    initial_state: WorkState = {
        "topic": args.topic or os.environ.get("TOPIC", ""),
        "topic_meta": (json.loads(args.topic_meta) if args.topic_meta else {}),
        "topic_slug": topic_slug,
        "config": cfg,
        "output_subdir": output_subdir,
    }

    # 若开启 Debug，追加独立 debug 文件句柄并提升日志等级
    _enable_debug_logging(cfg.get("debug", False), output_subdir)

    app = build_graph(default_llm, cfg, registry, args)

    # Visualize
    try:
        print("\n📊 ASCII Graph:")
        try:
            print(app.draw_ascii())
        except Exception:
            # Fallback for versions exposing draw_* on underlying graph
            print(app.get_graph().draw_ascii())
        print("\n📊 Mermaid:")
        try:
            print(app.draw_mermaid())
        except Exception:
            print(app.get_graph().draw_mermaid())
    except Exception:
        pass

    print("\n🚀 Running full pipeline...")
    # Provide default thread_id to satisfy checkpointer requirements
    run_config = {"configurable": {"thread_id": f"full:{output_subdir}"}}
    try:
        final_state: WorkState = asyncio.run(app.ainvoke(initial_state, config=run_config))  # type: ignore
    except Exception:
        final_state = app.invoke(initial_state, config=run_config)

    print("\n✅ 完成。报告如下：\n")
    print(final_state.get("report_md", "(无报告)"))


if __name__ == "__main__":
    main()
