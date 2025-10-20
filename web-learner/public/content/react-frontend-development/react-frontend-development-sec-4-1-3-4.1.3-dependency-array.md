好的，我们来续写这一节内容。

---

### 4.1.3 关键：驾驭依赖项数组 (Dependency Array)

我们刚刚通过一个空数组 `[]` 成功实现了只在组件挂载时运行一次的副作用，这解决了初始化数据获取的问题。但这仅仅是依赖项数组能力的冰山一角。它才是真正控制副作用何时“苏醒”、何时“沉睡”的精确开关。

依赖项数组的**核心工作机制**非常简单：在每次组件重新渲染后，React 会将数组中当前的值与上一次渲染时的值进行逐一对比（使用 `Object.is` 算法）。只要有**任何一个值发生了变化**，React 就会重新执行该 `useEffect` 中的函数。

为了完全掌握它，我们需要深入理解和对比三种核心模式。

---

#### `comparison` 核心模式对比：三种依赖项，三种生命周期

| 模式 (Pattern) | 语法 (Syntax) | 执行时机 (Execution Timing) | 典型用例 (Typical Use Case) |
| :--- | :--- | :--- | :--- |
| **1. 无依赖数组** | `useEffect(() => { ... })` | **每次渲染后**都会执行。 | 1. 当副作用需要与每一次UI更新同步时（非常少见）。<br>2. 记录每次渲染的日志。<br>3. **通常是错误的用法，容易导致性能问题或无限循环。** |
| **2. 空依赖数组** | `useEffect(() => { ... }, [])` | **仅在组件首次挂载**到 DOM 后执行一次。 | 1. 获取初始数据 (`fetch`)。<br>2. 设置全局事件监听器 (`window.addEventListener`)。<br>3. 启动只需运行一次的定时器 (`setTimeout`, `setInterval`)。 |
| **3. 包含依赖项** | `useEffect(() => { ... }, [a, b])`| 1. 首次挂载后执行一次。<br>2. 在后续渲染中，只有当 `a` 或 `b` 的值发生变化时，才会再次执行。 | 1. 当 `props` 或 `state` 变化时，重新获取数据。<br>2. 当某个状态变化时，需要重置或更新订阅。<br>3. 任何需要“响应”特定值变化的副作用。 |

现在，让我们通过具体的代码示例来感受这三种模式的差异。

#### 模式一：省略依赖项数组 —— “每次都运行”

省略第二个参数，就等于告诉 React：“这个副作用与组件的每一次呼吸都息息相关，请在每次渲染完成后都执行它。”

```jsx
import React, { useState, useEffect } from 'react';

function RenderLogger() {
  const [count, setCount] = useState(0);

  // 模式一：没有依赖项数组
  useEffect(() => {
    // 每次组件渲染（包括 state 更新引起的重渲染）后，这行日志都会被打印
    console.log(`组件已渲染, count 值为: ${count}`);
  }); // 注意这里没有第二个参数

  return (
    <div>
      <p>You clicked {count} times</p>
      <button onClick={() => setCount(count + 1)}>
        Click me
      </button>
    </div>
  );
}
```

在这个例子中，每次你点击按钮，`count` 状态更新，组件重新渲染，`useEffect` 里的 `console.log` 就会执行一次。虽然这个例子是无害的，但如果 `useEffect` 内部包含的是 API 请求或复杂的计算，这种模式很快就会成为性能瓶颈。

**何时使用？** 极少数情况下，当你确实需要副作用与每一次的视觉更新保持同步时。大多数时候，这都不是你想要的行为。

#### 模式二：空数组 `[]` —— “只运行一次”

这我们已经很熟悉了。它声明副作用不依赖于任何 `props` 或 `state`，因此只在“出生”时（挂载）执行一次。这是组件的“设置”阶段。

```jsx
import React, { useState, useEffect } from 'react';

function GlobalClickListener() {
  useEffect(() => {
    const handleGlobalClick = () => {
      console.log('全局点击事件被触发！');
    };
    
    // 在 document 上设置一个事件监听
    document.addEventListener('click', handleGlobalClick);
    console.log('事件监听器已设置。');
    
    // 重要：返回一个清理函数，将在组件卸载时执行
    return () => {
      document.removeEventListener('click', handleGlobalClick);
      console.log('事件监听器已清理。');
    };
  }, []); // 空数组，表示此 effect 只在挂载和卸载时运行

  return <p>点击页面任意位置，查看控制台输出。</p>;
}
```

这个例子展示了另一个关键点：如果 `useEffect` 返回一个函数，这个函数被称为**清理函数 (Cleanup Function)**。React 会在组件从 UI 中移除（卸载）时，或者在下一次 effect 即将重新执行**之前**，运行这个清理函数。对于空数组模式，它只在组件卸载时运行，是 `componentWillUnmount` 的完美替代。

#### 模式三：包含依赖项 `[dep1, dep2, ...]` —— “按需运行”

这是 `useEffect` 最强大、最灵活的模式。它让副作用精确地“订阅”了某些值的变化。让我们回到 `UserProfile` 的例子，并让它能够响应 `userId` 的变化。

`code_example`
```jsx
import React, { useState, useEffect } from 'react';

// 子组件：根据传入的 userId 获取并显示用户信息
function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // 模式三：依赖于 userId prop
  useEffect(() => {
    console.log(`Effect 正在运行，因为 userId 变为: ${userId}`);
    setLoading(true); // 开始获取新数据，显示加载状态
    
    fetch(`https://api.example.com/users/${userId}`)
      .then(response => response.json())
      .then(data => {
        setUser(data);
        setLoading(false);
      });
  
  // 关键：将 userId 添加到依赖项数组中
  }, [userId]); 

  if (loading) {
    return <div>Loading user {userId}...</div>;
  }

  return <h1>Hello, {user.name}</h1>;
}

// 父组件：可以切换 userId
export default function App() {
  const [currentUserId, setCurrentUserId] = useState(1);

  return (
    <div>
      <UserProfile userId={currentUserId} />
      <button onClick={() => setCurrentUserId(currentUserId + 1)}>
        Load Next User (ID: {currentUserId + 1})
      </button>
    </div>
  );
}
```

执行流程分析：
1.  **初始渲染**: `App` 渲染，`currentUserId` 是 `1`。`UserProfile` 首次挂载，`userId` prop 是 `1`。`useEffect` 执行，获取用户 `1` 的数据。
2.  **点击按钮**: `setCurrentUserId(2)` 被调用。`App` 状态更新，重新渲染。
3.  **子组件重渲染**: `UserProfile` 接收到新的 `props`，`userId` 从 `1` 变成了 `2`。
4.  **依赖项检查**: React 比较上一次的依赖项 `[1]` 和这一次的 `[2]`。发现值发生了变化。
5.  **Effect 重新执行**: React 再次运行 `useEffect` 内部的函数，现在 `fetch` 的 URL 是 `.../users/2`，从而获取了新用户的数据。

这个模式完美实现了 Class 组件中 `componentDidUpdate` 的逻辑，但更加精准和声明式。你不再需要手动在 `componentDidUpdate` 中写 `if (prevProps.userId !== this.props.userId)` 这样的条件判断，依赖项数组为你自动处理了这一切。

---

#### `common_mistake_warning` 常见陷阱：遗漏依赖项

**最常见也是最危险的错误**，就是 effect 内部用到了某个 `prop` 或 `state`，却没有将它声明在依赖项数组中。这会导致一个被称为“**陈旧闭包 (Stale Closure)**”的问题。

看下面这个错误的例子：
```jsx
// 错误示范
function Counter() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    // 这个 effect 依赖 count，但我们故意忘记把它写进依赖项数组
    const intervalId = setInterval(() => {
      // 问题：这里的 count 永远是初始渲染时的值，即 0
      console.log(`定时器中的 count: ${count}`); 
    }, 1000);
    
    return () => clearInterval(intervalId);
  }, []); // 错误的空数组

  return <button onClick={() => setCount(count + 1)}>Increment: {count}</button>;
}
```
当你点击按钮，页面上的 `count` 会正常增加。但控制台每秒打印的 `count` **永远是 0**。

**为什么？**因为 `useEffect` 的回调函数是在组件首次渲染时创建的，它“捕获”了当时作用域中的 `count` 值（也就是 `0`）。由于依赖项是 `[]`，这个 effect 永远不会重新执行，所以那个旧的回调函数（和它捕获的旧 `count` 值）也永远不会被新的替换。

**正确做法是什么？** 始终诚实地列出所有依赖项。现代的 React 开发工具（如官方的 ESLint 插件 `eslint-plugin-react-hooks`）会自动检测并警告你这类错误。**请务必相信并遵循 linter 的提示！**

### 本节小结

*   **依赖项数组是 `useEffect` 的灵魂**，它决定了副作用的“生命周期”。
*   **三种核心模式**：
    *   **无数组**：每次渲染都运行，慎用。
    *   **空数组 `[]`**：仅挂载时运行一次，用于初始化。
    *   **有内容的数组 `[dep]`**：仅当依赖项 `dep` 变化时才运行，用于响应 `props` 或 `state` 的变化。
*   `useEffect` 可以返回一个**清理函数**，用于在组件卸载或 effect 重新运行前执行清理工作（如移除事件监听、取消订阅）。
*   **最重要的原则**：诚实地将 effect 内部用到的所有 `props` 和 `state` 都列入依赖项数组，以避免“陈旧闭包”等难以调试的 bug。