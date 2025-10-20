好的，作为一位资深的技术教育作者，我将为你撰写这篇关于 ESLint 和 Prettier 的教学内容。

---

### 6.1.4 工具三：自动化代码规范 (ESLint & Prettier)

在我们掌握了模块打包与项目构建的基础后，现在我们将注意力转向一个关乎团队协作效率与大型项目可维护性的核心环节：**代码规范**。

想象一下，一个多人协作的项目中，张三习惯用双引号，李四偏爱单引号；王五习惯在行尾加分号，而赵六则从不加。当他们修改同一份文件时，代码审查（Code Review）就会充斥着大量与功能无关的风格讨论，合并代码（Merge）时也可能因为这些微小的差异引发不必要的冲突。这不仅浪费时间，更影响开发心情。

自动化代码规范工具正是解决这一痛点的“银弹”。它们能将团队从无休止的风格争论中解放出来，专注于业务逻辑本身。在 React 生态中，ESLint 和 Prettier 的组合拳已成为事实上的标准。

#### 1. ESLint: 你的代码质量“纪律委员”

ESLint 是一个功能强大的 JavaScript **代码检查工具（Linter）**。它的核心职责是分析你的代码，找出潜在的错误、不合理的写法以及不符合规范的风格。它不仅仅是格式警察，更是一位经验丰富的代码审查员。

**ESLint 主要解决两类问题：**

1.  **代码质量问题 (Code-Quality Rules)**: 发现潜在的 bug 或逻辑错误。
    *   禁止使用未声明的变量。
    *   提示函数中有从未被执行到的代码（unreachable code）。
    *   在 React 中，强制你在 `useEffect` 的依赖数组中包含所有外部变量（`eslint-plugin-react-hooks` 提供的规则）。

2.  **代码风格问题 (Stylistic Rules)**: 确保代码风格的统一。
    *   要求使用单引号还是双引号。
    *   规定缩进是使用两个空格还是四个空格。
    *   要求 `if-else` 语句必须使用花括号。

**【code_example】一个 ESLint 发现问题的例子**

假设我们有如下 React 组件代码，其中包含了一些常见错误：

```jsx
import React, { useState, useEffect } from 'react';

function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  var userType = "guest"; // 使用了 var

  useEffect(() => {
    // 异步获取用户数据
    fetch(`/api/users/${userId}`)
      .then(res => res.json())
      .then(data => setUser(data));
      // 警告：useEffect 依赖数组为空，但内部使用了 userId
  }, []); // ESLint 会在这里发出警告

  if (user) {
    userType = user.isAdmin ? "admin" : "member";
  }

  // 警告：userType 在 if 语句外声明，但在其内部被重新赋值，可能会造成混淆
  // 警告：JSX 中字符串未使用大括号包裹变量
  return <div>User Type: "userType"</div>;
}
```

当你配置好 ESLint (例如 Create React App 已内置)，你的代码编辑器或终端会立刻给出类似下面的提示：

```bash
[eslint] 'userType' is assigned a value but never used. (no-unused-vars)
[eslint] 'userType' should be a 'const' instead of a 'var'. (no-var)
[eslint] React Hook useEffect has a missing dependency: 'userId'. Either include it or remove the dependency array. (react-hooks/exhaustive-deps)
```

这些提示精准地指出了代码中的隐患，远比肉眼审查高效得多。

#### 2. Prettier: 你的代码风格“格式化专家”

与 ESLint 的“检查”不同，Prettier 是一个“有主见”的（Opinionated）**代码格式化工具**。它不关心你的代码逻辑是否正确，只专注于一件事：**将你的代码按照一套预设的、统一的风格进行重排**。

Prettier 会接管所有关于代码外观的决策，例如：

*   最大行宽
*   制表符宽度
*   是否使用分号
*   使用单引号还是双引号
*   对象、数组的末尾是否添加逗号（trailing commas）

**【code_example】Prettier 的格式化魔法**

假设你写了下面这段格式混乱的代码：

```jsx
// 格式化前
const MyComponent=({userName,onLogin,    isMobile})=>{
return (<div>
<p>欢迎, {userName}!</p><button
onClick={onLogin}
style={{marginLeft:10, padding: isMobile ? '5px' : '10px' }}
>登录</button>
</div>)
}
```

按下保存（通常会配置“保存时自动格式化”），Prettier 会瞬间将其转换为：

```jsx
// 格式化后
const MyComponent = ({ userName, onLogin, isMobile }) => {
  return (
    <div>
      <p>欢迎, {userName}!</p>
      <button
        onClick={onLogin}
        style={{ marginLeft: 10, padding: isMobile ? "5px" : "10px" }}
      >
        登录
      </button>
    </div>
  );
};
```

代码变得整洁、易读，且无论由谁编写，最终呈现的风格都完全一致。

#### 3. 强强联合：ESLint 与 Prettier 的协同工作流

很多初学者会困惑：既然 ESLint 也能检查代码风格，为什么还需要 Prettier？

这是因为它们各有侧重，并且协同工作能达到最佳效果。

**【comparison】ESLint vs. Prettier**

| 特性 | ESLint | Prettier |
| :--- | :--- | :--- |
| **核心职责** | 代码质量检查 & 风格检查 | 代码格式化 |
| **工作方式** | **报告**问题，部分可自动修复 | **重写**代码以符合风格 |
| **关注点** | 潜在 bug、最佳实践、代码风格 | 代码的视觉呈现（换行、缩进、空格等） |
| **配置** | 灵活但复杂，有数百条规则可选 | 选项很少，强调“有主见” |

**最佳实践工作流：**

专业团队通常会将二者结合，让它们各司其职：

1.  **分工**：
    *   **Prettier**：全权负责代码**格式化**（行宽、分号、引号等）。
    *   **ESLint**：负责**代码质量**检查（未使用变量、React Hook 规则等）。

2.  **整合**：
    *   使用 `eslint-config-prettier` 这个插件，它会**关闭** ESLint 中所有与 Prettier 冲突的样式规则，避免“打架”。
    *   使用 `eslint-plugin-prettier` 插件，它能将 Prettier 的格式化问题作为 ESLint 的规则来**报告**。这样，不符合 Prettier 格式的代码也会在 ESLint 运行时报错，实现了一体化的检查。

3.  **自动化**：
    *   **编辑器集成**：通过 VS Code 等编辑器的插件，实现“保存时自动格式化”，这是提升个人效率的关键。
    *   **Git 提交卡点**：结合 `husky` 和 `lint-staged` 工具，可以在每次 `git commit` 前自动对暂存区（staged）的文件运行 Prettier 格式化和 ESLint 检查。只有通过检查的代码才能被提交，从源头上保证了代码仓库的规范与整洁。

这个流程确保了任何进入代码库的代码都同时满足了质量标准和风格标准，是一种现代前端工程化的必备实践。

---

**要点回顾**

*   **重要性**：自动化代码规范是保障团队协作效率、提升代码可读性和可维护性的基石。
*   **ESLint**：是代码质量的“守护者”，负责检查潜在错误和逻辑问题。
*   **Prettier**：是代码风格的“造型师”，负责统一、强制地格式化代码。
*   **协同工作**：通过整合配置，让 Prettier 专职格式化，ESLint 专职质量检查，实现 `1 + 1 > 2` 的效果。
*   **工程实践**：结合编辑器和 Git Hooks，将规范检查和格式化完全自动化，融入日常开发流程。