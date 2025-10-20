好的，作为一位资深的技术教育作者，我将为你撰写这篇关于ES6模块化的教学段落。

---

### 1.2.5 工具四：ES6模块化 (import/export)

在我们掌握了处理异步流程的 `Promise` 之后，现在我们将目光转向构建大型、可维护应用的组织性基石——模块化系统。这正是 ES6 模块（`import`/`export`）为我们带来的革命性变化，它不仅是现代 JavaScript 的标准，更是 React 组件化思想得以高效实现的技术保障。

#### 为什么模块化对 React 如此重要？

在没有模块化概念的旧时代，JavaScript开发者们常常陷入“全局变量冲突”和“script标签地狱”的困境。所有代码都运行在同一个全局作用域下，很容易互相覆盖、产生意想不到的错误。

ES6 模块系统彻底解决了这个问题。它规定：

1.  **每个文件都是一个独立的模块**：每个文件拥有自己的私有作用域，内部声明的变量、函数、类，不会污染到其他文件。
2.  **显式导出与导入**：模块必须通过 `export` 关键字，明确指定哪些部分可以被外部访问。相应地，其他模块需要通过 `import` 关键字，明确声明它需要引入哪些依赖。

这种机制与 React 的组件化理念不谋而合。在React的世界里，**每一个组件本质上就是一个独立的、可复用的模块**。一个 `Button` 组件文件，它封装了自身的结构（JSX）、样式和行为（事件处理逻辑），然后通过 `export` 将这个组件“暴露”出去。其他任何需要这个按钮的父组件，只需通过 `import` 就能轻松地“拿来使用”，而无需关心其内部复杂的实现细节。

这种清晰的依赖关系，使得大型 React 应用的代码库能够被拆分成成百上千个高内聚、低耦合的小单元（组件），极大地提升了代码的可读性、可维护性和团队协作效率。

#### `export`：开放模块的接口

一个模块可以通过两种主要方式导出其功能：**命名导出（Named Exports）**和**默认导出（Default Export）**。

##### 1. 命名导出 (Named Exports)

一个模块可以有多个命名导出。它非常适合于导出一系列功能相关的工具函数或常量。

```javascript
// src/utils/format.js

// 导出常量
export const MAX_LENGTH = 100;

// 导出一个格式化日期的函数
export function formatDate(date) {
  return new Date(date).toLocaleDateString();
}

// 导出一个处理文本的函数
export const truncateText = (text, length) => {
  return text.length > length ? text.slice(0, length) + '...' : text;
};
```

##### 2. 默认导出 (Default Export)

一个模块**只能有一个**默认导出。它通常用于导出一个模块最核心、最主要的功能。**在React中，这几乎总是用来导出组件本身**。

```jsx
// src/components/Button.jsx

import React from 'react';

function Button({ onClick, children }) {
  return (
    <button className="custom-button" onClick={onClick}>
      {children}
    </button>
  );
}

// 将Button组件作为模块的默认导出
export default Button;
```

#### `import`：引入外部依赖

使用 `import` 语句可以从其他模块中引入功能。导入的语法与导出方式直接对应。

1.  **导入命名导出的成员**：使用花括号 `{}`，且名称必须与导出时完全一致。
    ```javascript
    import { formatDate, truncateText } from '../utils/format.js';
    
    const today = formatDate(new Date());
    const shortStory = truncateText('一个很长很长的故事...', 10);
    ```

2.  **导入默认导出的成员**：直接指定一个变量名来接收，这个名字可以自定义。
    ```javascript
    import MyCustomButton from '../components/Button.jsx';
    
    // 这里的 MyCustomButton 就是 Button.jsx 中导出的 Button 组件
    ```
    习惯上，我们保持导入名称与组件原始名称一致，即 `import Button from ...`。

3.  **混合导入**：最经典的例子莫过于导入 React 自身。
    ```javascript
    // 'react' 模块既有默认导出 (React 对象)，也有命名导出 (如 useState, useEffect等Hooks)
    import React, { useState, useEffect } from 'react';
    ```

#### 实战演练：组装一个简单的应用

让我们看看 `import/export` 是如何将独立的组件和工具函数组织在一起的。

假设我们的项目结构如下：
```
src/
├── components/
│   └── Button.jsx
├── utils/
│   └── format.js
└── App.jsx
```

**`utils/format.js` (命名导出)**
```javascript
export function formatDate(date) {
  return new Date(date).toLocaleDateString();
}
```

**`components/Button.jsx` (默认导出)**
```jsx
import React from 'react';

function Button({ label }) {
  return <button>{label}</button>;
}

export default Button;
```

**`App.jsx` (消费模块)**
```jsx
import React from 'react';
// 导入默认导出的Button组件
import Button from './components/Button';
// 导入命名导出的formatDate函数
import { formatDate } from './utils/format';

function App() {
  const today = formatDate(new Date());

  return (
    <div>
      <h1>欢迎使用React!</h1>
      <p>今天是：{today}</p>
      <Button label="点我!" />
    </div>
  );
}

export default App;
```
在这个例子中，`App` 组件就像一个指挥中心，通过 `import` 精确地引入了它所需要的 `Button` 组件和 `formatDate` 工具函数，清晰、高效地完成了页面的构建。

---

#### 要点回顾

*   **模块即文件**：ES6模块化将每个文件视为一个独立的、拥有私有作用域的模块。
*   **封装与隔离**：模块化有效避免了全局变量污染，增强了代码的封装性。
*   **显式依赖**：通过 `import` 和 `export`，代码的依赖关系变得一目了然，极易于管理和追踪。
*   **两种导出方式**：
    *   **`export default`**：每个模块最多一个，是React组件导出的首选方式。
    *   **`export`**：每个模块可以有多个，常用于导出工具函数、常量等。
*   **支撑组件化**：ES6模块系统是React组件化架构的底层支柱，它让我们可以像搭积木一样，将独立、可复用的组件模块组装成一个复杂而有序的应用程序。