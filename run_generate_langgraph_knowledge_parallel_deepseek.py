#!/usr/bin/env python3
"""
LangGraph 学习知识并行生成脚本（LangGraph 编排 + DeepSeek API）

特性:
- 使用 LangGraph 进行流程编排（加载大纲 -> 并行生成 -> 完成）。
- 通过 DeepSeek（OpenAI 兼容）异步客户端并发生成内容。
- 从 web-learner/public/langgraph-learning-path.md 读取大纲。
- 输出到 web-learner/public/content 下（每个知识点一个 .md 文件）。

依赖:
  pip install -U openai langgraph tqdm

配置:
- 优先读取命令行指定的 --config，默认 config.example.json
- 需要提供 DeepSeek API Key
  - 环境变量 DEEPSEEK_API_KEY
  - 或配置文件中的 deepseek_api_key
  - base_url 默认为 https://api.deepseek.com
  - model 默认为 deepseek-chat（或根据需要改为 deepseek-reasoner）
"""

from __future__ import annotations

import os
import re
import json
import argparse
import asyncio
import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path
from tqdm.asyncio import tqdm_asyncio

# LangGraph 导入（若未安装给出友好提示）
try:
    from langgraph.graph import StateGraph, START, END
except Exception:
    raise SystemExit(
        "[错误] 未找到 langgraph。请先安装:\n"
        "  python3 -m pip install -U langgraph\n"
    )


# --- 日志设置 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('langgraph_generation_parallel_deepseek_log.txt', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# --- 数据结构 ---
@dataclass
class KnowledgePoint:
    id: str
    title: str
    level: int
    chapter: str
    section: str


class LangGraphKnowledgeGeneratorDeepSeek:
    def __init__(self, config_path: str = "config.example.json") -> None:
        self.base_dir = Path(__file__).parent.resolve()
        self.config = self._load_config(config_path)

        # 输入大纲
        outline_md = self.base_dir / 'web-learner' / 'public' / 'langgraph-learning-path.md'
        self.outline_content, self.knowledge_points = self._load_points_from_md(outline_md)

        # 输出目录（注意：要求写入到 public/content 根目录）
        self.output_dir = self.base_dir / 'web-learner' / 'public' / 'content'
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 初始化 DeepSeek OpenAI 兼容异步客户端
        self.client = None
        self._init_async_client()
        # 小节前缀过滤（如 {'3-1'} -> 匹配 lg-sec-3-1-*）
        self.group_prefix_filter: Optional[set[str]] = None

    # --- 配置与客户端 ---
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        default_config = {
            "api_provider": "deepseek",
            "deepseek_api_key": os.environ.get("DEEPSEEK_API_KEY") or "YOUR_DEEPSEEK_API_KEY_HERE",
            "deepseek_base_url": "https://api.deepseek.com",
            "model": "deepseek-reasoner",
            "temperature": 0.6,
            "max_tokens": 4096,
            "retry_times": 3,
            "retry_delay": 10,
            "max_parallel_requests": 8,
        }

        path = Path(config_path)
        if path.exists():
            try:
                user_cfg = json.loads(path.read_text(encoding='utf-8'))
                default_config.update(user_cfg)
            except Exception:
                logger.warning(f"配置文件 {config_path} 读取失败或格式错误，将使用默认配置。")
        else:
            path.write_text(json.dumps(default_config, ensure_ascii=False, indent=2), encoding='utf-8')
            logger.info(f"已创建默认配置文件: {config_path}。请填入 DeepSeek API Key。")

        return default_config

    def _init_async_client(self) -> None:
        try:
            from openai import AsyncOpenAI
        except Exception:
            logger.error("缺少 openai 库，请先安装: pip install openai")
            return

        api_key = self.config.get("deepseek_api_key") or os.environ.get("DEEPSEEK_API_KEY")
        if not api_key or "YOUR_DEEPSEEK_API_KEY_HERE" in api_key:
            logger.error("DeepSeek API Key 未设置。请在 config 或环境变量 (DEEPSEEK_API_KEY) 中配置。")
            return

        base_url = self.config.get("deepseek_base_url", "https://api.deepseek.com")
        # DeepSeek 的 OpenAI 兼容接口应可与标准 OpenAI SDK 使用 base_url 配置
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    # --- 大纲解析 ---
    def _load_points_from_md(self, md_path: Path) -> Tuple[str, List[KnowledgePoint]]:
        content = ""
        try:
            content = md_path.read_text(encoding='utf-8')
        except FileNotFoundError:
            logger.error(f"错误：找不到大纲文件 {md_path}。")
            return "", []

        points: List[KnowledgePoint] = []
        current_chapter = ""
        current_section = ""

        for line in content.splitlines():
            m_ch = re.search(r"## 第(\d+)章：(.+?) \(id: (lg-ch-\d+)\)", line)
            if m_ch:
                current_chapter = m_ch.group(2).strip()
                continue

            m_sec = re.search(r"### ([\d\.]+?) (.+?) \(id: (lg-gr-[\d\-]+)\)", line)
            if m_sec:
                current_section = m_sec.group(2).strip()
                continue

            m_pt = re.search(r"#### ([\d\.]+?) (.+?) \(id: (lg-sec-[\d\-a-z_]+)\)", line)
            if m_pt:
                points.append(
                    KnowledgePoint(
                        id=m_pt.group(3),
                        title=m_pt.group(2),
                        level=line.count('#'),
                        chapter=current_chapter,
                        section=current_section,
                    )
                )

        logger.info(f"成功从 {md_path} 加载了 {len(points)} 个知识点。")
        return content, points

    # --- Prompt ---
    def _build_prompt(self, point: KnowledgePoint) -> str:
        return f"""
你是一名顶级的软件架构师和 LangGraph 专家，擅长用模块化、可复现的代码来解释复杂的工作流。
你的任务是为 LangGraph 学习路径中的一个特定知识点生成详细的教学内容（Markdown格式）。

1) 当前知识点信息:
- 标题: {point.title}
- ID: {point.id}
- 所属章节: {point.chapter}
- 所属小节: {point.section}

2) 整体学习大纲上下文:
为了确保内容不重复且承上启下，请参考以下完整的 LangGraph 学习大纲。当前要生成的知识点是 {point.title}。
---
{self.outline_content}
---

3) 内容生成要求:
请严格按照以下Markdown结构生成内容。最关键的要求是：所有代码块都必须是完整、可独立运行的 LangGraph 应用，包含必要的 import、State 定义、节点函数、图构建与执行。

## {point.title}

### 🎯 核心概念
一句话说明这个知识点解决什么问题，为什么它是构建复杂 Agent 流程的关键。

### 💡 使用方式
给出核心 API 和基本用法，必要时附简短代码。

### 📚 Level 1: 基础认知（30秒理解）
提供一个最简单且完整可运行的代码示例（包含 import、state、nodes、graph、run）。
```python
# 完整、可运行的最小示例
```

### 📈 Level 2: 核心特性（深入理解）
展示 1-2 个关键特性或高级用法，每个特性配完整示例与说明。

#### 特性1: [特性名称]
```python
# 完整、可运行的代码示例
```

### 🔍 Level 3: 对比学习（避免陷阱）
如适用，通过“错误用法 vs 正确用法”展示常见陷阱。
```python
# 错误用法
# 正确用法
```

### 🚀 Level 4: 实战应用（真实场景）
设计一个实际场景，综合运用该知识点，提供完整可运行代码和预期输出说明。

### 💡 记忆要点
- 要点1
- 要点2
"""

    # --- LLM 调用（DeepSeek） ---
    async def _call_deepseek(self, prompt: str) -> Optional[str]:
        if self.client is None:
            logger.error("DeepSeek 客户端未初始化，请检查 openai 安装与 API Key 配置。")
            return None
        try:
            model = self.config.get("model", "deepseek-chat")
            temperature = self.config.get("temperature", 0.6)
            max_tokens = self.config.get("max_tokens", 4096)

            resp = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是经验丰富的中文技术讲解助手，擅长编写结构清晰、代码可运行的教学材料。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            if resp and resp.choices:
                return resp.choices[0].message.content
            return None
        except Exception as e:
            logger.error(f"DeepSeek API 调用失败: {e}")
            return None

    # --- 持久化 ---
    def _save_markdown(self, point: KnowledgePoint, content: str) -> None:
        path = self.output_dir / f"{point.id}.md"
        try:
            path.write_text(content, encoding='utf-8')
            rel = path.relative_to(self.base_dir)
            logger.info(f"✅ 已保存: {rel}")
        except Exception as e:
            logger.error(f"❌ 保存文件失败: {path}, 原因: {e}")

    # --- 并行生成一个知识点 ---
    async def _gen_one(self, point: KnowledgePoint, semaphore: asyncio.Semaphore, force: bool) -> str:
        path = self.output_dir / f"{point.id}.md"
        if not force and path.exists():
            return "skipped"

        async with semaphore:
            prompt = self._build_prompt(point)
            content: Optional[str] = None
            for _ in range(self.config.get("retry_times", 3)):
                content = await self._call_deepseek(prompt)
                if content:
                    break
                await asyncio.sleep(self.config.get("retry_delay", 10))

            if content:
                self._save_markdown(point, content)
                return "success"
            else:
                logger.error(f"❌ 多次尝试后仍未生成: {point.id} ({point.title})")
                return "failed"

    # --- LangGraph 节点函数 ---
    async def node_generate_all(self, state: Dict[str, Any]) -> Dict[str, Any]:
        force = bool(state.get("force", False))
        points: List[KnowledgePoint] = state.get("points", [])
        grp_prefixes = state.get("group_prefixes") or self.group_prefix_filter
        if grp_prefixes:
            prefixes = tuple(f"lg-sec-{pref}-" for pref in grp_prefixes)
            points = [p for p in points if p.id.startswith(prefixes)]
        if not points:
            logger.error("知识点列表为空，无法生成。")
            return {"results": []}

        max_parallel = int(self.config.get("max_parallel_requests", 8))
        sem = asyncio.Semaphore(max_parallel)

        tasks = [self._gen_one(p, sem, force) for p in points]
        results = await tqdm_asyncio.gather(*tasks, desc="生成进度")
        return {"results": results}


def build_graph(generator: LangGraphKnowledgeGeneratorDeepSeek):
    graph = StateGraph(dict)

    def node_load(state: Dict[str, Any]) -> Dict[str, Any]:
        return {"points": generator.knowledge_points, "group_prefixes": state.get("group_prefixes")}

    graph.add_node("load_outline", node_load)
    graph.add_node("generate_all", generator.node_generate_all)

    graph.add_edge(START, "load_outline")
    graph.add_edge("load_outline", "generate_all")
    graph.add_edge("generate_all", END)

    return graph.compile()


def main():
    parser = argparse.ArgumentParser(description="LangGraph 并行生成 LangGraph 学习内容（DeepSeek）")
    parser.add_argument("--config", default="config.example.json", help="配置文件路径")
    parser.add_argument("--force", action="store_true", help="强制覆盖已存在的文件")
    parser.add_argument("--max-parallel", type=int, help="覆盖配置中的最大并发数")
    parser.add_argument(
        "--group-prefixes",
        type=str,
        help="仅生成指定小节前缀（如 '3-1'，可逗号分隔）。匹配 id 前缀 lg-sec-3-1-*",
    )

    args = parser.parse_args()

    gen = LangGraphKnowledgeGeneratorDeepSeek(config_path=args.config)
    if args.max_parallel:
        gen.config["max_parallel_requests"] = args.max_parallel
        logger.info(f"命令行覆盖最大并发数: {args.max_parallel}")

    app = build_graph(gen)

    def _parse_group_prefixes(expr: Optional[str]):
        if not expr:
            return None
        vals = set()
        for tok in [t.strip() for t in expr.split(',') if t.strip()]:
            if re.fullmatch(r"\d+(?:-\d+){1,2}", tok):
                vals.add(tok)
            else:
                logger.warning(f"忽略无法解析的 group 前缀: {tok}")
        return vals or None

    grp = _parse_group_prefixes(args.group_prefixes)

    initial_state = {"force": bool(args.force), "group_prefixes": grp}

    # 异步执行（包含异步节点）
    asyncio.run(app.ainvoke(initial_state))


if __name__ == "__main__":
    main()
