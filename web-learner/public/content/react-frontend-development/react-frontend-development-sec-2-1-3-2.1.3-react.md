好的，作为一位资深的技术教育作者，我将紧密衔接前一节对React组件核心特性的介绍，自然地过渡并续写 **2.1.3 现代React的选择：函数式组件** 的内容。

---

### 2.1.3 现代React的选择：函数式组件

在前面的小节中，我们接触到的所有组件示例，比如 `WelcomeMessage` 和 `Comment`，都是以JavaScript函数的形式出现的。这简洁明了，也符合我们对组件“输入-处理-输出”模型的直观理解。

然而，如果你翻阅一些较早的React项目代码或教程，你很可能会遇到另一种基于ES6 Class语法的组件写法。为了让你在学习之路上不感困惑，并明确我们接下来的技术方向，是时候来了解一下React组件的“前世今生”了。

#### 组件的两种“范式”：类与函数

在React的历史上，主要存在过两种定义组件的方式：**类组件（Class Components）** 和 **函数式组件（Functional Components）**。

*   **类组件 (Class Components)**：这是早期React中构建有状态、有复杂逻辑组件的**唯一**方式。它使用ES6的 `class` 语法，继承自 `React.Component`，并且依赖于 `this` 关键字来访问 `props` 和 `state`，同时通过特定的生命周期方法（如 `componentDidMount`）来处理副作用（如API请求）。

*   **函数式组件 (Functional Components)**：在早期，函数式组件非常纯粹，它们只是接收 `props` 并返回JSX的函数。因为无法拥有自己的状态（state）和生命周期方法，它们通常被用作“无状态组件”或“展示型组件”（Dumb Components），只负责UI的渲染。

这个分水岭出现在2019年，React 16.8版本正式发布了 **Hooks** API。Hooks 是一系列特殊的函数（例如我们将在后续章节深入学习的 `useState`, `useEffect` 等），它们允许你“钩入”React的状态和生命周期等特性。

它的出现，彻底改变了游戏规则：**函数式组件从此拥有了与类组件同等甚至更强大的能力。**

#### 代码对比：同一个计数器，两种不同的人生

让我们通过一个最经典的“计数器”例子，直观地感受一下两种写法的差异。

| 类组件 (Class Component) - 旧范式 | 函数式组件 (Functional Component) - 现代范式 |
| :--- | :--- |
| **关注点：** 繁琐的模板代码，`this` 的指向问题，以及分散的生命周期逻辑。 | **关注点：** 直观的数据流，简洁的语法，以及通过Hooks按功能组织代码。 |
| ```jsx
// Counter.js (Class Component)
import React from 'react';

class Counter extends React.Component {
  // 1. 必须用 constructor 初始化 state
  constructor(props) {
    super(props);
    this.state = { count: 0 };
  }

  // 2. 方法需要绑定 this (或使用箭头函数)
  handleIncrement = () => {
    // 3. 通过 this.setState 更新状态
    this.setState({ count: this.state.count + 1 });
  };
  
  // 4. UI 必须在 render 方法中返回
  render() {
    return (
      <div>
        <p>You clicked {this.state.count} times</p>
        <button onClick={this.handleIncrement}>
          Click me
        </button>
      </div>
    );
  }
}
``` | ```jsx
// Counter.js (Functional Component with Hooks)
import React, { useState } from 'react';

function Counter() {
  // 1. 直接使用 useState Hook 声明一个状态变量
  const [count, setCount] = useState(0);

  // 2. 直接定义一个处理函数
  const handleIncrement = () => {
    // 3. 调用状态更新函数来更新状态
    setCount(count + 1);
  };

  // 4. 直接返回 UI
  return (
    <div>
      <p>You clicked {count} times</p>
      <button onClick={handleIncrement}>
        Click me
      </button>
    </div>
  );
}
``` |
| 代码量更多，需要理解 `class`、`constructor`、`super()` 和 `this` 的概念。 | 代码更少，逻辑更集中，更接近纯粹的JavaScript函数，心智负担更小。 |

#### 为何我们拥抱函数式组件？

对比之后，答案显而易见。自Hooks诞生以来，整个React社区和官方团队都已将重心全面转向函数式组件。这不仅仅是代码风格的偏好，更是因为它带来了实实在在的优势：

1.  **更简洁、可读性更高**：没有了 `this` 的困扰，没有了类相关的模板代码，代码更短，意图更清晰。
2.  **逻辑复用更优雅**：通过自定义Hooks，我们可以轻松地提取和共享有状态的逻辑（例如，获取数据、订阅事件等），这比类组件时代的高阶组件（HOCs）和渲染属性（Render Props）模式要简单和灵活得多。
3.  **更易于测试**：函数更容易被测试，因为它们通常更“纯”，依赖关系更明确。
4.  **拥抱未来**：React团队未来的所有新特性、性能优化（如并发模式）都将围绕函数式组件和Hooks构建。学习它，就是投资未来。

基于以上压倒性的优势，**本课程将完全采用现代的函数式组件与Hooks进行教学。** 我们会跳过类组件的冗余历史包袱，直接带你进入最高效、最前沿的React开发世界。

---

#### 本节小结

通过本节，我们明确了学习路径。你不必再为网上看到的两种组件写法感到困惑，因为你已经知道了它们背后的历史演变和技术优劣。

**要点回顾：**

*   **两种范式**：React历史上存在类组件和函数式组件两种写法。
*   **游戏改变者**：**Hooks** 的出现（React 16.8+），让函数式组件具备了管理状态和生命周期的能力，使其成为主流。
*   **现代选择**：函数式组件因其简洁、易于复用逻辑、没有 `this` 困扰等优点，已成为当今React开发的事实标准。
*   **课程聚焦**：本课程将**100%采用函数式组件与Hooks**进行教学，确保你学到的是最现代、最实用的React技术。

现在，我们已经扫清了历史障碍，确立了前进的方向。从下一个小节开始，我们将正式卷起袖子，学习编写React组件的“方言”——JSX。