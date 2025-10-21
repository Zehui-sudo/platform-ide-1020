# Mermaid 图表校验与修复计划

目标：系统性校验与修复 `public/content` 内所有 Markdown 文档中的 Mermaid 图表，使其在当前前端渲染链路下（`MermaidDiagram.tsx` → mermaid-to-excalidraw）稳定生成可视化结果，无运行时报错。

---

## 一、校验方法

在仓库根目录提供了代理指令，便于直接运行：

- 解析校验（推荐主流程）
  - `npm run validate:mermaid`
  - 作用：按前端与 `MermaidDiagram.tsx` 一致的归一化规则 + 同配置调用 `@excalidraw/mermaid-to-excalidraw` 完成“解析 + 转换（到骨架元素）”校验。
  - 输出：`web-learner/output/mermaid-render-errors.json`
    - 仅包含三项：`file`，`code`（原始代码块全文），`error`

- 静态规则检查（可快速发现格式问题）
  - `npm run lint:mermaid`
  - 输出：`output/mermaid-lint-report.json`

- 自动格式修复（安全回滚有备份）
  - `npm run fix:mermaid`
  - 备份目录：`output/mermaid-backup/`
  - 覆盖项：行尾分号、边标签统一为 `-->|…|`、必要引号、`<br/>` 归一化、sequenceDiagram 文本收拢等（详见脚本内注释）

注意：也可在包目录直接运行（效果一致）

- `cd web-learner && npm run validate:mermaid`
- `cd web-learner && npm run lint:mermaid`
- `cd web-learner && npm run fix:mermaid`

环境要求：Node ≥ 18（工程使用 pnpm，但以上脚本提供 npm 入口）。

---

## 二、预估错误类型与修复指引

以下类型来源于现有扫描（229 个块中 39 个失败）与常见写法总结，覆盖绝大多数问题：

1) 序列图文本/断行不合法（高频）
- 症状：Mermaid 报错如 “got NEWLINE/ACTOR/TXT/…”，或 “Expecting 'SOLID_OPEN_ARROW' … got 'NEWLINE'”。
- 成因：
  - 消息/箭头语句跨行写在多行；
  - `participant` 声明被插入了额外文字（如 IP）导致语法破裂；
  - Note/文本中夹入 HTML 标签或语法符号未转义。
- 修复：
  - 将一条消息合并为一行，内容内换行用 `\n`；
  - `participant A as …` 与说明分离到 Note（`note right of A: …`）或上/下文 Markdown；
  - Note 内容避免 HTML，保留纯文本，必要换行用 `\n`。

2) 未闭合/未加引号的标签文本（中高频）
- 症状：`got 'STR'/'PIPE'/'SQS'/'PS'` 等词法/语法错误。
- 成因：带有 `()`、`：:`、`[]` 的节点/边标签未加引号，或管道标签 `-->|…|` 内部存在 `()`/冒号未加引号，或引号未成对闭合。
- 修复：
  - 方/花/圆三类节点文本含 `() ： : [ {` 时整体加引号：`A["文本(含括号)"]`、`B{"文本:含冒号"}`、`C("文本[含中括号]")`；
  - 边的管道标签内含 `()`/冒号等时加引号：`-->|"含()的标签"|`。

3) 子图/节点引用不匹配
- 症状：`SubGraph element not found`。
- 成因：`subgraph` 标题/ID 与内部节点不一致；子图未正确闭合 `end`；或节点 ID 与 DOM 中渲染元素对不上。
- 修复：
  - 校对 `subgraph …` 与 `end` 配对；
  - 确保子图内节点 ID 与边引用一致；
  - 避免在子图标题里夹入未引号的 `()`/冒号。

4) `linkStyle` 索引越界
- 症状：`The index N for linkStyle is out of bounds`。
- 修复：确保 `linkStyle i` 的 `i` 在已有边的范围内 `0..(边数-1)`。

5) 代码块内误带 Markdown 引用符 `>`
- 症状：`No diagram type detected … for text: > graph TD …`
- 修复：移除围栏内每行起首的 `>`。

6) 不支持/混用的图表方言
- 症状：在流程图中使用 xychart/plot 风格的 `x-axis [0,22] line …` 等。
- 修复：改为 Mermaid v10 支持的图表类型（flowchart/sequence/class/gantt 等），或改为纯流程图。

7) 甘特图日期/区间非法
- 症状：`Invalid date: ...`
- 修复：日期用 `YYYY-MM-DD` 或合规的 duration 格式；避免自然语言日期。

8) 其他环境性错误（低频）
- 如 `Option is not defined` 等，通常来自校验脚本中 JSDOM 与 Mermaid 的边缘兼容；按当前数据量较少，如遇请在复查时注明为“环境性误报”并附截图验证。

---

## 三、修复完成标准

- 必须：`npm run validate:mermaid` 0 失败。
- 建议：`npm run lint:mermaid` 不出现严重规则项（可有建议但不阻塞）。
- 视觉：前端页面中不出现“Mermaid 渲染失败”；
  - 有放大预览（组件自带）情况下元素与文本无明显错位；
- 结构：
  - 节点/边/子图的 ID 和引用一致；
  - 序列图参与者、消息、note 逻辑清晰；
- 内容：
  - 不包含 HTML 标签破坏语法（如 `<b>`、`<code>` 混入图形语句行）；
  - 需要换行用 `\n`，避免真实 HTML `<br/>`（已在归一化阶段处理，但不能依赖其修复语义）。

---

## 四、推荐工作流（多轮协作）

1) 初始批处理
- 运行：`npm run fix:mermaid`
- 再运行：`npm run validate:mermaid`
- 打开：`web-learner/output/mermaid-render-errors.json`，按文件聚类问题，记录在“进度追踪”。

2) 分类修复（建议顺序）
- 序列图问题 → 文本合并与 note 纯文本化；
- 标签/引号类 → 节点/边标签系统加引号，一次通修；
- 子图/索引类 → 子图边界与 `linkStyle`；
- 方言/甘特 → 替换/重写或转为流程图；

3) 复验闭环
- 每修一批：`npm run validate:mermaid`；
- 0 失败后，打开页面 spot check 若干处（移动端/暗色）确保视觉合理。

4) 版本控制建议
- 每类问题修复一个提交，提交信息包含：[mermaid] 类型 / 文件范围 / 简述；
- 备份已由脚本自动写入 `output/mermaid-backup`，如需人工回滚可比对使用。

---

## 五、进度追踪（协作可编辑）

说明：按目录分批推进；每次修复后在此勾选并附上校验结果快照（可贴 `validate:mermaid` 统计数字或附带部分错误摘抄对比）。

- [ ] computer-network-principles
  - [ ] 批 1（序列图断行、HTML note）：
  - [ ] 批 2（linkStyle/子图）：
- [ ] natural-language-processing
  - [ ] 批 1（标签引号化、`[`/`(` 混入文本）：
  - [ ] 批 2（长图拆分/结构调整）：
- [ ] quantum-mechanics / quantum-mechanics2
  - [ ] 批 1（引用符 `>` 清理）：
  - [ ] 批 2（符号 `ψ`/`Δ` 出现在标签内时的引号与转义核对）：
- [ ] tailwind-css / react-frontend-development
  - [ ] 批 1（HTML 片段外移到 Markdown；图内 text 用纯文本）：
- [ ] microeconomics
  - [ ] 批 1（linkStyle 越界、坐标轴方言替换）：
- [ ] 其他目录（补充）：

当前基线（最近一次校验）：

```
Validated 229 Mermaid block(s). Parsed OK: 190. Failures: 39.
```

---

## 六、常见修复范式（示例）

- 序列图消息跨行 → 合并并用 `\n`：

原：

```
A->>B: 发送请求\n
“我是 192.168.1.11，
我的 MAC 是 0A:...:0B”
```

改：

```
A->>B: 发送请求\n“我是 192.168.1.11，\n我的 MAC 是 0A:...:0B”
```

- 参与者说明不要与声明同行：

原：

```
participant A as 主机A
IP: 192.168.1.10
```

改（将 IP 放入 note 或正文）：

```
participant A as 主机A
note right of A: IP: 192.168.1.10
```

- 含括号/冒号/中括号的标签统一加引号：

```
A["更新状态: setCount(newState)"]
B -->|"返回 JSX (UI 描述)"| C
subgraph "普通变量 (无法触发更新)"
```

- 移除围栏内 `>` 引用符：

```
graph TD
  A --> B
```

---

## 七、附录：脚本与实现对齐

- 前端渲染逻辑：`web-learner/src/components/MermaidDiagram.tsx`
  - 归一化：行尾分号、HTML `<br/>`、管道边标签、节点/子图标题引号化等；
  - 解析：`@excalidraw/mermaid-to-excalidraw`（与脚本一致参数）；
  - 导出 SVG：组件执行，校验脚本不做（无需模拟）。

- 校验脚本：`web-learner/scripts/validate-mermaid-render.mjs`
  - 输出仅含 `file`、`code`、`error`；
  - 使用 JSDOM 提供 DOM 支持；
  - 不进行 `exportToSvg`，避免额外 DOM 依赖。

- 静态检查/自动修复：
  - `web-learner/scripts/lint-mermaid.mjs`
  - `web-learner/scripts/fix-mermaid.mjs`

---

如需扩展：可在本文件补充“目录清单+责任人+预计完成时间”等协作元数据，以便持续推进与交接。

