# -*- coding: utf-8 -*-
"""Prompt catalog stored as explicit Python string constants."""

GEN_CLASSIFY_SUBJECT = '''You are a curriculum designer's assistant. Your task is to classify a given subject into one of two categories: "theory" or "tool".

Category Definitions:
* Theory: a field of knowledge, a discipline, or a conceptual framework focused on principles and the "why".
* Tool: a specific language, library, framework, or technology focused on the "how-to".

Task: Classify the following subject. Respond with a single word: theory or tool.

Subject: "{subject}"'''

GEN_FIX_PROPOSAL = '''你是严谨的技术编辑与作者。基于以下上下文，提出修复提案并给出修订后完整内容。

[主题]
{topic}

[知识点]
{point_title} (ID: {point_id})

[大纲]
{outline_md}

[当前内容]
{current_md}

[审查结果]
{review_json}
{extras_block}
请仅输出一个 JSON 对象，不要任何额外文字；键：
- summary: 对需要修改点与改动的简要说明（中文，100-200字）；
- revised_content: 修订后的完整 Markdown 内容（必须是完整替换稿而非片段）；
- risk (可选): 'low'|'medium'|'high'；
- change_categories (可选): 数组，参考审查分类；
- notes (可选): 对修复范围的简短说明。'''

GEN_THEORY_CONTENT = '''# 课程内容生成任务

你是一位世界级的教育家与作家，以其能将复杂、抽象的理论知识变得浅显易懂、引人入胜而闻名。你的天赋在于不仅仅是解释，更是去启发，将错综复杂的概念编织成一个引人入胜的叙事，从而促进读者形成深刻且持久的理解。

{path_block}
{goal_block}
{modules_block}
{contents_block}

【写作风格与深度要求】
- **类比与具象化**：对于抽象的核心概念，请使用读者生活中可能熟悉的现象或经验进行类比，帮助他们建立直观感受。**重要：确保类比在简化概念的同时，不会牺牲关键的技术精确性。**
- **背景与叙事**：对于任何一个基础理论、原则或关键思想，请深入挖掘其提出的背景。解释它试图解决什么问题？在此之前的主流观点是什么？它的出现带来了哪些关键性的影响？**对于技术性强的学科，这意味着清晰地阐述其“问题-解决方案-影响”的逻辑链条，而非文学性描述。**
- **启发性结尾**：在文章末尾，除了总结要点，还应提出一些发人深省的问题，或一个能承上启下的前瞻性观点，以激发读者的好奇心和进一步探索的欲望。
- **篇幅指导**：为确保内容的深度，每一篇知识点都应被充分地探讨。请力求内容详尽，目标篇幅不少于1500字。请优先考虑内容的深度与清晰度，而非简洁。

{context_block}
{task_block}

【输出约束】
- 使用 Markdown；结构清晰，标题层级合理；
- 叙事连贯：避免与已给上下文重复；必要时用一句话承接；
- 如引用数学/图表/流程，请使用适当的模块；
- 如 Markdown 中涉及代码示例，请用代码块进行声明包裹；
- 表格中不要出现代码格式的内容；
- 结尾含简短总结或要点回顾。

【语言】中文'''

GEN_TOOL_CONTENT = '''你是一位世界级的技术教育者和 {topic} 专家。
你的任务是接收一份由“总建筑师”设计的“教学设计图”（一个JSON对象），并依据这份设计图，将其中描述的知识点，转化为一篇高质量、多层次、结构清晰的Markdown教程。
{path_block}【教学设计图】
{design_json}

{context_block}【结构模板（按顺序生成对应区块）】
- 🎯 核心概念：用一句话说明这个知识点解决什么问题、为什么需要它。语言要精炼，直击要害。
- 💡 使用方式：介绍该知识点的主要使用方式或核心操作步骤。
- 📚 Level 1: 基础认知（30秒理解）
  提供一个最简单、最直观的代码示例，让初学者一眼就能明白基本用法。代码必须完整可运行，并以注释形式写出预期输出。
  ```python
  # 示例代码
  ```
- 📈 Level 2: 核心特性（深入理解）
  展示2-3个该知识点的关键特性或高级用法，每个特性配一个完整代码示例和简要说明。
  特性1: [特性名称]
  (简要说明)
  ```python
  # 示例代码
  ```
  特性2: [特性名称]
  (简要说明)
  ```python
  # 示例代码
  ```
- 🔍 Level 3: 对比学习（避免陷阱）
  通过对比“错误用法”和“正确用法”展示常见陷阱或易混淆概念。每种用法都需给出完整代码示例及解释。
  ```python
  # === 错误用法 ===
  # ❌ 展示常见错误
  # 解释为什么是错的

  # === 正确用法 ===
  # ✅ 展示正确做法
  # 解释为什么这样是对的
  ```
- 🚀 Level 4: 实战应用（真实场景）
  设计一个生动有趣的实战场景综合运用该知识点，避免枯燥案例。代码需完整并附有清晰输出结果。
  场景示例：[🎮 游戏角色属性计算器 / 🚀 星际飞船导航系统 / 🍕 披萨订单处理器 / 🐾 虚拟宠物互动等]
  ```python
  # 实战场景的完整代码
  ```
- 💡 记忆要点
  - **要点1**: [总结第一个关键记忆点]
  - **要点2**: [总结第二个关键记忆点]
  - ……

【输出要求】
- **循序渐进**: 从最简单的概念到复杂的应用。
- **重点突出**: 使用加粗、列表等方式突出核心知识。
- **生动有趣**: Level 4 的实战场景要富有想象力，使用 Emoji 增加趣味性。
- **代码可运行**: 所有代码块都必须是独立的、完整的、可以直接复制运行的。
- **中文讲解**: 所有解释和注释都使用中文。

{language_line}'''

KIMI_SYSTEM = '''你是 Kimi，具备联网搜索能力。请使用内置 $web_search 工具检索并返回指定教材的完整目录。严格输出 JSON，不要解释或 Markdown。'''

KIMI_USER = '''请检索并返回这本教材的完整目录输出时务必按照类似以下格式进行输出，具体到每个章节下的小节，保留原有层级与顺序：
## 第1章：LangGraph入门
### 1.1 核心概念
#### 1.1.1 什么是 LangGraph? (解决什么问题)
#### 1.1.2 State (状态): 图的记忆
#### 1.1.3 Nodes (节点): 工作单元
#### 1.1.4 Edges (边): 连接流程
### 1.2 第一个 LangGraph 应用
#### 1.2.1 定义 StateGraph
#### 1.2.2 添加节点 (Nodes)
#### 1.2.3 设置入口和出口 (Entry/Finish Point)
#### 1.2.4 编译与运行 (compile, stream)

## 第2章：构建动态流程 
### 2.1 条件分支
#### 2.1.1 条件边的使用
#### 2.1.2 实现一个简单的路由 Agent
### 2.2 循环与迭代
#### 2.2.1 在图中创建循环
#### 2.2.2 案例: 多轮问答或自我修正
只输出以下 JSON 对象：{
  "book": {"title": string, "authors": [string], "publisher": string},
  "toc": [string 或 对象，按原始目录顺序],
  "source": string
}
目标教材: 《[title]》 [authors] · [publisher]'''

RECONSTRUCT_CLASSIFY_SUBJECT = '''You are a curriculum designer's assistant. Your task is to classify a given subject into one of two categories: "theory" or "tool".

**Category Definitions:**

*   **Theory:** Refers to a field of knowledge, a discipline, or a conceptual framework. It focuses on the "why" and the underlying principles. Learning this involves understanding concepts, models, and their interconnections. Examples: "Natural Language Processing", "Microeconomics", "Deep Learning", "Algorithms".
*   **Tool:** Refers to a specific technology, programming language, library, or framework. It focuses on the "how-to" and practical application. Learning this involves mastering syntax, APIs, commands, and best practices for building things. Examples: "Python", "React", "Tailwind CSS", "Git", "Docker".

**Task:**
Classify the following subject. Respond with a single word: `theory` or `tool`.

**Subject:** "[subject]"'''

RECONSTRUCT_THEORIES_DEEP_PREVIEW = '''你是一位顶尖的课程设计师和该领域的专家。你的核心任务是基于以下提供的三份世界顶级教材的目录，为**本科大三学生**设计一份全面而深入的入门课程大纲。

**【核心目标】**
新大纲旨在帮助学习者构建一个**“T型知识结构”**。他们不仅要掌握**[subject]**领域从问题到解决方案的**核心叙事主线（T的横向）**，还必须深入理解每个关键节点上的**核心模型、算法或实现机制（T的纵向）**。学完后，他们应具备分析复杂问题、选择合适模型、并为后续项目实战打下坚实基础的能力。

**【原则要求】**

1.  **原则一：构建‘T型知识’，兼顾宏观叙事与微观深度**：
    *   **宏观叙事（横向）**：清晰地勾勒出领域发展的核心脉络，以一系列**根本性问题（Fundamental Question）**串联起关键的技术范式演进。让学习者理解“为什么需要这项技术”。
    *   **微观深度（纵向）**：对于叙事主线上的每一个**关键技术节点**（如：词向量、RNN、Transformer），必须深入展开，**至少包含**：
        *   **核心思想与工作原理**（The Core Idea & How it Works）。
        *   **关键的技术组件或算法步骤**（Key Components / Algorithmic Steps）。
        *   **该技术的主要变体及其权衡**（Important Variants and Their Trade-offs，例如：LSTM vs. GRU）。
        *   **它的优势与局限性**（Strengths and Limitations）。
    *   **必须排除**：纯粹的历史遗留细节和与主线无关的零散知识点。所有深度内容都必须服务于对核心节点的理解。

2.  **原则二：采用‘问题-思想-机制’的递进式逻辑框架**：
    *   目录结构需清晰地反映该领域的**核心挑战和技术演进**。
    *   每一章节都应围绕一个**“根本性问题”**展开。
    *   在提出问题后，首先介绍解决该问题的**“核心思想/范式”**（Core Idea/Paradigm）。
    *   然后，必须有一个或多个小节专门**“拆解关键机制”**（Unpacking the Key Mechanisms），深入讲解实现该思想的具体模型、结构或算法。
    *   **强调**概念间的依赖关系，例如，清晰地展示RNN如何为Seq2Seq铺路，Seq2Seq的局限性又如何催生了Attention机制。

3.  **原则三：连接‘理论知识’与‘实践应用’**：
    *   最终目标是让学习者获得**‘可应用知识’（Applicable Knowledge）**，能够将理论模型与具体的任务场景联系起来。
    *   每个关键技术节点都必须关联一个**“典型应用场景”或“标准任务”**（Canonical Application / Standard Task），例如：讲解RNN时，关联“语言模型”；讲解Seq2Seq时，关联“机器翻译”。
    *   在适当的地方，可以加入**“案例分析”或“实践指南”**，例如，“如何为一个文本分类任务选择并微调一个合适的预训练模型”。

请根据以上原则，审阅并整合以下提供的三本教材目录，输出一份全新的、符合要求的入门课程目录：

输入材料：textbook_toc_pipeline_langgraph.py 搜集的三份世界级教材目录

学习者期望（可选）

**【设计要求】**
在你的设计中，必须严格遵循以下两种原子结构模型：

*   **流水线 (Pipeline):**
    *   **定义:** 一系列具有**强时序依赖**的步骤，每一步都**建立在前一步的结果之上**，旨在完成一个**明确的整体任务**。
    *   **与“章节”的关系:** 对于大型领域（如NLP），**每一章**可以被视为一个**较大的流水线**，代表对一个基础问题的提出与解决。
    *   **例子:** 从“语言表示问题”出发 → 词向量 → 上下文表示 → 序列建模 → 预训练与微调。

*   **工具箱 (Toolbox):**
    *   **定义:** 一组围绕**共同主题或目标**，但彼此**相对独立**的知识点。
    *   **关键特征:** 知识点之间没有严格的顺序依赖，可以并行学习或按任意顺序学习。它们是解决相关问题的不同方法、工具或概念。
    *   **例子:** Python的各种数据结构、机器学习的各种分类算法、CSS的各种选择器。

**【构建步骤】**
1.  **分析与分组:** 仔细阅读输入的知识点列表。识别出哪些知识点可以串联成“流水线”，哪些可以归类到不同的“工具箱”中，形成小节(Group)。
2.  **设计微观结构:** 在每个小节内部，排列知识点（Section）的顺序，确保逻辑通顺。
3.  **精炼标题:** 为每个小节和知识点撰写清晰、简洁且具有引导性的标题。
4.  **注入元数据 (关键):** 在最终的JSON结构中，必须为每个小节（Group）和知识点（Section）添加以下元数据：
    *   为每个**小节 (Group)** 添加 `structure_type: "pipeline" | "toolbox"` 字段。
    *   为每个**知识点 (Section)** 添加：
        - `relation_to_previous`: `builds_on | tool_in_toolbox | alternative_to | deep_dive_into | first_in_sequence`
        - `primary_goal`: 用一句话清晰地定义该知识点的**核心内容目标**。它应精准描述“这节内容需要讲清楚什么核心问题”或“它要从什么角度去写”，而不是定义学习者的能力目标。
            - **反例 (Bad)**: "学习数据清洗" (过于宽泛，是学习目标)
            - **正例 (Good)**: "介绍数据清洗作为预处理流程第一步的核心任务，并展示常见的清洗技术。" (明确了内容范围和任务，是内容目标)
        - `suggested_modules`: 在正常的文字阐述之外，可以额外使用的**增强表达形式**清单（数组，允许从以下枚举中挑选）：
            `["code_example", "common_mistake_warning", "mermaid diagram", "checklist", "comparison", "case_study"]`
        - `suggested_contents`: 该知识点中**建议包含的核心内容**清单（数组）。
5.  **格式化输出:** 确保最终输出是一个结构严谨、格式正确的单一JSON对象，代表这一个章节的完整结构。不要包含任何多余解释性的文字

**【输出范例 (JSON)】**
```json
{
    "title": "Natural Language Processing: From Foundations to Large Models",
    "id": "cs-nlp-301",
    "groups": [
        {
            "title": "第一章：基础篇 · 让机器理解语言的基石",
            "id": "nlp-ch-1",
            "structure_type": "pipeline",
            "sections": [
                {
                    "title": "1.1 根本问题：为何机器处理文本如此困难？",
                    "id": "nlp-sec-1-1-1",
                    "relation_to_previous": "first_in_sequence",
                    "primary_goal": "通过展示语言的歧义性、非结构化和多样性，阐明自然语言处理（NLP）领域的核心挑战，并建立起将文本转化为机器可处理格式的必要性。",
                    "suggested_modules": [
                        "case_study",
                        "mermaid diagram"
                    ],
                    "suggested_contents": [
                        "**核心概念：歧义性 (Ambiguity)** - 展示词法歧义 (e.g., 'bank'), 句法歧义 (e.g., 'I saw a man with a telescope'), 和语义歧义的实例。",
                        "**核心挑战：非结构化特性** - 对比非结构化的自然语言与结构化的数据库表格，强调从文本中提取信息的难度。",
                        "**核心挑战：上下文依赖** - 解释同一个词在不同上下文中意义完全不同，引出上下文理解的重要性。",
                        "**基本框架** - 提出NLP任务的基本处理流程：原始文本 -> 预处理 -> 特征表示 -> 模型建模 -> 任务输出。"
                    ]
                },
                {
                    "title": "1.2 文本预处理：从原始语料到结构化词元流",
                    "id": "nlp-sec-1-1-2",
                    "relation_to_previous": "builds_on",
                    "primary_goal": "介绍作为所有NLP任务起点的文本预处理流水线，包括分词（Tokenization）、规范化（Normalization）和过滤（Filtering）等关键步骤及其实现方法。",
                    "suggested_modules": [
                        "code_example",
                        "checklist",
                        "common_mistake_warning"
                    ],
                    "suggested_contents": [
                        "**分词 (Tokenization)** - 讲解词分词、句子分词，并简要介绍更高级的子词分词（如BPE），并讨论其对处理未登录词的优势。",
                        "**规范化 (Normalization)** - 详细对比词干提取 (Stemming) 和词形还原 (Lemmatization) 的区别，并提供具体例子 (e.g., 'studies' -> 'studi' vs. 'study')。",
                        "**过滤 (Filtering)** - 解释停用词 (Stop Words) 移除的概念，并讨论何时应该（或不应该）移除停用词。",
                        "**代码实践** - 提供使用NLTK或spaCy库完成一套完整预处理流程的Python代码片段。"
                    ]
                }
            ]
        },
        {
            "title": "第二章：文本表示 · 将词语转化为向量",
            "id": "nlp-ch-2",
            "structure_type": "toolbox",
            "sections": [
                {
                    "title": "2.1 核心思想：分布式表示假说",
                    "id": "nlp-sec-2-1-1",
                    "relation_to_previous": "first_in_sequence",
                    "primary_goal": "解释将词语映射到向量空间的核心思想，并引入“一个词的含义由其上下文决定”的分布式假说，作为理解现代词向量模型的基础。",
                    "suggested_modules": [
                        "mermaid diagram"
                    ],
                    "suggested_contents": [
                        "**核心引言** - 引用J.R. Firth的名言：'You shall know a word by the company it keeps.'",
                        "**向量空间类比** - 使用2D/3D图示展示词向量关系，例如著名的 `vector('King') - vector('Man') + vector('Woman') ≈ vector('Queen')`。",
                        "**分布式 vs. 符号表示** - 对比词向量（分布式）与One-Hot编码（符号式）的差异，强调分布式表示的语义捕捉能力。"
                    ]
                },
                {
                    "title": "2.2 工具一 (统计方法)：TF-IDF与词袋模型",
                    "id": "nlp-sec-2-2-1",
                    "relation_to_previous": "tool_in_toolbox",
                    "primary_goal": "详细拆解词袋模型（BoW）和TF-IDF的计算原理，并分析它们作为稀疏、离散表示方法的优势（简单、可解释）与核心局限（无法捕捉语义、维度灾难）。",
                    "suggested_modules": [
                        "code_example",
                        "comparison"
                    ],
                    "suggested_contents": [
                        "**词袋模型 (BoW)** - 解释如何将一个句子或文档表示为一个忽略语序的词频向量。",
                        "**TF-IDF计算** - 分步讲解词频 (Term Frequency) 和逆文档频率 (Inverse Document Frequency) 的计算公式和直觉含义。",
                        "**动手计算** - 提供一个包含3-4个短文档的小型语料库，手动计算其中某个词的TF-IDF值。",
                        "**优劣分析** - 总结其优点（简单高效）和缺点（稀疏性、维度灾难、无语义信息）。"
                    ]
                },
                {
                    "title": "2.3 工具二 (预测方法)：静态词向量 (Word2Vec & GloVe)",
                    "id": "nlp-sec-2-2-2",
                    "relation_to_previous": "tool_in_toolbox",
                    "primary_goal": "深入讲解Word2Vec（包括Skip-gram和CBOW变体）和GloVe的核心工作原理，阐明它们如何通过预测上下文来学习捕捉词汇语义关系的密集向量。",
                    "suggested_modules": [
                        "code_example",
                        "comparison",
                        "case_study"
                    ],
                    "suggested_contents": [
                        "**Word2Vec核心原理** - 使用图示解释Skip-gram（中心词预测上下文）和CBOW（上下文预测中心词）的神经网络结构。",
                        "**GloVe核心原理** - 解释GloVe如何结合全局词-词共现矩阵的统计信息与预测方法的优点。",
                        "**代码实践** - 展示如何加载预训练的Word2Vec或GloVe模型，并用它来寻找近义词或完成词汇类比任务。",
                        "**可视化** - 使用t-SNE等降维方法可视化词向量空间，直观感受语义相近的词在空间中聚集的现象。"
                    ]
                },
                {
                    "title": "2.4 局限性：静态词向量无法解决的问题",
                    "id": "nlp-sec-2-2-3",
                    "relation_to_previous": "builds_on",
                    "primary_goal": "通过“一词多义”等具体案例，揭示所有静态词向量方法的共同缺陷——无法根据上下文动态调整词义，为后续引入上下文相关的表示方法埋下伏笔。",
                    "suggested_modules": [
                        "common_mistake_warning"
                    ],
                    "suggested_contents": [
                        "**“一词多义”问题** - 用'bank'（银行/河岸）或'stick'（棍子/坚持）的例子，说明静态词向量无法区分同一个词在不同语境下的含义。",
                        "**上下文无关** - 强调静态词向量为每个词生成一个固定的向量，无论其上下文如何变化。",
                        "**引出下一章** - 明确指出解决此问题的关键在于模型需要具备理解和记忆上下文的能力。"
                    ]
                }
            ]
        }
    ]
}
```
'''

RECONSTRUCT_THEORIES_PRINCIPLES = '''你是一位顶尖的课程设计师和该领域的专家。你的核心任务是基于以下提供的三份世界顶级教材的目录，为**本科大三学生**设计一份全面而深入的入门课程大纲。

**【核心目标】**
新目录旨在帮助学习者快速构建对**[subject]**核心原理的**概念脚手架（Conceptual Scaffold）**。学完后，他们应能运用所学知识解释该领域的基本现象，并为后续的深入学习打下坚实、结构化的基础。

**【原则要求】**
1.  **遵循80/20原则，聚焦核心**：
    *   专注于阐释该领域中，能够解释80%现象的20%核心公理、模型或理论。
    *   **必须排除**：1）历史上重要但已过时的细节；2）过于细分的专业分支内容；3）复杂的数学推导或非必要的实现细节。
    *   重点应放在该领域的**第一性原理（First Principles）、核心思想（Core Ideas）和分析框架（Analytical Frameworks）**上，而非零散的知识点。

2.  **构建‘问题-解决方案’的逻辑框架**：
    *   目录结构需清晰地反映该领域的**核心结构（例如：从宏观到微观，从理论到应用，按时间线发展）**。
    *   每一章节都应以该领域的一个**根本性问题（Fundamental Question）**为驱动（例如，“社会财富是如何创造和分配的？” -> 经济学中的生产与分配理论）。
    *   **特别强调**不同概念之间的内在逻辑和依赖关系，让知识形成一个连贯、自洽的体系。

3.  **强调‘解释性知识’与现实世界的联系**：
    *   最终目标是让学习者获得**‘解释性知识’（Explanatory Knowledge）**，使他们能够用学科视角**分析和解释**现实世界中的相关现象，而不是进行专业级别的操作或计算。
    *   每个核心概念都必须与一个**具体、可感知的现实案例或应用场景强绑定**（例如，讲解“机会成本”时，要关联到“选择读研而非工作的得失”）。
    *   鼓励在章节命名和内容描述中使用**生动、恰当的类比**，以降低非专业人士的认知门槛，并建立直观理解。

请根据以上原则，审阅并整合以下提供的三本教材目录，输出一份全新的、符合要求的入门课程目录：

输入材料：textbook_toc_pipeline_langgraph.py 搜集的三份世界级教材目录

学习者期望（可选）

**【设计要求】**
在你的设计中，必须严格遵循以下两种原子结构模型：

*   **流水线 (Pipeline):**
    *   **定义:** 一系列具有**强时序性或强依赖性**的知识点。它们通常描述一个连续的过程、工作流或逻辑推演。
    *   **关键特征:** 前一个知识点的**输出**是后一个知识点的**输入**。学习顺序**几乎不可更改**。
    *   **例子:** 文本预处理流程、数学定理的证明步骤、一个算法的执行过程。

*   **工具箱 (Toolbox):**
    *   **定义:** 一组围绕**共同主题或目标**，但彼此**相对独立**的知识点。
    *   **关键特征:** 知识点之间没有严格的顺序依赖，可以并行学习或按任意顺序学习。它们是解决相关问题的不同方法、工具或概念。
    *   **例子:** Python的各种数据结构、机器学习的各种分类算法、CSS的各种选择器。

**【构建步骤】**
1.  **分析与分组:** 仔细阅读输入的知识点列表。识别出哪些知识点可以串联成“流水线”，哪些可以归类到不同的“工具箱”中，形成小节(Group)。
2.  **设计微观结构:** 在每个小节内部，排列知识点（Section）的顺序，确保逻辑通顺。
3.  **精炼标题:** 为每个小节和知识点撰写清晰、简洁且具有引导性的标题。
4.  **注入元数据 (关键):** 在最终的JSON结构中，必须为每个小节（Group）和知识点（Section）添加以下元数据：
    *   为每个**小节 (Group)** 添加 `structure_type: "pipeline" | "toolbox"` 字段。
        - `primary_goal`: 用一句话清晰地定义该知识点的**核心内容目标**。它应精准描述“这节内容需要讲清楚什么核心问题”或“它要从什么角度去写”。
        - `suggested_modules`: 在正常的文字阐述之外，可以额外使用的**增强表达形式**清单（数组，允许从以下枚举中挑选）：
            `["code_example", "common_mistake_warning", "mermaid diagram", "checklist", "comparison", "case_study"]`
        - `suggested_contents`: 该知识点中**建议包含的核心内容**清单（数组）。
5.  **格式化输出:** 确保最终输出是一个结构严谨、格式正确的单一JSON对象，代表这一个章节的完整结构。不要包含任何多余解释性的文字
        
**【输出范例 (JSON)】**
```json
{
    "title": "Natural Language Processing: From Foundations to Large Models",
    "id": "cs-nlp-301",
    "groups": [
        {
            "title": "第一章：基础篇 · 让机器理解语言的基石",
            "id": "nlp-ch-1",
            "structure_type": "pipeline",
            "sections": [
                {
                    "title": "1.1 根本问题：为何机器处理文本如此困难？",
                    "id": "nlp-sec-1-1-1",
                    "relation_to_previous": "first_in_sequence",
                    "primary_goal": "通过展示语言的歧义性、非结构化和多样性，阐明自然语言处理（NLP）领域的核心挑战，并建立起将文本转化为机器可处理格式的必要性。",
                    "suggested_modules": [
                        "case_study",
                        "mermaid diagram"
                    ],
                    "suggested_contents": [
                        "**核心概念：歧义性 (Ambiguity)** - 展示词法歧义 (e.g., 'bank'), 句法歧义 (e.g., 'I saw a man with a telescope'), 和语义歧义的实例。",
                        "**核心挑战：非结构化特性** - 对比非结构化的自然语言与结构化的数据库表格，强调从文本中提取信息的难度。",
                        "**核心挑战：上下文依赖** - 解释同一个词在不同上下文中意义完全不同，引出上下文理解的重要性。",
                        "**基本框架** - 提出NLP任务的基本处理流程：原始文本 -> 预处理 -> 特征表示 -> 模型建模 -> 任务输出。"
                    ]
                },
                {
                    "title": "1.2 文本预处理：从原始语料到结构化词元流",
                    "id": "nlp-sec-1-1-2",
                    "relation_to_previous": "builds_on",
                    "primary_goal": "介绍作为所有NLP任务起点的文本预处理流水线，包括分词（Tokenization）、规范化（Normalization）和过滤（Filtering）等关键步骤及其实现方法。",
                    "suggested_modules": [
                        "code_example",
                        "checklist",
                        "common_mistake_warning"
                    ],
                    "suggested_contents": [
                        "**分词 (Tokenization)** - 讲解词分词、句子分词，并简要介绍更高级的子词分词（如BPE），并讨论其对处理未登录词的优势。",
                        "**规范化 (Normalization)** - 详细对比词干提取 (Stemming) 和词形还原 (Lemmatization) 的区别，并提供具体例子 (e.g., 'studies' -> 'studi' vs. 'study')。",
                        "**过滤 (Filtering)** - 解释停用词 (Stop Words) 移除的概念，并讨论何时应该（或不应该）移除停用词。",
                        "**代码实践** - 提供使用NLTK或spaCy库完成一套完整预处理流程的Python代码片段。"
                    ]
                }
            ]
        },
        {
            "title": "第二章：文本表示 · 将词语转化为向量",
            "id": "nlp-ch-2",
            "structure_type": "toolbox",
            "sections": [
                {
                    "title": "2.1 核心思想：分布式表示假说",
                    "id": "nlp-sec-2-1-1",
                    "relation_to_previous": "first_in_sequence",
                    "primary_goal": "解释将词语映射到向量空间的核心思想，并引入“一个词的含义由其上下文决定”的分布式假说，作为理解现代词向量模型的基础。",
                    "suggested_modules": [
                        "mermaid diagram"
                    ],
                    "suggested_contents": [
                        "**核心引言** - 引用J.R. Firth的名言：'You shall know a word by the company it keeps.'",
                        "**向量空间类比** - 使用2D/3D图示展示词向量关系，例如著名的 `vector('King') - vector('Man') + vector('Woman') ≈ vector('Queen')`。",
                        "**分布式 vs. 符号表示** - 对比词向量（分布式）与One-Hot编码（符号式）的差异，强调分布式表示的语义捕捉能力。"
                    ]
                },
                {
                    "title": "2.2 工具一 (统计方法)：TF-IDF与词袋模型",
                    "id": "nlp-sec-2-2-1",
                    "relation_to_previous": "tool_in_toolbox",
                    "primary_goal": "详细拆解词袋模型（BoW）和TF-IDF的计算原理，并分析它们作为稀疏、离散表示方法的优势（简单、可解释）与核心局限（无法捕捉语义、维度灾难）。",
                    "suggested_modules": [
                        "code_example",
                        "comparison"
                    ],
                    "suggested_contents": [
                        "**词袋模型 (BoW)** - 解释如何将一个句子或文档表示为一个忽略语序的词频向量。",
                        "**TF-IDF计算** - 分步讲解词频 (Term Frequency) 和逆文档频率 (Inverse Document Frequency) 的计算公式和直觉含义。",
                        "**动手计算** - 提供一个包含3-4个短文档的小型语料库，手动计算其中某个词的TF-IDF值。",
                        "**优劣分析** - 总结其优点（简单高效）和缺点（稀疏性、维度灾难、无语义信息）。"
                    ]
                },
                {
                    "title": "2.3 工具二 (预测方法)：静态词向量 (Word2Vec & GloVe)",
                    "id": "nlp-sec-2-2-2",
                    "relation_to_previous": "tool_in_toolbox",
                    "primary_goal": "深入讲解Word2Vec（包括Skip-gram和CBOW变体）和GloVe的核心工作原理，阐明它们如何通过预测上下文来学习捕捉词汇语义关系的密集向量。",
                    "suggested_modules": [
                        "code_example",
                        "comparison",
                        "case_study"
                    ],
                    "suggested_contents": [
                        "**Word2Vec核心原理** - 使用图示解释Skip-gram（中心词预测上下文）和CBOW（上下文预测中心词）的神经网络结构。",
                        "**GloVe核心原理** - 解释GloVe如何结合全局词-词共现矩阵的统计信息与预测方法的优点。",
                        "**代码实践** - 展示如何加载预训练的Word2Vec或GloVe模型，并用它来寻找近义词或完成词汇类比任务。",
                        "**可视化** - 使用t-SNE等降维方法可视化词向量空间，直观感受语义相近的词在空间中聚集的现象。"
                    ]
                },
                {
                    "title": "2.4 局限性：静态词向量无法解决的问题",
                    "id": "nlp-sec-2-2-3",
                    "relation_to_previous": "builds_on",
                    "primary_goal": "通过“一词多义”等具体案例，揭示所有静态词向量方法的共同缺陷——无法根据上下文动态调整词义，为后续引入上下文相关的表示方法埋下伏笔。",
                    "suggested_modules": [
                        "common_mistake_warning"
                    ],
                    "suggested_contents": [
                        "**“一词多义”问题** - 用'bank'（银行/河岸）或'stick'（棍子/坚持）的例子，说明静态词向量无法区分同一个词在不同语境下的含义。",
                        "**上下文无关** - 强调静态词向量为每个词生成一个固定的向量，无论其上下文如何变化。",
                        "**引出下一章** - 明确指出解决此问题的关键在于模型需要具备理解和记忆上下文的能力。"
                    ]
                }
            ]
        }
    ]
}
```

### reconstruct.tools'''

REVIEW_DEFAULT = '''你是资深的技术编辑，你的任务是审查下面的初稿，并以JSON格式提供具体的、可操作的反馈。

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

【你的JSON输出】'''

TOC_RECOMMEND = '''你是资深课程设计专家。请基于全球范围内的经典/权威/广泛采用的教材，推荐与主题“[subject]”最相关的教材。

如果提供了学习者的特定期望或偏好，请在不偏离“全球经典/权威”前提下，优先选择更契合这些期望的教材或版本（如更适合某语种学习、包含某类章节、偏向某些应用/任务等）。

输出要求：严格 JSON，且只输出以下结构：
{
  "textbooks": [
    {
      "title": "书名",
      "authors": ["作者1", "作者2"],
      "edition": "版次或年份版",
      "publisher": "出版社",
      "year": 2020,
      "isbn13": "可选",
      "official_url": "可选，出版社或课程官网"
    }
  ]
}

约束：
- 仅输出 JSON，不要附带解释或 Markdown。
- 关注“全球经典教材”，优先列出高影响力版本（如英文原版）。
- 一共推荐5本，优先推荐最相关的3本教材，按相关度降序输出。'''

TOC_SLUG = '''你的任务是为一个给定的主题生成一个简洁、全小写、URL友好、用连字符分隔（kebab-case）的英文 slug。

约束：
1. 只包含英文字母、数字和连字符'-'。
2. 如果主题是中文或其他语言，请先将其翻译或音译为有意义的英文。
3. 结果必须简短且具有描述性。

主题: "计算机网络原理"
Slug: computer-network-principles

主题: "八字算命"
Slug: bazi-divination

主题: "[subject]"
只输出 slug，不要任何解释或标点：'''

PROMPTS = {
    'gen.classify_subject': GEN_CLASSIFY_SUBJECT,
    'gen.fix_proposal': GEN_FIX_PROPOSAL,
    'gen.theory_content': GEN_THEORY_CONTENT,
    'gen.tool_content': GEN_TOOL_CONTENT,
    'kimi.system': KIMI_SYSTEM,
    'kimi.user': KIMI_USER,
    'reconstruct.classify_subject': RECONSTRUCT_CLASSIFY_SUBJECT,
    'reconstruct.theories.deep_preview': RECONSTRUCT_THEORIES_DEEP_PREVIEW,
    'reconstruct.theories.principles': RECONSTRUCT_THEORIES_PRINCIPLES,
    'review.default': REVIEW_DEFAULT,
    'toc.recommend': TOC_RECOMMEND,
    'toc.slug': TOC_SLUG,
}
