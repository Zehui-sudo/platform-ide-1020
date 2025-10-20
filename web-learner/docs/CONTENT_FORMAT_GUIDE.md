# 课程内容文件格式指南

本文档定义了 `public/content/` 目录下课程内容 `.md` 文件的编写与组织规范，并说明新版“按主题分目录 + 解析器兼容旧 ID”的路径策略。

## 1. 目录结构与命名

自本次重构起，所有内容文件采用“按主题分目录”的嵌套结构：

- Astrology（占星）放置于：`public/content/astrology/`
  - 文件名通常以 `astro-` 开头，另有 `astrology_index.md`
- JavaScript 放置于：`public/content/javascript/`
  - 文件名通常以 `js-` 开头
- Python 放置于：`public/content/python/`
  - 文件名通常以 `py-` 开头

文件命名（不含 `.md` 后缀）需与知识点 Section 的 `id` 一致（即“文件基名 = sectionId”），路径由前缀推断的主题目录决定：

- `astro-*` 与 `astrology_index` → 放在 `astrology/`
- `js-*` → 放在 `javascript/`
- `py-*` → 放在 `python/`

解析器已实现向后兼容：
- 旧式 ID `python-sec-*` 会在解析层兼容映射为 `py-sec-*`，无需重命名既有文件。
- 旧式扁平链接（例如 `/content/js-sec-... .md` 或仅写裸 `js-sec-...`）在渲染中会被动态改写为新嵌套路径（详见第 4 节）。

相关实现：
- 内容路径工具：[contentPath.ts](../src/utils/contentPath.ts)
  - 解析旧 ID 与生成新路径：[resolveLegacyUrl()](../src/utils/contentPath.ts) / [resolveLegacyPath()](../src/utils/contentPath.ts) / [getContentPath()](../src/utils/contentPath.ts)

## 2. 文件与知识点（Section）的对应关系

- 每一个 `.md` 文件代表一个独立的知识点（Section）。
- 文件名称（不含 `.md`）必须与该知识点的 `id` 完全一致（“文件基名 = sectionId”）。
  - 例如：知识点 `js-sec-1-1-hello-world` 的内容应存储在
    - 新结构：`public/content/javascript/js-sec-1-1-hello-world.md`
    - （旧链接仍兼容：`/content/js-sec-1-1-hello-world.md`，渲染时会动态映射到新路径）

## 3. 内容块的定义

系统会将整个 `.md` 文件解析成一个由【Markdown 内容块】和【交互式代码块】组成的序列。

### 3.1 Markdown 内容块 (`MarkdownBlock`)

所有标准的 Markdown 文本，包括标题、段落、列表、图片以及不带特殊标记的普通代码块，都会被视为 Markdown 内容。解析器会将连续的 Markdown 内容合并成一个 `MarkdownBlock`。

示例：
```markdown
# 这是一个标题

这是一段说明文字。

下面是一个静态的代码示例，用于展示语法，但不能运行：

```javascript
function sayHello(name) {
  return `Hello, ${name}!`;
}
```

以上所有内容，包括标题、文字和上面的静态代码块，都属于同一个 `MarkdownBlock`。
```

### 3.2 交互式代码块 (`InteractiveCodeBlock`)

为了定义一个可交互、可运行的代码块，请使用标准的 Markdown 围栏代码块语法，并在语言标识符后面紧跟 `:interactive` 标记。

格式：
````markdown
```javascript:interactive
// 在这里编写可运行的代码
```
````

示例：
```markdown
现在，让我们来尝试一个真正的交互式例子。你可以修改下面的代码，然后点击“运行”按钮查看效果。

```javascript:interactive
// 修改引号内的文字，然后点击运行
console.log("你好，交互式编程！");
```

上面这个带有 `:interactive` 标记的代码块，将被解析成一个独立的 `InteractiveCodeBlock`。
```

## 4. 内部链接与向后兼容

在 Markdown 中编写指向其他知识点的链接时，推荐以下两种写法（均可被解析器正确识别并转到新嵌套路径）：

- 直接使用裸 `sectionId`：
  - 例：`[跳转到变量声明](js-sec-1-1-1-变量声明（var-let-const）)`
- 使用旧式扁平路径（渲染时会被重写）：
  - 例：`[跳转到变量声明](/content/js-sec-1-1-1-变量声明（var-let-const）.md)`

渲染层会使用路径工具进行改写与兼容：
- 链接改写逻辑见组件 [EnhancedMarkdownRenderer](../src/components/EnhancedMarkdownRenderer.tsx) 中的自定义 `a` 渲染器，它会调用路径工具将旧式链接动态映射到 `/content/{language}/{filename}.md` 结构。
- 解析与生成路径逻辑见 [contentPath.ts](../src/utils/contentPath.ts)。

## 5. 总结

- 新版采用“按主题分目录”的嵌套结构：`/content/{language}/{sectionId}.md`。
- 保持“文件基名 = sectionId”；主题目录由前缀推断（`js-` → `javascript/`，`py-` → `python/`，`astro-`/`astrology_index` → `astrology/`）。
- 解析器已向后兼容旧式扁平链接与 `python-sec-*` → `py-sec-*` 的差异。
- 交互式代码块使用 `language:interactive` 标记；其他内容均属于 Markdown 块。