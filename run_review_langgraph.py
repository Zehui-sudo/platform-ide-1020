"""
LangGraph-based agent team to review Markdown content.

Reimplements the logic from run_review_crew.py using LangGraph, avoiding CrewAI.

Pipeline:
1) Plan: Extract chapter numbers from `web-learner/public/javascript-learning-path.md`.
2) Review: For each chapter, read all chapter markdowns from `web-learner/public/content/`
   and have an LLM review per file into a structured JSON list.
3) Synthesize: Summarize structured findings into a final Markdown report.

Requirements (install if missing):
  pip install -U langgraph langchain langchain-google-genai

Environment/config:
- Reads `config.json` and uses `gemini_api_key` if `GOOGLE_API_KEY` is not set.
- Model defaults to `gemini-2.5-pro` and can be overridden by `config.json:model`.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, TypedDict, Annotated
import argparse
import asyncio
from operator import add

# Soft-imports with helpful error if missing
try:
    from langgraph.graph import StateGraph, START, END
except Exception as e:  # pragma: no cover
    sys.stderr.write(
        "[错误] 未找到 langgraph。请先安装：\n"
        "  python3 -m pip install -U langgraph\n"
    )
    raise

# Optional: langchain-google-genai. If missing or broken, we fallback to google-generativeai
try:
    from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore
    _LC_GENAI_AVAILABLE = True
    _LC_GENAI_IMPORT_ERR = None
except Exception as e:  # pragma: no cover
    ChatGoogleGenerativeAI = None  # type: ignore
    _LC_GENAI_AVAILABLE = False
    _LC_GENAI_IMPORT_ERR = e


# --- 0. 配置与模型初始化 ---

BASE_DIR = Path(__file__).parent.resolve()
CONFIG_PATH = BASE_DIR / "config.json"


def _load_config() -> Dict[str, Any]:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


cfg = _load_config()

# 优先使用环境变量，其次使用 config.json 的 gemini_api_key
if not os.environ.get("GOOGLE_API_KEY") and cfg.get("gemini_api_key"):
    os.environ["GOOGLE_API_KEY"] = cfg.get("gemini_api_key")

MODEL_NAME = cfg.get("model", "gemini-2.5-pro")
SHOW_PROMPTS = str(os.environ.get("SHOW_PROMPTS", "0")).lower() in {"1", "true", "yes", "on"}

def _init_llm():
    # Prefer langchain wrapper if available and not explicitly disabled
    if _LC_GENAI_AVAILABLE and str(os.environ.get("USE_NATIVE_GEMINI", "0")).lower() not in {"1","true","yes","on"}:
        try:
            return ChatGoogleGenerativeAI(model=MODEL_NAME)  # type: ignore
        except Exception as e:  # pragma: no cover
            sys.stderr.write(
                f"[警告] 初始化 ChatGoogleGenerativeAI 失败，切换到原生 google-generativeai。原因: {e}\n"
            )
    # Fallback: native google-generativeai client
    try:
        import google.generativeai as genai  # type: ignore
    except Exception:
        sys.stderr.write(
            "[错误] 未找到 google-generativeai。请安装：\n"
            "  python3 -m pip install -U google-generativeai\n"
        )
        # 同时提示潜在的 protobuf 兼容性方案
        if _LC_GENAI_IMPORT_ERR:
            sys.stderr.write(
                "此外，可尝试解决 protobuf 兼容性：\n"
                "  python3 -m pip install 'protobuf<5' 'googleapis-common-protos<2'\n"
            )
        raise SystemExit(1)

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        sys.stderr.write("[错误] 缺少 GOOGLE_API_KEY 环境变量或 config.json.gemini_api_key。\n")
        raise SystemExit(1)
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(MODEL_NAME)

    class _NativeLLM:
        def __init__(self, m):
            self._m = m

        def invoke(self, prompt: str):
            resp = self._m.generate_content(prompt)
            text = getattr(resp, "text", "") or "".join(
                getattr(resp, "candidates", []) and [
                    getattr(getattr(resp.candidates[0], "content", None), "parts", [])[0].text  # type: ignore
                ] or [""]
            )

            class R:
                def __init__(self, content: str):
                    self.content = content

            return R(text)

        async def ainvoke(self, prompt: str):
            # 在原生 SDK 上用线程池避免阻塞事件循环
            return await asyncio.to_thread(self.invoke, prompt)

    return _NativeLLM(model)


# 初始化Gemini模型（优先 langchain-google-genai，失败则回退到原生 SDK）
llm = _init_llm()

# 全局并发控制（默认 8，可用 MAX_PARALLEL_REVIEWS 覆盖）
MAX_PARALLEL = int(os.environ.get("MAX_PARALLEL_REVIEWS", "8") or "8")
_SEM = asyncio.Semaphore(MAX_PARALLEL)


# --- 1. 数据与工具 ---

LEARNING_PATH_FILE = BASE_DIR / "web-learner/public/javascript-learning-path.md"
CONTENT_DIR = BASE_DIR / "web-learner/public/content/"


def _read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception as e:
        return f"[读取失败] {p.name}: {e}"


def _extract_chapter_numbers_from_learning_path(md_text: str) -> List[str]:
    # 匹配形如 “第1章”、“第 2 章” 等，尽量鲁棒
    nums = re.findall(r"第\s*(\d+)\s*章", md_text)
    # 去重并按数字排序
    unique = sorted({int(n) for n in nums})
    return [str(n) for n in unique]


def _read_chapter_content(chapter_number: str) -> str:
    base_path = CONTENT_DIR
    all_files_content = ""
    prefix = f"js-sec-{chapter_number}-"
    try:
        for filename in sorted(os.listdir(base_path)):
            if filename.startswith(prefix) and filename.endswith(".md"):
                file_path = base_path / filename
                try:
                    content = file_path.read_text(encoding="utf-8")
                    all_files_content += (
                        f"--- START OF FILE: {filename} ---\n\n{content}\n\n--- END OF FILE: {filename}---\n\n"
                    )
                except Exception as e:
                    all_files_content += f"--- ERROR READING FILE: {filename} - {e}---\n"
        if not all_files_content:
            return f"没有找到章节 {chapter_number} 的文件，文件名前缀为 '{prefix}'。"
        return all_files_content
    except Exception as e:
        return f"访问目录 {base_path} 时出错: {e}"


def _list_chapter_files(chapter_number: str) -> List[Path]:
    prefix = f"js-sec-{chapter_number}-"
    files: List[Path] = []
    try:
        for filename in sorted(os.listdir(CONTENT_DIR)):
            if filename.startswith(prefix) and filename.endswith(".md"):
                files.append(CONTENT_DIR / filename)
    except Exception:
        return []
    return files


def _try_parse_json_list(text: str) -> List[Dict[str, Any]]:
    # 强力解析器：尽可能从文本中提取一个 JSON 数组
    text = text.strip()
    # 常见情况：包在代码块中
    if "```" in text:
        # 取出第一个代码块内容
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("[") and part.endswith("]"):
                try:
                    return json.loads(part)
                except Exception:
                    pass
    # 回退：在全文中寻找第一个 [ 与最后一个 ]
    try:
        start = text.index("[")
        end = text.rindex("]")
        return json.loads(text[start : end + 1])
    except Exception:
        return []


# --- 2. LangGraph 状态与节点 ---


class ReviewState(TypedDict, total=False):
    chapters: List[str]
    reviews: Annotated[List[Dict[str, Any]], add]
    report: str
    chapters_filter: List[str]
    current_chapter: str


def _apply_chapter_filter(all_chapters: List[str], filter_list: List[str]) -> List[str]:
    if not filter_list:
        return all_chapters
    filt = [c.strip() for c in filter_list if c and c.strip().isdigit()]
    allowed = set(filt)
    return [c for c in all_chapters if c in allowed]


def _infer_chapters_from_content_dir() -> List[str]:
    """当学习路径大纲缺失或无法识别章节时，从内容目录文件名推断章节号。"""
    chapters_set = set()
    try:
        for filename in sorted(os.listdir(CONTENT_DIR)):
            # 仅匹配形如 js-sec-7-... 的文件
            m = re.match(r"js-sec-(\d+)-", filename)
            if m and filename.endswith(".md"):
                try:
                    chapters_set.add(int(m.group(1)))
                except Exception:
                    pass
    except Exception:
        return []
    return [str(n) for n in sorted(chapters_set)]
    
def plan_node(state: ReviewState) -> ReviewState:
    print("\n🔎 [Plan] 读取课程大纲:", LEARNING_PATH_FILE)
    md_text = _read_text(LEARNING_PATH_FILE)
    chapters_all = _extract_chapter_numbers_from_learning_path(md_text)
    chapters_filter = state.get("chapters_filter", []) or []
    chapters = _apply_chapter_filter(chapters_all, chapters_filter)
    if chapters_filter:
        print("🎯 [Plan] 目标章节过滤:", ", ".join(chapters_filter))
        missing = [c for c in chapters_filter if c not in chapters_all]
        if missing:
            print("⚠️ [Plan] 过滤中包含未在大纲找到的章节:", ", ".join(missing))
    if chapters:
        print("✅ [Plan] 识别章节编号:", ", ".join(chapters))
    else:
        print("⚠️ [Plan] 未能从大纲中识别到章节编号。")
    return {**state, "chapters": chapters}


def dispatch_chapters(state: ReviewState):
    chapters = state.get("chapters", []) or []
    if not chapters:
        print("⚠️ [Dispatch] 无可用章节，跳过分发。")
        return state
    print(f"\n🚚 [Dispatch] 派发 {len(chapters)} 个章节进行并行审查...")
    return [Send("review_one", {"current_chapter": ch}) for ch in chapters]


async def review_one_chapter(state: ReviewState) -> ReviewState:
    ch = state.get("current_chapter", "")
    if not ch:
        return {}
    print(f"\n📚 [Review-One] 开始审查章节: {ch}")
    files = _list_chapter_files(ch)
    print(f"📂 [Review-One] 第{ch}章匹配到 {len(files)} 个文件")
    for f in files[:20]:
        print("  -", f.name)

    system_preamble = (
        "你是一位经验丰富的JavaScript专家和一丝不苟的技术编辑。"
        "请严格按照要求对文件进行审查，并仅输出符合规范的JSON数组。"
    )
    instruction = (
        "针对提供的章节号与该章节内的所有文件内容，逐个文件进行审查。\n\n"
        "【审查指令】\n"
        "1. 主题一致性: 检查内容是否与文件标题及其在课程体系中的位置相符。\n"
        "2. 内容独特性: 判断是否与其它部分应有的内容存在显著重叠。\n"
        "3. 质量保证: 示例是否清晰且正确，解释是否符合逻辑。\n\n"
        "【输出要求】\n"
        "- 仅输出一个 JSON 数组字符串，不要添加额外文本。\n"
        "- 数组中的每个对象必须包含键: \"file_name\", \"chapter\", \"topic_adherence_score\", \"topic_adherence_comment\", \"uniqueness_score\", \"uniqueness_comment\", \"quality_score\", \"quality_comment\"。\n"
        "- 所有分数字段的取值只能是: \"OK\"、\"Warning\"、\"Critical Error\"。\n"
    )

    content = _read_chapter_content(ch)
    prompt = (
        f"{system_preamble}\n\n"
        f"当前章节: {ch}\n\n"
        f"{instruction}\n"
        f"以下为该章节的所有文件内容（带有文件名边界标记）：\n\n"
        f"{content}\n"
        f"请生成 JSON 数组，确保每个对象包含文件名(来自边界标记)、章节号等字段。"
    )

    try:
        print(f"🧠 [Review-One] 向模型发送请求 → 第{ch}章 ...")
        if SHOW_PROMPTS:
            print("—" * 40)
            print("[Prompt - 第" + ch + "章]\n" + prompt)
            print("—" * 40)
        async with _SEM:
            if hasattr(llm, "ainvoke"):
                resp = await llm.ainvoke(prompt)  # type: ignore
            else:
                resp = await asyncio.to_thread(llm.invoke, prompt)  # type: ignore
        print("📥 [Review-One] 已收到模型响应，解析JSON...")
        text = getattr(resp, "content", str(resp))
        parsed = _try_parse_json_list(text)
        for item in parsed:
            item.setdefault("chapter", ch)
        if not parsed:
            sys.stderr.write(f"[警告] 第{ch}章审查结果解析失败，跳过或为空。\n")
        else:
            # 局部统计仅日志用途
            levels = {"OK": 0, "Warning": 0, "Critical Error": 0}
            for it in parsed:
                for k in ["topic_adherence_score","uniqueness_score","quality_score"]:
                    v = str(it.get(k, "")).strip()
                    if v in levels:
                        levels[v] += 1
            print(
                f"✅ [Review-One] 第{ch}章解析成功: {len(parsed)} 条记录 | "
                f"OK={levels['OK']} Warning={levels['Warning']} Critical={levels['Critical Error']}"
            )
        return {"reviews": parsed}
    except Exception as e:
        sys.stderr.write(f"[错误] 第{ch}章审查失败: {e}\n")
        return {"reviews": []}


async def review_parallel_node(state: ReviewState) -> ReviewState:
    """在单个 LangGraph 节点内并行审查所有章节（使用 asyncio.gather + Semaphore）。"""
    chapters = state.get("chapters", []) or []
    if not chapters:
        print("⚠️ [Review-Parallel] 未发现章节，跳过并行审查。")
        return {**state, "reviews": []}

    print(f"\n⚙️ [Review-Parallel] 准备并行处理 {len(chapters)} 个章节（并发上限={MAX_PARALLEL}）...")
    tasks = [review_one_chapter({"current_chapter": ch}) for ch in chapters]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    aggregated: List[Dict[str, Any]] = []
    for idx, res in enumerate(results):
        if isinstance(res, Exception):
            sys.stderr.write(f"[错误] 并行任务 {idx} 失败: {res}\n")
            continue
        if isinstance(res, dict):
            aggregated.extend(res.get("reviews", []))

    print(f"📊 [Review-Parallel] 并行完成，累计记录: {len(aggregated)}")
    return {**state, "reviews": aggregated}


def review_node(state: ReviewState) -> ReviewState:
    # 保留旧的串行实现以便回退或对比，不在主图中使用
    chapters = state.get("chapters", [])
    all_reviews: List[Dict[str, Any]] = []

    system_preamble = (
        "你是一位经验丰富的JavaScript专家和一丝不苟的技术编辑。"
        "请严格按照要求对文件进行审查，并仅输出符合规范的JSON数组。"
    )

    instruction = (
        "针对提供的章节号与该章节内的所有文件内容，逐个文件进行审查。\n\n"
        "【审查指令】\n"
        "1. 主题一致性: 检查内容是否与文件标题及其在课程体系中的位置相符。\n"
        "2. 内容独特性: 判断是否与其它部分应有的内容存在显著重叠。\n"
        "3. 质量保证: 代码示例是否清晰且正确，解释是否符合逻辑。\n\n"
        "【输出要求】\n"
        "- 仅输出一个 JSON 数组字符串，不要添加额外文本。\n"
        "- 数组中的每个对象必须包含键: \"file_name\", \"chapter\", \"topic_adherence_score\", \"topic_adherence_comment\", \"uniqueness_score\", \"uniqueness_comment\", \"quality_score\", \"quality_comment\"。\n"
        "- 所有分数字段的取值只能是: \"OK\"、\"Warning\"、\"Critical Error\"。\n"
    )

    def _count_severity(items: List[Dict[str, Any]]):
        levels = {"OK": 0, "Warning": 0, "Critical Error": 0}
        keys = [
            "topic_adherence_score",
            "uniqueness_score",
            "quality_score",
        ]
        for it in items:
            for k in keys:
                v = str(it.get(k, "")).strip()
                if v in levels:
                    levels[v] += 1
        return levels

    for ch in chapters:
        print("\n📚 [Review] 开始审查章节:", ch)
        files = _list_chapter_files(ch)
        print(f"📂 [Review] 第{ch}章匹配到 {len(files)} 个文件")
        for f in files[:20]:  # 避免控制台过长，只展示前20个
            print("  -", f.name)
        content = _read_chapter_content(ch)
        prompt = (
            f"{system_preamble}\n\n"
            f"当前章节: {ch}\n\n"
            f"{instruction}\n"
            f"以下为该章节的所有文件内容（带有文件名边界标记）：\n\n"
            f"{content}\n"
            f"请生成 JSON 数组，确保每个对象包含文件名(来自边界标记)、章节号等字段。"
        )

        try:
            print(f"🧠 [Review] 向模型发送请求 → 第{ch}章 ...")
            if SHOW_PROMPTS:
                print("—" * 40)
                print("[Prompt - 第" + ch + "章]\n" + prompt)
                print("—" * 40)
            resp = llm.invoke(prompt)
            print("📥 [Review] 已收到模型响应，解析JSON...")
            text = getattr(resp, "content", str(resp))
            parsed = _try_parse_json_list(text)
            # 强制填充 chapter 字段（若模型遗漏）
            for item in parsed:
                item.setdefault("chapter", ch)
            if not parsed:
                sys.stderr.write(f"[警告] 第{ch}章审查结果解析失败，跳过或为空。\n")
            else:
                sev = _count_severity(parsed)
                print(
                    f"✅ [Review] 第{ch}章解析成功: {len(parsed)} 条记录 | "
                    f"OK={sev['OK']} Warning={sev['Warning']} Critical={sev['Critical Error']}"
                )
            all_reviews.extend(parsed)
        except Exception as e:
            sys.stderr.write(f"[错误] 第{ch}章审查失败: {e}\n")

    # 汇总整体统计
    overall_levels = {"OK": 0, "Warning": 0, "Critical Error": 0}
    if all_reviews:
        sev = _count_severity(all_reviews)
        overall_levels.update(sev)
    print(
        f"\n📊 [Review] 全部章节汇总: {len(all_reviews)} 条记录 | "
        f"OK={overall_levels['OK']} Warning={overall_levels['Warning']} Critical={overall_levels['Critical Error']}"
    )

    return {**state, "reviews": all_reviews}


def synthesize_node(state: ReviewState) -> ReviewState:
    reviews = state.get("reviews", [])
    print("\n🧩 [Synthesize] 汇总审查数据:", len(reviews), "条")
    try:
        review_json = json.dumps(reviews, ensure_ascii=False)
    except Exception:
        review_json = "[]"

    prompt = (
        "你是一位总编辑。请基于下面严格结构化的JSON审查结果，"
        "生成一份人类可读、可操作的Markdown最终审计报告。\n\n"
        "报告必须包含：\n"
        "1. 执行摘要（总计文件数、严重问题数等统计）。\n"
        "2. 严重问题（列出所有评级为“严重错误”的发现）。\n"
        "3. 警告与建议（列出所有“警告”的发现和改进建议）。\n\n"
        f"以下是JSON数据：\n{review_json}\n\n"
        "只输出Markdown，不要包含其他说明。"
    )

    try:
        print("🧠 [Synthesize] 生成最终Markdown报告...")
        resp = llm.invoke(prompt)
        report_md = getattr(resp, "content", str(resp))
    except Exception as e:
        report_md = f"# 审计报告\n\n[错误] 生成报告失败：{e}"

    return {**state, "report": report_md}


def build_graph():
    graph = StateGraph(ReviewState)
    graph.add_node("plan", plan_node)
    graph.add_node("review_parallel", review_parallel_node)
    graph.add_node("review", review_node)  # 备用：不接入主链
    graph.add_node("synthesize", synthesize_node)

    graph.add_edge(START, "plan")
    graph.add_edge("plan", "review_parallel")
    graph.add_edge("review_parallel", "synthesize")
    graph.add_edge("synthesize", END)
    return graph.compile()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LangGraph Review Runner")
    parser.add_argument(
        "-c", "--chapters",
        help="逗号分隔的章节编号，如: 7 或 1,2,3。也可用环境变量 CHAPTERS=...",
        default=os.environ.get("CHAPTERS", ""),
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    chapters_filter: List[str] = []
    if args.chapters:
        chapters_filter = [s.strip() for s in str(args.chapters).split(",") if s.strip()]
    start_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("🚀 使用 LangGraph 启动内容审查团队...")
    print(f"🛠️ 配置: model={MODEL_NAME} | content_dir={CONTENT_DIR} | MAX_PARALLEL_REVIEWS={MAX_PARALLEL}")
    if chapters_filter:
        print(f"🎯 仅审查指定章节: {', '.join(chapters_filter)}")
    print("🗺️ 工作流: START → plan → review_parallel(并行) → synthesize → END")
    app = build_graph()

    # --- 可视化部分 ---
    try:
        print("\n📊 ASCII 图：")
        print(app.draw_ascii())
        print("\n📊 Mermaid 语法：")
        print(app.draw_mermaid())
    except Exception:
        # 某些版本不支持可视化导出，忽略
        pass
    
    print("🔧 图已编译，开始执行...")
    initial_state: ReviewState = {
        "chapters": [],
        "reviews": [],
        "report": "",
        "chapters_filter": chapters_filter,
    }
    try:
        final_state: ReviewState = asyncio.run(app.ainvoke(initial_state))  # type: ignore
    except Exception:
        final_state = app.invoke(initial_state)

    end_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"⏱️ 执行时间: {start_ts} → {end_ts}")
    print("\n\n✅ 团队工作完成！这是最终报告:\n")
    print("=" * 50)
    print(final_state.get("report", "(无报告)"))


if __name__ == "__main__":
    main()
