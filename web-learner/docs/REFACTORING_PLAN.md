# `reconstruct_outline_langgraph.py` 改造计划

**目标:** 对现有脚本进行重构，使其能够智能区分“理论型”和“工具型”学习主题，并调用两种不同的、专门优化的Prompt来生成相应的大纲。

---

### 第1步: 内置并行的Prompt模板

为了让脚本独立运行，我们将不再从外部文件加载Prompt，而是将所有需要的Prompt模板作为常量直接内置在脚本中。

1.  **分类Prompt:** 新增一个 `PROMPT_CLASSIFY_SUBJECT` 常量。 【当前已经完成√】
    *   **作用:** 用于请求LLM判断一个给定的主题（Subject）属于“理论”还是“工具”。
    *   **设计:** Prompt会清晰地定义“理论”和“工具”的区别，并要求LLM仅返回单个词（`theory` 或 `tool`）作为回答，以便程序解析。

2.  **理论Prompt:** 将现有的 `PROMPT_INSTRUCTION` 重命名为 `PROMPT_INSTRUCTION_THEORIES`。
    *   **作用:** 保留现有功能，用于处理“自然语言处理”、“微观经济学”等理论型学科。它依赖于输入的多份教材目录，构建“T型知识结构”。

3.  **工具Prompt:** 新增一个 `PROMPT_INSTRUCTION_TOOLS` 常量。
    *   **作用:** 用于处理“Python”、“React”等工具型技能。它将指导LLM构建一个“技能金字塔”式的、从基础到实践的学习路径，不强依赖外部教材输入。

---

### 第2步: 实现主题的自动分类

脚本需要一个“调度员”来决定走哪条Prompt路径。

1.  **创建 `classify_subject` 函数:** 【当前已经完成√】
    *   **输入:** `subject` (字符串), `llm_caller` (一个LLM调用实例)。
    *   **逻辑:**
        *   该函数会使用一个专门用于分类的、轻量级的LLM（如 `gemini-1.5-flash`）。
        *   它将 `subject` 填入 `PROMPT_CLASSIFY_SUBJECT` 模板。
        *   调用LLM，并获取返回结果。
        *   对结果进行清洗（例如，去除多余的空格和转换成小写），确保稳定返回 `theory` 或 `tool`。
    *   **输出:** 分类结果字符串 (`"theory"` 或 `"tool"`)。

---

### 第3步: 改造Prompt构建与选择逻辑

`build_prompt` 函数需要变得更“聪明”，能够根据分类结果选择不同的模板和处理方式。

1.  **修改 `build_prompt` 函数签名:**
    *   新的函数签名将是 `build_prompt(subject: str, materials: Dict[str, Any], subject_type: str) -> str`。它增加了一个 `subject_type` 参数。

2.  **实现内部条件路由:**
    *   **if `subject_type == "tool"`:**
        *   选择 `PROMPT_INSTRUCTION_TOOLS` 作为基础模板。
        *   `materials` (教材目录) 的处理逻辑将变为**可选**。工具类Prompt的核心是其内在的知识结构，外部教材仅作为参考，甚至可以完全不使用。
    *   **if `subject_type == "theory"`:**
        *   选择 `PROMPT_INSTRUCTION_THEORIES` 作为基础模板。
        *   `materials` 的处理逻辑保持不变，仍然是**必需的**核心输入。

---

### 第4步: 更新主函数 `main` 的执行流程

`main` 函数需要被更新以串联起以上所有的新组件。

1.  **加载配置后，初始化分类器:** 在加载完`config.json`后，专门为分类任务初始化一个轻量级的 `LLMCaller` 实例。

2.  **执行分类:** 在准备好 `subject` 字符串后，立刻调用 `classify_subject` 函数，得到 `subject_type` 的值。并打印一条日志，告知用户当前主题被识别为哪种类型。

3.  **传递分类结果:** 在调用 `build_prompt` 函数时，将上一步得到的 `subject_type` 传递进去。

4.  **后续流程不变:** 脚本的后续部分（调用LLM、解析JSON、保存文件）保持不变，因为无论哪条路径，最终都期望得到一个符合格式的JSON输出。
