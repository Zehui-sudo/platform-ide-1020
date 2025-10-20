好的，作为一位资深的技术教育作者，我将为你撰写这篇关于“用自定义Hooks封装状态逻辑”的教学段落。

---

### 6.2.2 实践二：用自定义Hooks封装状态逻辑

继上一节我们探讨了通过合理的组件拆分来提升代码可维护性之后，本节我们将深入到另一个关键领域：**逻辑的复用**。在React函数式组件的开发中，我们经常会发现，不同的组件需要处理相似的、带有状态的逻辑。此时，简单地复制粘贴代码显然是不可取的，它会造成代码冗余，并给未来的维护带来噩梦。

自定义Hook正是React为解决这一问题提供的优雅方案。它允许我们将组件逻辑提取到可重用的函数中，实现状态逻辑的封装与共享。

#### 案例研究：一个普遍的需求——追踪浏览器窗口尺寸

想象一个场景：你的应用中有多个组件需要根据浏览器窗口的尺寸变化来调整自身的布局或行为。

*   一个 `ResponsiveHeader` 组件，在窗口宽度小于768px时显示汉堡菜单，大于768px时显示完整的导航链接。
*   一个 `ProductList` 组件，在宽屏下每行显示4个商品，窄屏下每行显示2个。

让我们看看在不使用自定义Hook的情况下，这两个组件的代码会是什么样子。

**最初的实现（代码重复）**

```jsx
// ResponsiveHeader.jsx
import React, { useState, useEffect } from 'react';

function ResponsiveHeader() {
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);

  useEffect(() => {
    const handleResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    
    // 关键：组件卸载时必须清理监听器，防止内存泄漏
    return () => window.removeEventListener('resize', handleResize);
  }, []); // 空依赖数组确保此 effect 仅在挂载和卸载时运行

  return (
    <header>
      {windowWidth < 768 ? (
        <span>🍔 Menu</span>
      ) : (
        <nav>Home | Products | About</nav>
      )}
    </header>
  );
}

// ProductList.jsx
import React, { useState, useEffect } from 'react';

function ProductList() {
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);

  // 警告：这里的状态逻辑与 ResponsiveHeader 组件完全重复！
  useEffect(() => {
    const handleResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const columns = windowWidth > 1024 ? 4 : 2;
  
  return (
    <div>
      <h2>Our Products ({columns} columns)</h2>
      {/* ... 商品列表渲染逻辑 ... */}
    </div>
  );
}
```

显而易见，`useState` 和 `useEffect` 这一整块关于监听窗口大小的逻辑在两个组件中被完整地复制了一遍。如果我们还需要第三个、第四个响应式组件，代码的冗余度将急剧上升。

#### 解决方案：提取逻辑到自定义Hook

自定义Hook的本质是一个**以 `use` 开头的JavaScript函数**，它可以在内部调用其他的Hook（如 `useState`, `useEffect` 等）。现在，让我们将上述重复的逻辑提取到一个名为 `useWindowSize` 的自定义Hook中。

**1. 创建 `useWindowSize.js`**

```javascript
// hooks/useWindowSize.js
import { useState, useEffect } from 'react';

export function useWindowSize() {
  const [windowSize, setWindowSize] = useState({
    width: window.innerWidth,
    height: window.innerHeight,
  });

  useEffect(() => {
    // 定义resize处理函数
    function handleResize() {
      setWindowSize({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    }

    // 添加事件监听器
    window.addEventListener('resize', handleResize);

    // 立即执行一次，以确保初始尺寸正确
    handleResize();

    // 返回一个清理函数，在组件卸载时移除监听器
    return () => window.removeEventListener('resize', handleResize);
  }, []); // 空依赖数组意味着此effect仅在挂载时运行一次

  // 返回组件所需的状态
  return windowSize;
}
```

这个 `useWindowSize` 函数做了三件事：
1.  用 `useState` 创建并管理 `windowSize` 状态。
2.  用 `useEffect` 封装了添加和移除 `resize` 事件监听器的副作用。
3.  将最新的 `windowSize` 对象返回给调用它的组件。

**2. 重构组件：更清晰、更简洁**

现在，我们可以用这个自定义Hook来重构之前的组件，你会发现它们变得异常整洁和专注。

```jsx
// ResponsiveHeader.jsx (重构后)
import React from 'react';
import { useWindowSize } from './hooks/useWindowSize'; // 导入自定义Hook

function ResponsiveHeader() {
  const { width } = useWindowSize(); // 一行代码即可获取窗口宽度

  return (
    <header>
      {width < 768 ? (
        <span>🍔 Menu</span>
      ) : (
        <nav>Home | Products | About</nav>
      )}
    </header>
  );
}

// ProductList.jsx (重构后)
import React from 'react';
import { useWindowSize } from './hooks/useWindowSize'; // 复用同一个Hook

function ProductList() {
  const { width } = useWindowSize(); // 同样一行代码，逻辑完全复用
  const columns = width > 1024 ? 4 : 2;
  
  return (
    <div>
      <h2>Our Products ({columns} columns)</h2>
      {/* ... 商品列表渲染逻辑 ... */}
    </div>
  );
}
```

通过这次重构，我们实现了：
*   **代码复用 (DRY - Don't Repeat Yourself)**：状态逻辑只编写了一次，可以在任意组件中使用。
*   **关注点分离**：组件本身不再关心如何监听窗口尺寸，只关心如何根据尺寸进行渲染，其职责更加单一。
*   **可维护性提升**：如果未来需要修改监听逻辑（例如增加节流防抖），我们只需修改 `useWindowSize` 这一个地方。

#### 自定义Hook的核心原则

1.  **命名约定**：自定义Hook必须以 `use` 开头。这是React的硬性规定，React Linter会依赖这个约定来检查你是否违反了Hook的使用规则（例如，不能在条件语句中调用Hook）。
2.  **隔离状态，共享逻辑**：这是最关键的概念。每个调用 `useWindowSize` 的组件都会获得**自己独立的状态**。`ResponsiveHeader` 的 `width` 和 `ProductList` 的 `width` 是两个独立的state变量，它们只是通过同一个逻辑函数进行更新。自定义Hook共享的是**状态处理的逻辑**，而非**状态本身**。

#### 何时应该创建自定义Hook？

一个简单的经验法则是：**当你发现自己在多个组件之间复制粘贴包含`useState`、`useEffect`或其它Hook的逻辑时，就是创建自定义Hook的最佳时机。**

常见的自定义Hook应用场景包括：
*   数据获取 (`useFetch`)
*   表单状态管理 (`useForm`)
*   与浏览器API交互，如LocalStorage (`useLocalStorage`) 或地理位置 (`useGeolocation`)
*   实现动画效果 (`useAnimation`)

---

#### 本节小结

通过本节的学习，我们掌握了React工程实践中一项至关重要的技能——封装和复用状态逻辑。

*   **目的**：自定义Hook旨在解决不同组件间状态逻辑重复的问题，遵循DRY原则。
*   **实现**：它是一个以`use`开头的JS函数，内部可以调用其他React Hooks。
*   **核心价值**：它实现了**逻辑共享**与**状态隔离**，让组件代码更简洁、更具可读性和可维护性。

在你的项目中，积极地将通用逻辑提取为自定义Hook，是迈向编写高质量、可维护React应用的关键一步。