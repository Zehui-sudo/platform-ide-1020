# Web Learner 正式三级目录改造方案

目标：在现有“章 → 节”的两级模型基础上，增强为“章 → 小类（SectionGroup）→ 节”的三级导航结构，同时确保现有内容渲染、搜索、聊天知识链接与用户进度等功能保持兼容。

## 一、数据模型调整

- LearningPath：保持不变
  - `id: string`
  - `title: string`
  - `language: 'python' | 'javascript'`
  - `chapters: Chapter[]`

- Chapter：新增 groups，保留 sections 以兼容旧数据
  - `id: string`
  - `title: string`
  - `groups?: SectionGroup[]`  // 新增
  - `sections?: Section[]`     // 兼容旧版（可选）

- SectionGroup（新增）：小类/主题分组（如“1.1 变量与值”）
  - `id: string`           // e.g., `js-gr-1-1`
  - `title: string`        // e.g., `1.1 变量与值`
  - `sections: Section[]`

- Section：保持不变
  - `id: string`
  - `title: string`
  - `chapterId: string`    // 仍指向父 Chapter.id（无需增加 groupId，除非后续需要）

- SectionLink / KnowledgeIndexEntry：可选增强
  - 可新增 `groupTitle?: string`，便于展示，但不是必要字段。

兼容性要求：
- `Chapter.sections` 与 `Chapter.groups[].sections` 二选一或同时存在时，渲染逻辑需要统一合并视图（详见 UI 部分）。

## 二、内容索引解析规则（Markdown → 数据）

为支持三级结构，调整 `public/javascript-learning-path.md` 的标题层级约定：

- `#` 路径标题（含 `(id: <path-id>)`）
- `##` 章标题（含 `(id: <chapter-id>)`）
- `###` 小类（SectionGroup）标题（含 `(id: <group-id>)`）
- `####` 节标题（Section）（含 `(id: <section-id>)`）

解析器（`learningStore.getLearningPath`）调整要点：
- 当前仅识别 `#`/`##`/`###`，需扩展识别 `###` 作为 Group，`####` 作为 Section。
- 解析流程：
  1) 读入整文，提取 path 标题与 id。
  2) 扫描 `##` 新建 Chapter；为每个 Chapter 初始化 `groups: []`。
  3) 扫描 `###` 新建 SectionGroup，挂到当前 Chapter；重置“当前组”。
  4) 扫描 `####` 新建 Section，挂到当前组；若当前组为空，则降级挂到 `chapter.sections` 以兼容旧结构。
- 仍要求每个 `(id: …)` 唯一且与 `public/content/{topic}/{sectionId}.md` 文件名一致（其中 `{topic}` ∈ `astrology` | `javascript` | `python`）。

示例片段（新索引格式）：

```markdown
# JavaScript 核心基础 (id: javascript-basics)

## 第一章：语言基础 (id: js-ch-1)
### 1.1 变量与值 (id: js-gr-1-1)
#### 1.1.1 变量声明（var/let/const） (id: js-sec-1-1-1-变量声明（var-let-const）)
#### 1.1.2 基本数据类型（number/string/boolean） (id: js-sec-1-1-2-基本数据类型（number-string-boolean）)
```

## 三、UI 改造（NavigationSidebar）

现状：按 Chapter → Section 扁平渲染。

改造目标：
- Accordion 第一级：Chapter
- Chapter 内：
  - 若有 `groups`：按 Group 分块（可用简单标题或二级 Accordion），每个 Group 下渲染 `sections` 列表。
  - 若无 `groups`：与现状一致，直接渲染 `chapter.sections`。

交互与状态：
- 搜索：应在章节、组、节三级过滤；命中节时需保留上层容器以便可见。（实现：预先构建过滤后的 `chapters`，对 `groups` 与 `sections` 做递归 filter）。
- 进度/收藏：保持基于 `section.id` 的状态，不变。
- 展开状态：
  - 复用 `expandedChapters: string[]`；
  - 若 Group 使用二级 Accordion，可新增 `expandedGroups: Record<chapterId, string[]>`。

无障碍与性能：
- 渲染量大时，建议对组/节列表做虚拟化（非必须，后续优化）。

## 四、服务层与其他模块影响评估

- 内容加载：`getSectionContent(sectionId)` 接入路径解析器，调用 [resolveLegacyUrl()](web-learner/src/utils/contentPath.ts:1) 将 `sectionId` 映射为新路径 `/content/{language}/{filename}.md` 后再 fetch；保持对旧式 `python-sec-*` 等 ID 的兼容。
- 知识链接：索引初始化时从 `LearningPath` 遍历收集 `Section` 即可；如需展示 Group，可额外传入 `groupTitle`。
- 聊天与语义检索：不依赖层级结构，仅依赖 Section 列表与语言标记，保持不变。
- 用户进度：键仍为 `sectionId`，不变。

## 五、迁移步骤清单

1) 类型定义：在 `src/types/index.ts` 新增 `SectionGroup` 接口；`Chapter` 增加 `groups?` 字段，保留 `sections?` 兼容。
2) 解析器：修改 `learningStore.getLearningPath` 的解析逻辑，按“### 组 / #### 节”的规则生成结构。
3) UI 导航：
   - `NavigationSidebar.tsx`：
     - 读取 `chapter.groups` 优先渲染；无则回退到 `chapter.sections`。
     - 搜索时对 `groups` 与 `sections` 递归过滤。
     - 可选：新增 `expandedGroups` 状态以更精细控制展开。
4) 内容索引：将 `public/javascript-learning-path.md` 升级为三级标题结构（见“二、内容索引解析规则”）。
5) 验证：
   - 渲染是否兼容仅两级的 Python 课程（回退逻辑生效）。
   - 搜索/收藏/完成状态是否正常。
   - 点击节是否正确加载对应 Markdown。
6) 清理（可选）：稳定后逐步弃用 `chapter.sections`（保留兼容期 1-2 个版本）。

## 六、测试建议

- 单元测试（可选）：为解析器编写用例，覆盖：
  - 仅两级（## + ###）
  - 三级（## + ### + ####）
  - 混合结构（同一章内含组与直接节）
  - 缺失 id/重复 id 的容错处理

- 手测清单：
  - 左侧导航展开/折叠/搜索/高亮当前节
  - 内容区渲染 Markdown 与交互式代码块
  - 用户进度（完成/收藏）统计与持久化
  - 聊天面板知识链接识别与跳转

## 七、回滚策略

- 若上线后出现导航渲染异常，可快速回滚至：
  - 解析器旧版本（仅两级）
  - UI 导航旧组件（仅渲染 `chapter.sections`）
  - 内容索引仍支持两级结构（保留一份旧版 `javascript-learning-path.md`）

## 八、时间评估（开发者日常效率）

- 类型 + 解析器：0.5 天
- 导航 UI 改造：0.5–1 天（含搜索与状态兼容）
- 验证与修正：0.5 天
- 合计：1.5–2 天

