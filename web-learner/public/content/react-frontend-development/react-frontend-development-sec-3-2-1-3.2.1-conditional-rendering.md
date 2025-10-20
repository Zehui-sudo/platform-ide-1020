好的，作为一位资深的技术教育作者，我将为你撰写这篇关于 React 条件渲染的教学段落。

---

### 3.2.1 工具一：条件渲染 (Conditional Rendering)

在上一节中，我们已经掌握了如何使用 `useState` 来管理组件的内部状态。然而，状态本身只是数据，如果不能影响用户看到的界面，那它就毫无意义。本节我们将学习第一个，也是最核心的“数据驱动视图”工具：**条件渲染**。

条件渲染的核心思想非常直观：**根据当前的状态或 props，来决定渲染哪些 JSX 内容**。这就像生活中的场景：如果外面正在下雨（一个状态），你就带上雨伞（渲染雨伞图标）；如果没下雨，你就不带。在 React 中，我们利用标准的 JavaScript 语法来实现这一思想。

让我们来看看实现条件渲染的三种主流模式。

#### 模式一：三元运算符 (Ternary Operator)

当你的渲染逻辑是 “二选一” 的情况，比如“登录”或“未登录”、“开”或“关”，三元运算符 (`condition ? A : B`) 是最简洁、最常用的选择。

它的语法结构如下：

```javascript
condition ? expressionIfTrue : expressionIfFalse
```

在 JSX 中，你可以将它直接嵌入花括号 `{}` 中。

`code_example`
假设我们正在开发一个用户登录状态的显示组件。

```jsx
import React, 'useState' from 'react';

function UserGreeting() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const handleLoginClick = () => {
    setIsLoggedIn(true);
  };

  const handleLogoutClick = () => {
    setIsLoggedIn(false);
  };

  return (
    <div>
      {/* 根据 isLoggedIn 状态，决定显示欢迎语还是提示语 */}
      <h1>
        {isLoggedIn ? '欢迎回来, 尊贵的用户!' : '请先登录'}
      </h1>

      {/* 根据 isLoggedIn 状态，决定显示“登出”按钮还是“登录”按钮 */}
      {isLoggedIn 
        ? <button onClick={handleLogoutClick}>登出</button>
        : <button onClick={handleLoginClick}>登录</button>
      }
    </div>
  );
}

export default UserGreeting;
```

在这个例子中，`h1` 标签的内容和显示的按钮都由 `isLoggedIn` 这个 state 精确控制，实现了两种 UI 状态的清晰切换。

#### 模式二：逻辑与运算符 (`&&`)

有时候，我们的需求不是“二选一”，而是“满足条件就显示，不满足就什么都不显示”。这时，逻辑与运算符 (`&&`) 就派上了用场。

这个模式利用了 JavaScript 的“短路”特性：
*   `true && expression` 的结果总是 `expression`。
*   `false && expression` 的结果总是 `false`。

在 React 中，`true`、`false`、`null` 和 `undefined` 都是有效的子节点，但它们不会被渲染成任何内容。因此，`false && <SomeComponent />` 会导致什么都不渲染，这正是我们想要的效果。

`code_example`
想象一个邮箱应用，只有在有未读邮件时，才显示一个提示横幅。

```jsx
import React, { useState } from 'react';

function Mailbox() {
  const [unreadMessages, setUnreadMessages] = useState(['React 学习通知', '项目截止日期提醒']);

  return (
    <div>
      <h2>您的收件箱</h2>
      {/* 仅当 unreadMessages 数组长度大于 0 时，才渲染下面的 h3 标签 */}
      {unreadMessages.length > 0 &&
        <h3>
          您有 {unreadMessages.length} 条未读消息。
        </h3>
      }
      <p>这里是邮件列表...</p>
    </div>
  );
}

export default Mailbox;
```
在这个例子中，`<h3>` 标签及其内容只有在 `unreadMessages.length > 0` 为 `true` 时才会被渲染。如果数组为空，`&&` 左侧为 `false`，整个表达式短路，React 就不会渲染任何额外内容，界面非常干净。

#### 模式三：`if` 语句与变量

当渲染逻辑变得复杂，比如有多个 `else if` 分支，或者在决定渲染内容前需要进行一些计算时，将 `if` 语句直接写在 JSX 中是行不通的。

正确的做法是：**在 `return` 语句之前，使用 `if/else if/else` 逻辑准备好要渲染的 JSX，将其赋值给一个变量，然后在 `return` 中渲染这个变量。**

`code_example`
假设我们在开发一个数据加载组件，它有三种状态：`'loading'`（加载中）、`'success'`（成功）和 `'error'`（失败）。

```jsx
import React, { useState } from 'react';

function DataFetcher({ status }) { // status 由父组件传入
  // 1. 声明一个变量来持有将要渲染的内容
  let content;

  // 2. 在 return 外部，使用 if/else if/else 语句进行复杂的逻辑判断
  if (status === 'loading') {
    content = <p>⏳ 正在加载数据，请稍候...</p>;
  } else if (status === 'success') {
    content = <div>✅ 数据加载成功！</div>;
  } else if (status === 'error') {
    content = <p>❌ 抱歉，加载失败，请重试。</p>;
  } else {
    content = <p>请点击按钮开始加载。</p>;
  }

  // 3. 在 JSX 中，只渲染这个已经确定好内容的变量
  return (
    <div>
      {content}
    </div>
  );
}

export default DataFetcher;
```
这种方式让组件的 `return` 部分保持了结构上的简洁，同时将复杂的业务逻辑清晰地组织在了一起，可读性和可维护性都非常高。

`comparison`
#### 如何选择？一张图帮你决定

| 模式 | 最佳场景 | 优点 | 注意事项 |
| :--- | :--- | :--- | :--- |
| **三元运算符 `? :`** | “二选一” 的情况 | 极其简洁，可读性强，JSX 内联首选 | 嵌套过多会降低可读性 |
| **逻辑与 `&&`** | “显示或隐藏” 的情况 | 代码量最少，意图明确 | 避免在 `&&` 左侧使用数字 `0`，因为它会渲染出 `0` |
| **`if` 语句与变量** | 复杂的、多分支的渲染逻辑 | 逻辑清晰，易于扩展和维护 | 代码结构稍长，需要将逻辑提到 `return` 外部 |

---

`checklist`
### 本节回顾

- **核心思想**：条件渲染是 React 数据驱动视图的基石，它让 UI 能够根据组件的 state 和 props 动态变化。
- **工具箱**：你现在掌握了三种实现条件渲染的 JavaScript 模式：
    1.  **三元运算符 (`? :`)**：用于处理 `if-else` 式的二元选择。
    2.  **逻辑与运算符 (`&&`)**：用于处理 `if` 式的单路显示/隐藏。
    3.  **`if` 语句**：用于处理更复杂的、多分支的渲染决策。

熟练运用这三种模式，你的组件就拥有了“看情况办事”的智能，能够为用户呈现出丰富、动态的交互界面。接下来，我们将学习另一个数据驱动视图的重要工具：列表渲染。