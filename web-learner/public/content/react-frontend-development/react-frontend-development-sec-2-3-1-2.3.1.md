好的，我们紧接上一节对组件“蓝图”概念的介绍，开始动手实践。

### 2.3.1 第一步：编写你的第一个函数式组件

理论说得再多，不如亲手实践。现在，让我们卷起袖子，将“组件是UI蓝图”这一抽象概念，转化为看得见、摸得着的代码。在React中，函数式组件是最常用也是最直接的组件形式。

#### 什么是函数式组件？

从本质上讲，一个React函数式组件就是一个普通的JavaScript函数，但它需要遵循两个核心约定：

1.  **首字母大写**：组件的函数名必须以大写字母开头，例如 `MyComponent` 而不是 `myComponent`。这是React区分普通HTML标签（如 `div`）和自定义组件（如 `<MyComponent />`）的关键规则。
2.  **返回JSX**：这个函数必须返回一个React元素，通常是通过JSX语法编写的。这个返回值描述了该组件应该渲染成什么样子的UI。

准备好了吗？让我们来创建第一个组件。

---

### `code_example`：创建 `Greeting` 组件

假设我们正在构建一个简单的个人主页，我们首先需要一个欢迎标语。这个标语就是一个完美的、独立的UI单元，非常适合作为我们的第一个组件。

1.  **创建组件文件**

    在你的项目 `src` 目录下，新建一个文件，命名为 `Greeting.js`。将组件放在独立的文件中是React开发的最佳实践，它能让你的项目结构保持清晰和模块化。

2.  **编写组件代码**

    在 `Greeting.js` 文件中，输入以下代码：

    ```javascript
    // src/Greeting.js

    // 这是一个最基础的函数式组件
    function Greeting() {
      // 它返回一段描述UI的JSX
      return (
        <div className="greeting-card">
          <h1>你好，React！</h1>
          <p>这是我的第一个组件，旅程开始了！</p>
        </div>
      );
    }

    // 使用 export default 将组件导出，以便其他文件可以导入并使用它
    export default Greeting;
    ```

    **代码解析**：
    *   `function Greeting() { ... }`：我们定义了一个名为 `Greeting` 的JavaScript函数，注意首字母 `G` 是大写的。
    *   `return (...)`：函数返回了一段JSX。使用圆括号包裹多行JSX是一个好习惯，可以避免JavaScript自动在换行处插入分号导致的潜在错误。
    *   `<div className="greeting-card">...</div>`：这里看起来和HTML几乎一样，但请注意 `class` 属性被写成了 `className`。这是因为 `class` 是JavaScript的保留关键字，在JSX中需要用 `className` 来代替。
    *   `export default Greeting;`：这行代码是ES6模块语法，它允许我们将 `Greeting` 函数作为这个文件的默认导出。这样，在其他文件中就可以轻松地引入这个组件了。

#### 将组件渲染到屏幕上

我们已经设计好了 `Greeting` 这张“蓝图”，但它还只是存在于代码中。要让用户在浏览器中看到它，我们需要一个“施工队”——`ReactDOM`——来将它“建造”到网页的DOM（文档对象模型）中。

通常，这个“建造”过程发生在项目的入口文件，比如 `src/index.js` 或 `src/main.jsx`。

打开你的入口文件，修改代码如下：

```javascript
// src/index.js

import React from 'react';
import ReactDOM from 'react-dom/client';

// 1. 从 './Greeting.js' 文件中导入我们刚刚创建的组件
import Greeting from './Greeting'; 
// 假设你有一个 index.css 文件用于样式
import './index.css'; 

// 2. 找到HTML中的根节点，React应用将挂载在这里
const rootElement = document.getElementById('root');

// 3. 创建一个React根
const root = ReactDOM.createRoot(rootElement);

// 4. 使用 root.render() 将我们的组件渲染到DOM中
root.render(
  <React.StrictMode>
    <Greeting /> 
  </React.StrictMode>
);
```

**关键步骤解析**：
1.  **导入 (`import`)**：我们使用 `import Greeting from './Greeting';` 来引入我们编写的组件。现在，`Greeting` 这个变量就代表了我们的组件函数。
2.  **使用 (`<Greeting />`)**：这是最神奇的地方！我们像使用普通HTML标签一样，直接在JSX中写下了 `<Greeting />`。当React看到这个语法时，它会知道：“啊，我需要调用 `Greeting` 函数，并将它返回的JSX内容渲染到这个位置。”

现在，启动你的开发服务器并访问应用，你将会在浏览器中看到由你的第一个组件渲染出的欢迎语！

#### 工作流程回顾

让我们用一个简单的流程图来梳理从组件定义到最终显示的全过程：

```mermaid
graph TD
    A[<b>你编写 Greeting.js</b>
定义Greeting函数并返回JSX] --> B{export default Greeting}
    B --> C[<b>你编写 index.js</b>
import Greeting from './Greeting.js']
    C --> D[在JSX中使用 <code>&lt;Greeting /&gt;</code>]
    D --> E["<b>ReactDOM.render()</b>
React的核心渲染引擎"]
    E -->|"调用Greeting()函数"| F["获取返回的JSX: <code>&lt;div&gt;...&lt;/div&gt;</code>"]
    F -->|转换为真实DOM节点| G[<b>浏览器</b>
在 <code>&lt;div id="root"&gt;</code> 中显示内容]

    style A fill:#D6EAF8,stroke:#333,stroke-width:2px
    style C fill:#D6EAF8,stroke:#333,stroke-width:2px
    style G fill:#D5F5E3,stroke:#333,stroke-width:2px
```

### 要点回顾

恭喜你，你已经完成了从0到1的突破！通过这个过程，我们掌握了：

*   **函数式组件的定义**：它是一个返回JSX的、首字母大写的JavaScript函数。
*   **组件的模块化**：通过 `export` 和 `import` 实现组件的定义与使用相分离。
*   **组件的渲染**：`ReactDOM.createRoot().render()` 是连接React世界与真实浏览器DOM的桥梁。
*   **JSX中的组件语法**：使用类似HTML标签的 `<ComponentName />` 语法来实例化和渲染组件。

现在，你已经拥有了构建更复杂应用的基石。在接下来的章节中，我们将学习如何让组件动起来，接收数据，并进行交互。