
#!/usr/bin/env python3
"""
Python知识点内容批量生成工具 (并行版)
根据 python-learning-path.md 中的结构，使用 asyncio 并行调用AI API生成所有知识点内容。

安装依赖:
pip install google-generativeai tqdm
"""

import os
import json
import time
import logging
import re
import asyncio
import argparse
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from tqdm.asyncio import tqdm_asyncio

# --- 日志设置 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('python_generation_parallel_log.txt', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class KnowledgePoint:
    """知识点数据结构"""
    id: str
    title: str
    level: int
    chapter: str
    section: str

class KnowledgeGenerator:
    """知识点内容并行生成器"""
    
    def __init__(self, config_path: str = "config.example.json"):
        """初始化生成器"""
        self.config = self.load_config(config_path)
        self.outline_content, self.knowledge_points = self.load_knowledge_points_from_md('web-learner/public/python-learning-path.md')
        self.output_dir = Path('web-learner/public/content/')
        self.output_dir.mkdir(exist_ok=True)
        
    def load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        default_config = {
            "api_provider": "gemini",
            "gemini_api_key": os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE"),
            "model": "gemini-1.5-pro-latest",
            "temperature": 0.6,
            "max_tokens": 4096,
            "retry_times": 3,
            "retry_delay": 10,
            "max_parallel_requests": 8  # 新增：最大并发请求数
        }
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                try:
                    user_config = json.load(f)
                    default_config.update(user_config)
                except json.JSONDecodeError:
                    logger.warning(f"配置文件 {config_path} 格式错误，将使用默认配置。")
        else:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            logger.info(f"已创建默认配置文件: {config_path}。请填入你的API Key。")
            
        return default_config

    def load_knowledge_points_from_md(self, md_path: str) -> Tuple[str, List[KnowledgePoint]]:
        """从Markdown大纲文件加载知识点"""
        points = []
        content = ""
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            logger.error(f"错误：找不到大纲文件 {md_path}。")
            return "", []

        lines = content.split('\n')
        current_chapter = ""
        current_section = ""
        
        for line in lines:
            chapter_match = re.search(r'## 第(\d+)章：(.+?) \(id: (py-ch-\d+)\)', line)
            if chapter_match:
                current_chapter = chapter_match.group(1)
                continue

            section_match = re.search(r'### ([\d\.]+?) (.+?) \(id: (py-gr-[\d\-]+)\)', line)
            if section_match:
                current_section = section_match.group(1)
                continue

            point_match = re.search(r'#### ([\d\.]+?) (.+?) \(id: (py-sec-[\d\-a-z_]+)\)', line)
            if point_match:
                point_id = point_match.group(3)
                title = point_match.group(2)
                level = line.count('#') - 1
                
                points.append(KnowledgePoint(
                    id=point_id,
                    title=title,
                    level=level,
                    chapter=current_chapter,
                    section=current_section
                ))
        
        logger.info(f"成功从 {md_path} 加载了 {len(points)} 个知识点。")
        return content, points

    def generate_prompt(self, point: KnowledgePoint) -> str:
        """为单个知识点生成高质量的prompt"""
        # (此函数与原脚本完全相同，此处省略以保持简洁)
        return f"""
你是一名顶级的Python教育专家，擅长以循序渐进、重点突出、生动有趣的方式讲解复杂的编程概念。
你的任务是为Python学习路径中的一个特定知识点生成详细的教学内容（Markdown格式）。

**1. 当前知识点信息:**
- **标题:** {point.title}
- **ID:** {point.id}

**2. 整体学习大纲上下文:**
为了确保内容不重复且承上启下，请参考以下完整的Python学习大纲。当前要生成的知识点是 **{point.title}**。
---
{self.outline_content}
---

**3. 内容生成要求:**
请严格按照以下Markdown结构生成内容，确保每个代码块都是完整、可独立运行的Python代码。

## {point.title}

### 🎯 核心概念
(用一句话说明这个知识点解决什么问题，为什么需要它。语言要精炼，直击要害。)

### 💡 使用方式
介绍这个知识点的具体使用方式

### 📚 Level 1: 基础认知（30秒理解）
(提供一个最简单、最直观的代码示例，让初学者一眼就能明白基本用法。代码必须完整可运行，并以注释的形式包含预期输出结果。)
```python
# 示例代码
```

### 📈 Level 2: 核心特性（深入理解）
(展示2-3个该知识点的关键特性或高级用法，每个特性配一个完整的代码示例和简要说明。)

#### 特性1: [特性名称]
(简要说明)
```python
# 示例代码
```

#### 特性2: [特性名称]
(简要说明)
```python
# 示例代码
```

### 🔍 Level 3: 对比学习（避免陷阱）
(通过对比“错误用法”和“正确用法”来展示常见的陷阱或易混淆的概念。每个用法都必须有完整的代码示例和清晰的解释。)

```python
# === 错误用法 ===
# ❌ 展示常见错误
# 解释为什么是错的

# === 正确用法 ===
# ✅ 展示正确做法
# 解释为什么这样是对的
```

### 🚀 Level 4: 实战应用（真实场景）
(设计一个生动有趣的实战场景来综合运用该知识点。场景要富有创意，例如游戏、科幻、生活趣事等，避免枯燥的纯理论或商业案例。代码需完整，并有清晰的输出结果。)

**场景：** [选择一个有趣的场景，如：🎮 游戏角色属性计算器, 🚀 星际飞船导航系统, 🍕 披萨订单处理器, 🐾 虚拟宠物互动等]

```python
# 实战场景的完整代码
```

### 💡 记忆要点
- **要点1**: [总结第一个关键记忆点]
- **要点2**: [总结第二个关键记忆点]
- **要点3**: [总结第三个关键记忆点]

**4. 内容风格要求:**
- **循序渐进**: 从最简单的概念到复杂的应用。
- **重点突出**: 使用加粗、列表等方式突出核心知识。
- **生动有趣**: Level 4的实战场景要富有想象力，使用Emoji增加趣味性。
- **代码可运行**: 所有代码块都必须是独立的、完整的、可以直接复制运行的。
- **中文讲解**: 所有解释和注释都使用中文。

请现在开始为知识点 **"{point.title}"** 生成内容。
"""

    async def call_gemini_api_async(self, prompt: str) -> Optional[str]:
        """异步调用Google Gemini API"""
        try:
            import google.generativeai as genai
        except ImportError:
            logger.error("Google GenerativeAI库未安装，请运行: pip install google-generativeai")
            return None

        try:
            api_key = self.config.get("gemini_api_key")
            if not api_key or "YOUR_GEMINI_API_KEY_HERE" in api_key:
                logger.error("Gemini API Key 未在配置文件中设置。")
                return None
            
            genai.configure(api_key=api_key)
            
            model = genai.GenerativeModel(
                model_name=self.config.get("model", "gemini-1.5-pro-latest"),
                generation_config={
                    "temperature": self.config.get("temperature", 0.6),
                    "max_output_tokens": self.config.get("max_tokens", 4096),
                }
            )
            
            response = await model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API调用失败: {e}")
            return None

    def save_content(self, point: KnowledgePoint, content: str):
        """保存生成的内容到文件"""
        filename = f"{point.id}.md"
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"✅ 已保存: {filepath.name}")
        except Exception as e:
            logger.error(f"❌ 保存文件失败: {filepath.name}, 原因: {e}")

    async def generate_one_point_async(self, point: KnowledgePoint, semaphore: asyncio.Semaphore, force_regenerate: bool) -> str:
        """处理单个知识点的生成 (异步工作单元)"""
        filepath = self.output_dir / f"{point.id}.md"
        if not force_regenerate and filepath.exists():
            logger.info(f"文件已存在，跳过: {point.title}")
            return "skipped"

        async with semaphore:
            logger.info(f"--- 开始处理: {point.title} ---")
            prompt = self.generate_prompt(point)
            
            content = None
            for attempt in range(self.config.get("retry_times", 3)):
                content = await self.call_gemini_api_async(prompt)
                if content:
                    break
                logger.warning(f"第 {attempt + 1} 次尝试失败 ({point.title})，将在 {self.config.get('retry_delay', 10)} 秒后重试...")
                await asyncio.sleep(self.config.get('retry_delay', 10))

            if content:
                self.save_content(point, content)
                return "success"
            else:
                logger.error(f"❌ 经过多次尝试，生成 {point.id} ({point.title}) 失败。")
                return "failed"

    async def run_parallel_generation(self, force_regenerate: bool):
        """主生成流程 (并行版)"""
        if not self.knowledge_points:
            logger.error("知识点列表为空，无法进行生成。")
            return

        max_parallel = self.config.get("max_parallel_requests", 8)
        logger.info(f"🚀 开始并行生成 {len(self.knowledge_points)} 个Python知识点内容 (最大并发数: {max_parallel})...")
        
        semaphore = asyncio.Semaphore(max_parallel)
        
        tasks = [
            self.generate_one_point_async(point, semaphore, force_regenerate)
            for point in self.knowledge_points
        ]
        
        results = await tqdm_asyncio.gather(*tasks, desc="生成进度")

        # 统计结果
        success_count = results.count("success")
        skipped_count = results.count("skipped")
        failed_count = results.count("failed")

        logger.info("🎉🎉🎉 所有任务处理完毕！ 🎉🎉🎉")
        logger.info(f"统计: 成功 {success_count}, 跳过 {skipped_count}, 失败 {failed_count}")


def main():
    """主函数，处理命令行参数"""
    parser = argparse.ArgumentParser(description="Python知识点内容批量生成工具 (并行版)")
    parser.add_argument("--config", default="config.example.json", help="配置文件路径")
    parser.add_argument("--force", action="store_true", help="强制重新生成所有文件，即使它们已存在")
    parser.add_argument("--max-parallel", type=int, help="覆盖配置文件中的最大并发数")
    
    args = parser.parse_args()
    
    generator = KnowledgeGenerator(config_path=args.config)

    if args.max_parallel:
        generator.config["max_parallel_requests"] = args.max_parallel
        logger.info(f"命令行覆盖最大并发数: {args.max_parallel}")

    asyncio.run(generator.run_parallel_generation(force_regenerate=args.force))

if __name__ == "__main__":
    main()