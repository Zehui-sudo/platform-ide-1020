# 项目总览与进度（纲要与模板生成改造）

本文件用于快速同步当前目标、方案与进度，便于下次直接上手。

## 目标
- 把“知识点生成”变成可控、稳定的流程：用“9 类原型（archetypes）+ 开关（switches）”来约束产物结构与风格。
- 让“学习大纲”先天携带元数据（archetype + switches），为后续生成节点提供高质量先验，降低波动。
- 逐步从“一次生成”升级为“多阶段流水线”，并引入可量化的质量评审与轻量自动修复。

## 核心设计
- 原型（9 类）
  - algorithm_impl, math_derivation, concept_exposition, api_quickstart, procedure_checklist, comparative_analysis, case_study, architecture_design, troubleshooting
- 开关（常用）
  - include_code, code_lang, include_math, math_depth, include_comparison_table, include_steps_checklist,
    include_case_snippets, include_eval_metrics, include_references, audience_level, tone_style
  - 可视化增强：include_mermaid, include_ascii_diagram, diagram_types, diagram_depth
- 模板库
  - 提供九类原型的由浅入深 Prompt 模板，并内置可视化位（Mermaid/ASCII）。
  - 文件：`prompt_archetype_templates.md`

## 已完成的脚本与文件
- 原型判别（规则/LLM）
  - `scripts/archetype_classifier.py`（规则+可选 LLM Hook）：
    - 解析通用 Markdown 大纲（标题+列表），规则打分出 archetype + switches，JSONL 输出，`--pretty` 预览。
  - `scripts/archetype_classifier_llm.py`（仅 LLM 判别）：
    - 专适配 learning-path 结构（H1/H2/H3/H4 含 id：js-ch/js-gr/js-sec）。
    - 默认输出到 `output/<输入文件名>.archetype_llm.jsonl`；支持 `--resume` 断点续跑、`--fsync` 强制落盘；
      并行度由 `config.json.max_parallel_requests` 控制（可用 `--llm` 指定模型）。

- 大纲生成（一次生成 + 四阶段流水线）
  - `scripts/generate_outline.py`（一次生成，输入“主题+深度”）：
    - 单次 LLM 输出结构化 JSON（含 archetype + switches），本地补默认与稳定 ID，渲染为 Markdown（learning-path 风格）。
    - 深度仅用于控制规模与粒度（章节/小节/知识点数量），不预分配 archetype 配比。
  - `scripts/generate_outline_pipeline.py`（四阶段 Brainstorm→Structure→Detail→Review）：
    - 阶段1 发散：产出 `seeds.json`（概念/理论/技能/工具/陷阱/前沿）。
    - 阶段2 聚类排序：产出 `skeleton.json`（章节骨架）。
    - 阶段3 递归深化：为每章生成小节与知识点，并对每个知识点用 LLM 判别 archetype+switches（内容驱动，无预分配）。
      - 中间产物：`outline.stage3.json`
    - 阶段4 审查评分：输出 `review.json`（结构方差、难度单调率、模板命中率、可视化命中率与总分），并进行轻量修复（如强制小节难度升序、必要原型默认开启 Mermaid）。
    - 最终产物：`outline.json` + `learning-path.md`。

- 模板库（由浅入深 + 可视化）
  - `prompt_archetype_templates.md`：九类原型模板骨架，支持 Mermaid/ASCII 可视化开关。

## 配置与依赖
- `config.json`
  - `llms`: deepseek-chat / deepseek-reasoner / gemini-2.5-pro 等（provider、base_url、api_key、model、temperature）
  - `node_llm`: 默认模型路由（generate_outline / generate_prompt_template 等）
  - `max_parallel_requests`: 并行度（LLM 判别与流水线并发）
- 依赖库
  - DeepSeek/OpenAI：`openai`；Gemini：`google-generativeai`
  - 本地运行无需网络写操作；调用 LLM 时需已配置对应 API Key

## 质量标准（用于评审与 A/B 对比）
- 逻辑递进性：由浅入深、宏观→微观、理论→实践（“故事线”测试）。
- 知识脚手架：中后期点的先修在前（“前置依赖”测试）。
- 完整性与覆盖度：主题关键板块不缺（“知识缺口”测试）。
- 结构均衡性：章/节/点分布均衡，避免极端臃肿或稀薄。
- 实用性与深度：Why & How，包含案例/流程/对比/权衡与图示。
- 自动化指标（流水线阶段4已覆盖部分）：
  - 结构方差、难度单调率、模板命中率、可视化命中率、总分（0–100）。

## 快速使用
- 原型判别（LLM，仅解析学习路径风格）：
  - `python scripts/archetype_classifier_llm.py web-learner/public/javascript-learning-path.md --config config.json --resume --pretty`
- 一次性大纲生成：
  - `python scripts/generate_outline.py --topic "JavaScript 核心基础" --depth core --pretty`
- 四阶段大纲生成：
  - `python scripts/generate_outline_pipeline.py --topic "LangGraph 入门" --depth core --pretty`
  - 可加：`--llm-gen / --llm-cls` 指定生成与分类模型；`--resume` 复用中间产物；`--max-parallel` 覆盖并发度。

## 当前进度
- 完成九类原型与开关设计，并沉淀模板库（含可视化开关）。
- 完成两种原型判别脚本（规则版与纯 LLM 版）；LLM 版支持并行与断点续跑，默认输出 JSONL。
- 完成一次性大纲生成脚本与四阶段流水线脚本；流水线输出 seeds/skeleton/outline/review，全链路可复用中间物。
- 评审指标（阶段4）已落地首版并能驱动轻量修复。

## 下一步（建议优先级）
- 将四阶段流水线的“审查评分 + 轻量修复”能力迁移到一次性脚本，统一审查口径。
- 增强评审指标：冗余率（标题标准化相似度）、命名规范、原型-开关一致性校验、跨章依赖检测。
- 与 `run_full_langgraph_pipeline.py` 集成：在生成节点读写 outline.json 的 archetype+switches，命中模板库。
- 增加缓存与重试（退避）策略，优化并发与成本。
- 提供 A/B 评测工具：对两份 outline.json 计算各维度分并生成对比报告。

## 关键决策
- 不预分配 archetype_mix（与内容强绑定），分类完全由知识点内容驱动。
- 深度（overview/core/advanced）仅用于控制规模与粒度，不影响原型配比。
- 默认对 algorithm_impl / procedure_checklist / architecture_design / troubleshooting 开启 Mermaid 可视化（可配置）。

## 可能风险与缓解
- LLM 波动与成本：引入骨架与审查闸门、并发控制、断点续跑与中间物复用。
- 领域差异：后续可按领域挂载“必备清单”和命名规范，增强覆盖与可教性。
- 渲染兼容：Mermaid 不可用时用 ASCII 兜底（模板库已覆盖）。

---
如需进一步细化某一阶段或集成到现有流水线，请在本文件“下一步”列表上认领与更新状态。

