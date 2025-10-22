#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
最小可行的 LangGraph 流水线：使用 Gemini 推荐全球经典教材；使用 Kimi 并行检索教材目录（TOC）。

步骤
- recommend_textbooks（Gemini）：给定学科主题，输出全球经典教材的 JSON 列表。
- fetch_kimi_tocs（Kimi）：对前 N 本教材进行联网检索，返回完整目录（并行执行）。

配置
- 使用项目根目录的 config.json 管理 LLM 配置与密钥：
  - Gemini：优先读取 llms 中配置的条目，默认键为 'gemini-2.5-pro'；可回退到环境变量 GOOGLE_API_KEY。
  - Kimi：优先读取 llms 中配置的条目，默认键为 'kimi-k2'；可回退到 MOONSHOT_API_KEY/KIMI_API_KEY。

运行
  python scripts/pipelines/langgraph/textbook_toc_pipeline_langgraph.py \
    --subject "量子力学" --top-n 3 --expected-content "偏向中文NLP与预训练模型实践"

依赖
  pip install -U langgraph google-generativeai openai

注意
- 关键错误（如 Gemini 返回无法解析为 JSON）直接抛出并终止。
- Kimi 阶段按教材逐本隔离：单本失败记录错误但不影响其他书目。
 - 若提供 `--expected-content`，将用于引导“推荐教材”阶段（Gemini）尽量选择更契合学习者期望的经典教材或版本。
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import re
import sys
from dataclasses import dataclass
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

# --- 依赖导入（若缺失给出友好提示） ---
try:
    from langgraph.graph import StateGraph, START, END
except Exception:
    sys.stderr.write(
        "[错误] 未找到 langgraph。请先安装:\n  python3 -m pip install -U langgraph\n"
    )
    raise SystemExit(1)

try:
    import google.generativeai as genai
except Exception:
    sys.stderr.write(
        "[错误] 未找到 google-generativeai。请先安装:\n  python3 -m pip install -U google-generativeai\n"
    )
    raise SystemExit(1)

try:
    from openai import OpenAI
except Exception:
    sys.stderr.write(
        "[错误] 未找到 openai SDK。请先安装:\n  python3 -m pip install -U openai\n"
    )
    raise SystemExit(1)


# --- 配置读取工具 ---
def _find_repo_root() -> Path:
    p = Path(__file__).resolve()
    for parent in [p] + list(p.parents):
        if (parent / "config.json").exists():
            return parent
    return Path(__file__).resolve().parents[-1]

BASE_DIR = _find_repo_root()
CONFIG_PATH = BASE_DIR / "config.json"


def _load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise SystemExit(f"[错误] 未找到配置文件: {CONFIG_PATH}")
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        raise SystemExit(f"[错误] 解析配置文件失败: {e}")


def _slugify(text: str, fallback: str = "subject") -> str:
    t = (
        text.replace("（", "(").replace("）", ")").replace("—", "-")
        .strip()
    )
    t = re.sub(r"[^0-9A-Za-z\-_.\s]", "", t)
    t = re.sub(r"\s+", "-", t)
    t = t.strip("-_.").lower()
    return t or fallback


@dataclass
class GeminiConfig:
    model: str
    api_key: str


@dataclass
class KimiConfig:
    model: str
    api_key: str
    base_url: str


@dataclass
class DeepseekConfig:
    model: str
    api_key: str
    base_url: str


def _pick_llm_key_by_provider(cfg: Dict[str, Any], provider: str) -> Optional[str]:
    llms = cfg.get("llms") or {}
    for k, v in llms.items():
        if str(v.get("provider", "")).lower().startswith(provider):
            return k
    return None


def load_gemini_config(cfg: Dict[str, Any], key_hint: Optional[str]) -> GeminiConfig:
    llms = cfg.get("llms") or {}
    key = key_hint or ("gemini-2.5-pro" if "gemini-2.5-pro" in llms else _pick_llm_key_by_provider(cfg, "gemini"))
    if not key or key not in llms:
        raise SystemExit("[错误] config.json 缺少 Gemini 配置项 (llms). 可指定 --gemini-llm-key")
    entry = llms[key]
    api_key = entry.get("api_key") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise SystemExit("[错误] 未配置 Gemini API Key。请在 config.json 或设置 GOOGLE_API_KEY。")
    model = entry.get("model") or key
    return GeminiConfig(model=model, api_key=api_key)


def load_kimi_config(cfg: Dict[str, Any], key_hint: Optional[str]) -> KimiConfig:
    llms = cfg.get("llms") or {}
    key = key_hint or ("kimi-k2" if "kimi-k2" in llms else _pick_llm_key_by_provider(cfg, "openai_compat"))
    if not key or key not in llms:
        raise SystemExit("[错误] config.json 缺少 Kimi 配置项 (llms)。可指定 --kimi-llm-key")
    entry = llms[key]
    api_key = entry.get("api_key") or os.environ.get("MOONSHOT_API_KEY") or os.environ.get("KIMI_API_KEY")
    if not api_key:
        raise SystemExit("[错误] 未配置 Kimi API Key。请在 config.json 或设置 MOONSHOT_API_KEY/KIMI_API_KEY。")
    model = entry.get("model") or "kimi-k2-turbo-preview"
    base_url = entry.get("base_url") or "https://api.moonshot.cn/v1"
    # 修正明显的 URL 拼写错误（例如 'hhttps://' → 'https://')
    base_url = re.sub(r"^hhttps://", "https://", base_url)
    return KimiConfig(model=model, api_key=api_key, base_url=base_url)


def load_deepseek_config(cfg: Dict[str, Any], key_hint: Optional[str]) -> DeepseekConfig:
    """从 config.json 读取 DeepSeek 配置；默认键 deepseek-chat。

    - 支持从 llms 条目读取 api_key/base_url/model。
    - 回退到环境变量：DEEPSEEK_API_KEY / DEEPSEEK_BASE_URL。
    - 若 base_url 未带 /v1，自动补全。
    """
    llms = cfg.get("llms") or {}
    key = key_hint or ("deepseek-chat" if "deepseek-chat" in llms else _pick_llm_key_by_provider(cfg, "deepseek"))
    if not key or key not in llms:
        raise SystemExit("[错误] config.json 缺少 DeepSeek 配置项 (llms)。可指定 --deepseek-llm-key 或配置 llms.deepseek-chat")
    entry = llms[key]
    api_key = (
        entry.get("api_key")
        or entry.get("deepseek_api_key")
        or os.environ.get("DEEPSEEK_API_KEY")
    )
    if not api_key:
        raise SystemExit("[错误] 未配置 DeepSeek API Key。请在 config.json 或设置 DEEPSEEK_API_KEY。")
    base_url = (
        entry.get("base_url")
        or entry.get("deepseek_base_url")
        or os.environ.get("DEEPSEEK_BASE_URL")
        or "https://api.deepseek.com"
    )
    # 规范化 base_url，确保包含 /v1 前缀
    base_url = re.sub(r"^hhttps://", "https://", base_url)
    if not re.search(r"/v1/?$", base_url):
        base_url = base_url.rstrip("/") + "/v1"
    model = entry.get("model") or "deepseek-chat"
    return DeepseekConfig(model=model, api_key=api_key, base_url=base_url)


def _prompt_from_catalog(key: str, default_text: str) -> str:
    try:
        from prompts.prompt_loader import get_prompt
        return get_prompt(key, default_text)
    except Exception:
        return default_text


def _parse_json_str(text: str) -> Any:
    """最小 JSON 解析：支持一次代码块围栏回退（```json ... ```）。"""
    text = (text or "").strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    # 尝试解析代码围栏：```json ... ``` 或通用 ``` ... ```
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE)
    if m:
        frag = (m.group(1) or "").strip()
        return json.loads(frag)
    raise ValueError("响应内容不是有效的 JSON。")


# --- 状态定义 ---
class PipelineState(TypedDict, total=False):
    subject: str
    subject_slug: str
    top_n: int
    max_parallel: int
    gemini: GeminiConfig
    kimi: KimiConfig
    expected_content: str
    print_prompt: bool
    recommendations: List[Dict[str, Any]]
    tocs: List[Dict[str, Any]]


# --- 流水线节点 ---
def generate_subject_slug(state: PipelineState) -> PipelineState:
    """使用轻量模型为 subject 生成英文 kebab-case slug。

    - 默认模型：deepseek-chat（参考 config.json 中 llms.deepseek-chat）。
    - 当 LLM 调用失败或输出异常时，先回退 Gemini（若可用），再回退本地 _slugify(subject, "subject").
    """
    logger = logging.getLogger(__name__)
    subject = str(state.get("subject") or "").strip()
    if not subject:
        return {**state, "subject_slug": _slugify("", "subject")}

    # 清洗函数：只保留 a-z0-9-，合并重复 -，去除首尾 -
    def _clean_slug(s: str) -> str:
        s = (s or "").strip().lower()
        s = re.sub(r"[^a-z0-9\-]+", "", s)
        s = re.sub(r"-+", "-", s).strip("-")
        return s

    # 优先调用 DeepSeek（openai 兼容），失败则尝试 Gemini flash，再失败回退本地
    tmpl = _prompt_from_catalog(
        "toc.slug",
        "你的任务是为一个给定的主题生成一个简洁、全小写、URL友好、用连字符分隔（kebab-case）的英文 slug。\n\n"
        "约束：\n"
        "1. 只包含英文字母、数字和连字符'-'。\n"
        "2. 如果主题是中文或其他语言，请先将其翻译或音译为有意义的英文。\n"
        "3. 结果必须简短且具有描述性。\n\n"
        "主题: \"计算机网络原理\"\n"
        "Slug: computer-network-principles\n\n"
        "主题: \"八字算命\"\n"
        "Slug: bazi-divination\n\n"
        "主题: \"[subject]\"\n"
        "只输出 slug，不要任何解释或标点：",
    )
    prompt = tmpl.replace("[subject]", subject)

    final_slug: str
    # 1) DeepSeek 尝试
    try:
        cfg = _load_config()
        ds_cfg = load_deepseek_config(cfg, None)
        client = OpenAI(base_url=ds_cfg.base_url, api_key=ds_cfg.api_key)
        resp = client.chat.completions.create(
            model=ds_cfg.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs only short slugs in lowercase kebab-case."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=64,
        )
        raw = (resp.choices[0].message.content or "") if (resp and resp.choices) else ""
        slug = _clean_slug(raw)
        final_slug = slug or _slugify(subject, "subject")
    except Exception as e:
        logger.warning("DeepSeek 生成 slug 失败，尝试 Gemini：%s", e)
        # 2) Gemini 尝试（使用轻量 flash）
        try:
            gem_cfg: GeminiConfig = state["gemini"]
            genai.configure(api_key=gem_cfg.api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            resp = model.generate_content(prompt)
            raw = getattr(resp, "text", "")
            slug = _clean_slug(raw)
            final_slug = slug or _slugify(subject, "subject")
        except Exception as e2:
            logger.warning("Gemini 备选生成 slug 失败，回退本地规则：%s", e2)
            final_slug = _slugify(subject, "subject")

    logger.info("生成 Slug: %s -> %s", subject, final_slug)
    new_state = dict(state)
    new_state["subject_slug"] = final_slug
    return new_state  # type: ignore
def recommend_textbooks(state: PipelineState) -> PipelineState:
    logger = logging.getLogger(__name__)
    subject = state["subject"]
    expected = (state.get("expected_content") or "").strip()
    gem_cfg: GeminiConfig = state["gemini"]

    genai.configure(api_key=gem_cfg.api_key)
    model = genai.GenerativeModel(gem_cfg.model)

    if expected:
        logger.info("[1/2] 调用 Gemini 推荐教材 … 模型=%s 主题=%s | 学习者期望已提供", gem_cfg.model, subject)
    else:
        logger.info("[1/2] 调用 Gemini 推荐教材 … 模型=%s 主题=%s", gem_cfg.model, subject)
    prompt_tmpl = _prompt_from_catalog(
        "toc.recommend",
        "你是资深课程设计专家。请基于全球范围内的经典/权威/广泛采用的教材，推荐与主题“[subject]”最相关的教材。\n\n"
        "如果提供了学习者的特定期望或偏好，请在不偏离“全球经典/权威”前提下，优先选择更契合这些期望的教材或版本（如更适合某语种学习、包含某类章节、偏向某些应用/任务等）。\n\n"
        "输出要求：严格 JSON，且只输出以下结构：\n"
        "{\n"
        "  \"textbooks\": [\n"
        "    {\n"
        "      \"title\": \"书名\",\n"
        "      \"authors\": [\"作者1\", \"作者2\"],\n"
        "      \"edition\": \"版次或年份版\",\n"
        "      \"publisher\": \"出版社\",\n"
        "      \"year\": 2020,\n"
        "      \"isbn13\": \"可选\",\n"
        "      \"official_url\": \"可选，出版社或课程官网\"\n"
        "    }\n"
        "  ]\n"
        "}\n\n"
        "约束：\n"
        "- 仅输出 JSON，不要附带解释或 Markdown。\n"
        "- 关注“全球经典教材”，优先列出高影响力版本（如英文原版）。\n"
        "- 一共推荐5本，优先推荐最相关的3本教材，按相关度降序输出。\n",
    )
    prompt = prompt_tmpl.replace("[subject]", subject)
    if expected:
        prompt = prompt + "\n" + ("学习者期望：\n- " + expected + "\n")

    if state.get("print_prompt"):
        print("========== DEBUG: Gemini Prompt Begin ==========", file=sys.stderr)
        print(prompt, file=sys.stderr)
        print("=========== DEBUG: Gemini Prompt End ===========", file=sys.stderr)
    resp = model.generate_content(prompt)
    text = getattr(resp, "text", "")
    data = _parse_json_str(text)
    if not isinstance(data, dict) or "textbooks" not in data:
        raise ValueError("Gemini 返回的 JSON 不含 textbooks 字段。")

    recs = data.get("textbooks") or []
    if not isinstance(recs, list) or not recs:
        raise ValueError("Gemini 未返回教材列表。")

    top_n = int(state.get("top_n", 3) or 3)
    recs = recs[:top_n]
    logger.info("Gemini 推荐教材共 %d 本，取前 %d 本。", len(data.get("textbooks", [])), len(recs))
    new_state = dict(state)
    new_state["recommendations"] = recs
    return new_state  # type: ignore


def _kimi_chat_once(client: OpenAI, model: str, messages: List[Dict[str, Any]]):
    return client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.6,
        max_tokens=32768,
        tools=[
            {
                "type": "builtin_function",
                "function": {"name": "$web_search"},
            }
        ],
    )


def _fetch_one_toc(kimi_cfg: KimiConfig, book: Dict[str, Any], print_prompt: bool = False) -> Dict[str, Any]:
    logger = logging.getLogger(__name__)
    client = OpenAI(base_url=kimi_cfg.base_url, api_key=kimi_cfg.api_key)
    sys_prompt = _prompt_from_catalog(
        "kimi.system",
        "你是 Kimi，具备联网搜索能力。请使用内置 $web_search 工具检索并返回指定教材的完整目录。严格输出 JSON，不要解释或 Markdown。",
    )
    title = str(book.get("title", "")).strip()
    authors = ", ".join(book.get("authors", []) or [])
    publisher = str(book.get("publisher", "")).strip()
    ask_tmpl = _prompt_from_catalog(
        "kimi.user",
        "请检索并返回这本教材的完整目录输出时务必按照类似以下格式进行输出，具体到每个章节下的小节，保留原有层级与顺序：\n"
        "## 第1章：LangGraph入门\n"
        "### 1.1 核心概念\n"
        "#### 1.1.1 什么是 LangGraph? (解决什么问题)\n"
        "#### 1.1.2 State (状态): 图的记忆\n"
        "#### 1.1.3 Nodes (节点): 工作单元\n"
        "#### 1.1.4 Edges (边): 连接流程\n"
        "### 1.2 第一个 LangGraph 应用\n"
        "#### 1.2.1 定义 StateGraph\n"
        "#### 1.2.2 添加节点 (Nodes)\n"
        "#### 1.2.3 设置入口和出口 (Entry/Finish Point)\n"
        "#### 1.2.4 编译与运行 (compile, stream)\n\n"
        "## 第2章：构建动态流程 \n"
        "### 2.1 条件分支\n"
        "#### 2.1.1 条件边的使用\n"
        "#### 2.1.2 实现一个简单的路由 Agent\n"
        "### 2.2 循环与迭代\n"
        "#### 2.2.1 在图中创建循环\n"
        "#### 2.2.2 案例: 多轮问答或自我修正\n"
        "只输出以下 JSON 对象：{\n"
        "  \"book\": {\"title\": string, \"authors\": [string], \"publisher\": string},\n"
        "  \"toc\": [string 或 对象，按原始目录顺序],\n"
        "  \"source\": string\n"
        "}\n"
        "目标教材: 《[title]》 [authors] · [publisher]",
    )
    ask = (
        ask_tmpl
        .replace("[title]", title)
        .replace("[authors]", authors)
        .replace("[publisher]", publisher)
    )
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": ask},
    ]

    if print_prompt:
        try:
            print("========== DEBUG: Kimi System Prompt Begin ==========", file=sys.stderr)
            print(sys_prompt, file=sys.stderr)
            print("=========== DEBUG: Kimi System Prompt End ===========", file=sys.stderr)
            print("========== DEBUG: Kimi User Prompt Begin ==========", file=sys.stderr)
            print(ask, file=sys.stderr)
            print("=========== DEBUG: Kimi User Prompt End ===========", file=sys.stderr)
        except Exception:
            pass

    finish_reason = None
    choice = None
    try:
        logger.info("开始检索目录: 《%s》 (%s)", title or "", (authors or publisher or ""))
        while finish_reason is None or finish_reason == "tool_calls":
            comp = _kimi_chat_once(client, kimi_cfg.model, messages)
            choice = comp.choices[0]
            finish_reason = choice.finish_reason
            if finish_reason == "tool_calls":
                messages.append(choice.message)
                for tool_call in choice.message.tool_calls:
                    name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                    if name == "$web_search":
                        tool_result = args  # 按 Kimi 文档：将工具调用参数原样回传
                    else:
                        tool_result = {"error": f"unknown tool: {name}"}
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": name,
                        "content": json.dumps(tool_result, ensure_ascii=False),
                    })
        content = choice.message.content if choice else ""
        data = _parse_json_str(content)
        if isinstance(data, dict):
            # 确保至少包含基本的书目信息字段
            if "book" not in data:
                data["book"] = {
                    "title": title,
                    "authors": book.get("authors", []) or [],
                    "publisher": publisher,
                }
            data.setdefault("source", "")
            logger.info("完成目录获取: 《%s》", title or "")
            return data
        else:
            logger.warning("目录 JSON 解析为非对象：书名=《%s》", title or "")
            return {
                "book": {
                    "title": title,
                    "authors": book.get("authors", []) or [],
                    "publisher": publisher,
                },
                "raw": content,
                "error": "Kimi 返回非对象 JSON",
            }
    except Exception as e:
        logger.error("目录检索失败: 《%s》, 错误=%s", title or "", e)
        return {
            "book": {
                "title": title,
                "authors": book.get("authors", []) or [],
                "publisher": publisher,
            },
            "error": f"Kimi 查询失败: {e}",
        }


def fetch_kimi_tocs(state: PipelineState) -> PipelineState:
    logger = logging.getLogger(__name__)
    kimi_cfg: KimiConfig = state["kimi"]
    recs: List[Dict[str, Any]] = state.get("recommendations", []) or []
    max_parallel = int(state.get("max_parallel", 4) or 4)
    if not recs:
        raise ValueError("没有教材推荐，无法执行 Kimi TOC 查询。")

    logger.info("[2/2] 并行检索教材目录 … 并行度=%d，待检索=%d 本", max_parallel, len(recs))
    results: List[Dict[str, Any]] = []
    with cf.ThreadPoolExecutor(max_workers=max_parallel) as executor:
        future_map = {executor.submit(_fetch_one_toc, kimi_cfg, b, bool(state.get("print_prompt"))): b for b in recs}
        for f in cf.as_completed(future_map):
            book = future_map[f]
            title = (book or {}).get("title", "")
            try:
                res = f.result()
                results.append(res)
                if res.get("error"):
                    logger.warning("完成但有错误: 《%s》 -> %s", title, res.get("error"))
                else:
                    logger.info("完成: 《%s》 (目录获取成功)", title)
            except Exception as e:
                logger.error("任务异常: 《%s》 -> %s", title, e)
                results.append({"book": {"title": title}, "error": f"并行任务失败: {e}"})

    new_state = dict(state)
    new_state["tocs"] = results
    return new_state  # type: ignore


# --- 构建 LangGraph ---
def build_graph():
    g = StateGraph(PipelineState)
    g.add_node("generate_subject_slug", generate_subject_slug)
    g.add_node("recommend_textbooks", recommend_textbooks)
    g.add_node("fetch_kimi_tocs", fetch_kimi_tocs)
    g.add_edge(START, "generate_subject_slug")
    g.add_edge("generate_subject_slug", "recommend_textbooks")
    g.add_edge("recommend_textbooks", "fetch_kimi_tocs")
    g.add_edge("fetch_kimi_tocs", END)
    return g.compile()


def main():
    parser = argparse.ArgumentParser(description="Gemini 推荐教材 + Kimi 并行检索目录 (LangGraph)")
    parser.add_argument("--subject", required=True, help="主题，例如：计算机网络、微观经济学")
    parser.add_argument("--top-n", type=int, default=3, help="获取目录的教材数量")
    parser.add_argument("--max-parallel", type=int, default=5, help="Kimi 并行查询上限")
    parser.add_argument("--gemini-llm-key", type=str, default=None, help="config.json.llms 中 Gemini 的 key，例如 gemini-2.5-pro")
    parser.add_argument("--kimi-llm-key", type=str, default=None, help="config.json.llms 中 Kimi 的 key，例如 kimi-k2")
    parser.add_argument("--expected-content", type=str, default=None, help="学习者期望（可选，用于引导推荐阶段的侧重）")
    parser.add_argument("--out", type=str, default=None, help="输出 JSON 文件路径，可选")
    parser.add_argument("--print-prompt", action="store_true", help="打印推荐与检索阶段的完整 Prompt 以便调试")
    args = parser.parse_args()

    # 终端日志输出配置
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger(__name__)

    cfg = _load_config()
    gem_cfg = load_gemini_config(cfg, args.gemini_llm_key)
    kimi_cfg = load_kimi_config(cfg, args.kimi_llm_key)

    logger.info(
        "启动教材目录生成流水线 | 主题=%s | top_n=%d | 并行度=%d | Gemini=%s | Kimi=%s",
        args.subject, args.top_n, args.max_parallel, gem_cfg.model, kimi_cfg.model,
    )

    app = build_graph()
    logger.info("LangGraph 已构建，开始执行 …")
    init_state: PipelineState = {
        "subject": args.subject,
        "top_n": max(1, int(args.top_n)),
        "max_parallel": max(1, int(args.max_parallel)),
        "gemini": gem_cfg,
        "kimi": kimi_cfg,
        "expected_content": (args.expected_content or "").strip(),
        "print_prompt": bool(args.print_prompt),
    }

    final_state = app.invoke(init_state)

    # 汇总并写出结果
    out = {
        "subject": args.subject,
        "subject_slug": final_state.get("subject_slug") or _slugify(args.subject, "subject"),
        "top_n": init_state["top_n"],
        "expected_content": init_state.get("expected_content") or "",
        "recommendations": final_state.get("recommendations", []),
        "tocs": final_state.get("tocs", []),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = BASE_DIR / "output" / "textbook_tocs"
        out_dir.mkdir(parents=True, exist_ok=True)
        slug = out.get("subject_slug") or _slugify(args.subject, "subject")
        out_path = out_dir / f"{slug}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"

    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    # 终端摘要信息
    logger.info("[完成] 输出文件: %s", out_path)
    recs = final_state.get("recommendations", []) or []
    logger.info("推荐教材: %d 本 (展示前 %d 本)", len(recs), min(3, len(recs)))
    for i, b in enumerate(recs[:3], 1):
        logger.info("  %d. %s", i, b.get('title', '(no title)'))
    tocs = final_state.get("tocs", []) or []
    ok = sum(1 for t in tocs if not t.get("error"))
    logger.info("目录获取成功: %d/%d", ok, len(tocs))


if __name__ == "__main__":
    main()
