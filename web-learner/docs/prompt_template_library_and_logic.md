# Prompt Template Library & Routing (3-Tag Minimal)

目标：用不超过 3 个标签完成路由，稳定映射到少量可维护的模板；覆盖广、可控、易扩展。

## 1) 标签体系（≤ 3 个）
- `domain`（必选）：沿用现有 6 类
  - `TECHNOLOGY_AND_ENGINEERING`
  - `THEORETICAL_AND_FORMAL_SCIENCES`
  - `EMPIRICAL_AND_NATURAL_SCIENCES`
  - `HUMANITIES_AND_ARTS`
  - `SOCIAL_SCIENCES`
  - `PRACTICAL_SKILLS_AND_HOW_TO`
- `object_type`（必选，少量、域内收敛）：用于明确“知识对象”的形态。
  - Tech: `concept`, `method`, `tool`
  - Theoretical: `concept`, `principle`
  - Empirical: `phenomenon`, `experiment`
  - Humanities: `concept`, `work_or_person`
  - Social: `theory`, `study_or_case`
  - Practical: `howto`
- `mode`（可选，3 选 1）：决定强调侧重（同一模板内的“开关”）。
  - `explain`（解释/阐释为主）
  - `compare`（对比/辨析为主）
  - `apply`（应用/实操为主）

注：若无 `mode`，默认 `explain`；`mode` 不改变模板 ID，只影响模板内显示的模块权重/是否必填。

## 2) 路由规则（简单稳定）
1) 先取 `domain` → 选用该域的“基模板骨架”（即 `prompt-template.md` 中的 6 个之一）。
2) 再取 `object_type` → 在域骨架上套用对应的“对象型模块”（增减章节/更改栏目标题）。
3) 可选 `mode` → 打开或强调骨架内对应模块：
   - `explain` → 核心定义/原理/符号化/基础例子
   - `compare` → 错误 vs 正确/相邻概念/竞品或替代技术对比
   - `apply` → 迷你项目/步骤化教程/实验或案例复现

当分类置信度低或标签不在映射表内，回退到：域骨架 + `object_type` 最相近映射 + `explain`。

## 3) 映射表（Domain × ObjectType → TemplateID）
- TECHNOLOGY_AND_ENGINEERING
  - concept → `TECH_CONCEPT`
  - method → `TECH_METHOD`
  - tool → `TECH_TOOL`
- THEORETICAL_AND_FORMAL_SCIENCES
  - concept → `THEORY_CONCEPT`
  - principle → `THEORY_PRINCIPLE`
- EMPIRICAL_AND_NATURAL_SCIENCES
  - phenomenon → `NAT_PHENOMENON`
  - experiment → `NAT_EXPERIMENT`
- HUMANITIES_AND_ARTS
  - concept → `HUM_ANALYSIS`
  - work_or_person → `HUM_WORK_PERSON`
- SOCIAL_SCIENCES
  - theory → `SOC_THEORY`
  - study_or_case → `SOC_STUDY`
- PRACTICAL_SKILLS_AND_HOW_TO
  - howto → `HOWTO_GUIDE`

说明：TemplateID 是“域骨架 + 对象型模块”的别名，数量固定（12 个）。`mode` 不增加模板数量。

## 4) 模板落地（与现有骨架的对应）
每个 TemplateID 基于 `prompt-template.md` 中的对应域，按对象型模块切/并栏目：
- `TECH_CONCEPT` → 基于“技术与工程”，保留：核心概念、基础用法(L1)、对比学习(可选)、记忆要点；若 `mode=apply`，保留精简“实战应用”示例。
- `TECH_METHOD` → 强调：API/伪代码、完整可运行示例、复杂度/边界、常见错误；`compare` 下加入“替代方法对比”。
- `TECH_TOOL` → 强调：运行环境/版本/依赖、安装与最小可用、常见坑与 FAQ、命令/API 速查。
- `THEORY_CONCEPT` → 强调：严谨定义、符号体系、相邻概念区分、典型例题。
- `THEORY_PRINCIPLE` → 强调：公理前提、定理与证明思路、推论与局限、例题。
- `NAT_PHENOMENON` → 强调：核心现象、解释原理、模型与图表、现实意义。
- `NAT_EXPERIMENT` → 强调：研究问题、实验设计、变量控制、结果与不确定性、可重复性。
- `HUM_ANALYSIS` → 强调：时代背景、核心思想/文本、方法论视角、多元解读与批判。
- `HUM_WORK_PERSON` → 强调：作品/人物背景、代表作/关键事件、风格与影响、当代回响。
- `SOC_THEORY` → 强调：理论框架、机制机理、实证证据、批判与边界。
- `SOC_STUDY` → 强调：研究设计（样本/测量/效度）、发现与解释、伦理与偏差、外部效度。
- `HOWTO_GUIDE` → 强调：成果图/目标、材料清单、步骤化指令、常见问题、风险与替代方案。

`mode` 的影响（模板内开关示意）：
- `explain`：保留“核心概念/定义/原理/符号/例题/基础演示”模块。
- `compare`：强制启用“对比学习/相邻概念区分/替代技术或理论对比/错误 vs 正确”。
- `apply`：强制启用“实战应用/分步操作/实验复现/迷你项目”。

## 5) 分类器输出（最小 JSON）
- 字段：
  - `topic`(str)
  - `domain`(enum)
  - `object_type`(enum)
  - `mode`(enum, optional; default `explain`)
  - `confidence`(0–1, optional)
  - `rationale`(≤ 50 字, optional)
- 示例：
```json
{
  "topic": "傅里叶变换",
  "domain": "THEORETICAL_AND_FORMAL_SCIENCES",
  "object_type": "principle",
  "mode": "explain",
  "confidence": 0.84,
  "rationale": "数学原理与定理推导为主"
}
```

## 6) 路由伪代码
```pseudo
function route(input):
  d = input.domain
  o = input.object_type
  m = input.mode or 'explain'

  if (d,o) not in mapping:
    o = nearest_object_type_in_domain(d)

  template_id = mapping[(d,o)]
  return { template_id, mode: m }
```

## 7) 快速示例（5 条）
- 主题：CRDT 一致性算法
  - {domain=TECHNOLOGY_AND_ENGINEERING, object_type=method, mode=compare}
  - → `TECH_METHOD`，对比 Paxos/Raft，附运行示例
- 主题：米勒-尤里实验
  - {domain=EMPIRICAL_AND_NATURAL_SCIENCES, object_type=experiment, mode=explain}
  - → `NAT_EXPERIMENT`，变量控制与结论
- 主题：荷马史诗与希腊城邦精神
  - {domain=HUMANITIES_AND_ARTS, object_type=work_or_person, mode=explain}
  - → `HUM_WORK_PERSON`，文本选段+当代回响
- 主题：凯恩斯主义与后续批判
  - {domain=SOCIAL_SCIENCES, object_type=theory, mode=compare}
  - → `SOC_THEORY`，机制+实证证据+批判
- 主题：用 GitHub Actions 部署静态站点
  - {domain=TECHNOLOGY_AND_ENGINEERING, object_type=tool, mode=apply}
  - → `TECH_TOOL`，最小可运行流水线与 FAQ

## 8) 维护策略（极简）
- 模板数量固定为 12；仅当出现“批量需求”且复用率>30%时，才新增 TemplateID。
- 新增需求优先映射到现有模板，通过 `mode`/栏目开关满足；确需新增时：增加一个对象型模块或重用域骨架。
- 版本与评测：保留一个 50 题的基准校验集（topic→期望模板），每次变更跑一致性对比。

---
本文件定义了最小可用的 3 标签路由与固定模板集合。生成侧仅需：根据 (domain, object_type) 取模板，按 `mode` 打开相应模块。
