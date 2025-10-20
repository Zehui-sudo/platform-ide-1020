好的，我将以资深技术教育作者的身份，紧密衔接前面的内容，为您续写 **5.1.3 第二步：定义路由表**。

---

上一节我们成功安装了“导航系统” `<BrowserRouter>`，但它还不知道城市里有哪些具体的地址和目的地。整个应用还像一张白纸，无论URL如何变化，都只能显示 `<App />` 组件的原始内容。

这一步，我们的任务就是绘制这份至关重要的导航地图——也就是定义应用的**路由表（Routing Table）**。路由表是一系列规则的集合，它清晰地告诉React Router：“当用户访问这个URL路径时，请为他渲染那个React组件”。

### 5.1.3 第二步：定义路由表

为了构建这份“地图”，React Router v6 提供了两个核心组件，它们总是形影不离地协同工作：`<Routes>` 和 `<Route>`。

*   **`<Routes>`**: 你可以把它想象成一个智能的**路由交换机**或**规则容器**。它的职责是审视当前浏览器的URL，然后在它内部包裹的所有 `<Route>` 规则中，**只选择并渲染第一个路径匹配**的那一个。这种“唯一匹配”的机制确保了页面上不会同时出现多个页面的内容。

*   **`<Route>`**: 这就是具体的**路由规则**，它像地图上的一条条标注，精确定义了“路径”与“组件”之间的映射关系。它主要通过两个props来工作：
    *   `path`: 一个字符串，定义了需要匹配的URL路径。例如 `path="/about"` 会匹配 `your-app.com/about`。
    *   `element`: 一个React元素（通常是JSX），指定了当路径匹配时应该渲染哪个组件。**关键点**：这里传入的是一个组件的实例，如 `<AboutPage />`，而不是组件的引用 `AboutPage`。

#### 实践：创建你的第一张路由地图

让我们通过一个实际的例子来构建一个包含首页、关于我们和产品列表页面的路由表。

**1. 准备页面组件**

首先，我们需要有可供渲染的“目的地”——也就是我们的页面级组件。在 `src` 目录下创建一个 `pages` 文件夹来存放它们，这是一种良好的项目组织习惯。

```
src/
├── pages/
│   ├── HomePage.jsx
│   ├── AboutPage.jsx
│   └── ProductsPage.jsx
├── App.jsx
└── main.jsx
```

<div class="code_example">

**`src/pages/HomePage.jsx`**
```jsx
function HomePage() {
  return <h1>欢迎来到首页</h1>;
}

export default HomePage;
```

**`src/pages/AboutPage.jsx`**
```jsx
function AboutPage() {
  return <h1>关于我们</h1>;
}

export default AboutPage;
```

**`src/pages/ProductsPage.jsx`**
```jsx
function ProductsPage() {
  return <h1>产品列表</h1>;
}

export default ProductsPage;
```

这些都是最简单的React组件，足以让我们专注于路由逻辑。

</div>

**2. 在 `App.jsx` 中定义路由表**

现在，我们来改造核心的 `App.jsx` 文件。之前它可能包含了一些静态内容，现在我们将它变成路由的“调度中心”。

<div class="code_example">

**`src/App.jsx`**
```jsx
// 1. 从 react-router-dom 引入 Routes 和 Route 组件
import { Routes, Route } from 'react-router-dom';

// 2. 引入我们创建的页面组件
import HomePage from './pages/HomePage';
import AboutPage from './pages/AboutPage';
import ProductsPage from './pages/ProductsPage';

function App() {
  return (
    <div className="App">
      {/* 这里可以放置所有页面共享的布局，比如导航栏、页脚等 */}
      <header>
        <h1>我的应用</h1>
        {/* （我们将在下一节学习如何在这里添加导航链接） */}
      </header>

      <main>
        {/* 3. 使用 <Routes> 包裹所有路由规则 */}
        <Routes>
          {/* 4. 定义每一条路由规则 */}
          {/* 当URL为'/'时，渲染 HomePage 组件 */}
          <Route path="/" element={<HomePage />} />

          {/* 当URL为'/about'时，渲染 AboutPage 组件 */}
          <Route path="/about" element={<AboutPage />} />
          
          {/* 当URL为'/products'时，渲染 ProductsPage 组件 */}
          <Route path="/products" element={<ProductsPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
```

</div>

现在，重启你的应用并手动在浏览器地址栏中输入不同的路径，观察页面的变化：

*   访问 `http://localhost:5173/`，你会看到 “欢迎来到首页”。
*   访问 `http://localhost:5173/about`，页面内容会无刷新地切换为 “关于我们”。
*   访问 `http://localhost:5173/products`，则会显示 “产品列表”。

看！我们的路由表已经生效了。React Router正在监听URL的变化，并根据我们定义的规则，精准地在 `<Routes>` 所在的位置渲染对应的组件。

#### 处理未匹配的路径：创建404页面

如果用户访问了一个我们没有定义的路径，比如 `/contact`，会发生什么？当前页面会变空白，因为没有任何 `<Route>` 的 `path` 能够匹配上。为了提供更好的用户体验，我们应该显示一个“页面未找到”的提示，也就是通称的404页面。

React Router 提供了一个非常优雅的解决方案：使用 `*` 作为 `path` 的通配符。

<div class="code_example">

**1. 创建 `NotFoundPage.jsx` 组件**
```jsx
// src/pages/NotFoundPage.jsx
function NotFoundPage() {
  return <h1>404 - 页面未找到</h1>;
}
export default NotFoundPage;
```

**2. 在 `App.jsx` 中添加通配符路由**
```jsx
// src/App.jsx
import { Routes, Route } from 'react-router-dom';

import HomePage from './pages/HomePage';
import AboutPage from './pages/AboutPage';
import ProductsPage from './pages/ProductsPage';
import NotFoundPage from './pages/NotFoundPage'; // 引入 404 页面

function App() {
  return (
    // ... 省略外部布局 ...
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/about" element={<AboutPage />} />
      <Route path="/products" element={<ProductsPage />} />
      
      {/* 
        关键：将通配符路由放在所有其他路由之后。
        因为 <Routes> 只会渲染第一个匹配的路由，
        所以这个规则只有在以上所有路径都不匹配时才会生效。
      */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
    // ...
  );
}

export default App;
```

</div>

现在，当你访问任何未定义的URL（如 `/whatever` 或 `/contact`）时，应用都会优雅地显示“404 - 页面未找到”的内容。

---

### ✅ 第二步核对清单

我们已经成功地为应用定义了核心的导航规则。回顾一下你学到的关键点：

- [x] **路由表**：是URL路径与React组件之间的映射集合。
- [x] **`<Routes>` 组件**：作为所有路由规则的容器，并确保一次只渲染一个匹配的路由。
- [x] **`<Route>` 组件**：通过 `path` 和 `element` prop 定义单条路由规则。
- [x] **页面组件**：创建独立的组件来代表应用中的不同页面。
- [x] **404处理**：使用 `path="*"` 创建一个通配符路由，以捕获所有未匹配的路径，并务必将其放在路由列表的**最后**。

至此，我们的应用已经有了“灵魂”——能够根据URL的变化展示不同的内容了。但用户还无法通过点击页面上的元素来导航，他们只能手动修改地址栏。这显然不是我们想要的。在下一节中，我们将学习如何创建用户可以交互的导航链接。