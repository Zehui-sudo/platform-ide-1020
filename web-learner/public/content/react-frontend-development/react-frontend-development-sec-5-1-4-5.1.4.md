好的，我将以资深技术教育作者的身份，紧密衔接前面的内容，为您续写 **5.1.4 第三步：创建导航链接**。

---

我们已经成功地为应用规划了“城市地图”（路由表），并且通过手动修改浏览器地址栏验证了不同路径会展示不同“景点”（页面组件）。但这显然不是最终的用户体验。用户需要的是清晰、可点击的导航入口，而不是去当一个需要背诵URL的“黑客”。

这一步，我们的任务就是构建用户与路由系统交互的桥梁——导航链接。我们将学习为何不能使用传统的`<a>`标签，并掌握React Router提供的专属解决方案：`<Link>`组件。

### 5.1.4 第三步：创建导航链接

现在，让我们在所有页面共享的头部区域，添加一个真正的导航栏。

#### 为什么不能直接使用 `<a>` 标签？

在传统的HTML中，创建链接的唯一方式就是使用`<a>`标签，例如 `<a href="/about">关于我们</a>`。直觉上，我们可能会想在React应用中也这样做。让我们先尝试一下，看看会发生什么。

<div class="code_example">

**在 `App.jsx` 中尝试使用 `<a>` 标签:**
```jsx
// src/App.jsx
// ... (imports remain the same)

function App() {
  return (
    <div className="App">
      <header>
        <h1>我的应用</h1>
        <nav>
          {/* 警告：这是错误的做法！ */}
          <a href="/">首页</a> | 
          <a href="/about">关于</a> | 
          <a href="/products">产品</a>
        </nav>
      </header>

      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/products" element={<ProductsPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
```

</div>

现在运行应用，你会发现链接确实可以点击，页面内容也确实在变化。**但请仔细观察浏览器标签页**——每次点击，标签页都会出现一个短暂的加载指示器，页面可能会闪一下白屏。

这正是我们在 `5.1.1` 节中极力避免的**整页刷新**！

使用 `<a>` 标签，我们等于绕过了React Router精心构建的客户端路由系统，直接向浏览器下达了“请求一个新页面”的传统指令。浏览器忠实地执行了它，向服务器请求了新的HTML文档（尽管服务器可能只是返回了同一个 `index.html`），并重新加载了整个React应用。我们之前为实现流畅SPA体验所做的一切努力都付诸东流。

#### 正确的方式：使用 `<Link>` 组件

为了解决这个问题，`react-router-dom` 包提供了一个专门的 `<Link>` 组件。它就是我们一直在寻找的、能够与客户端路由无缝协作的“智能链接”。

`<Link>` 组件在最终渲染到DOM时，会被解析成一个标准的 `<a>` 标签，保证了HTML的语义化和可访问性。但它的核心魔力在于其点击事件处理：

1.  **拦截点击**：当你点击一个 `<Link>` 组件时，它会阻止浏览器的默认跳转行为。
2.  **更新URL**：它会使用History API，在不刷新的情况下悄悄更新浏览器地址栏的URL。
3.  **通知路由**：它会通知 `<Routes>` 组件URL已经改变，触发其重新匹配并渲染对应的页面组件。

<div class="code_example">

**在 `App.jsx` 中正确使用 `<Link>`:**

```jsx
// src/App.jsx

// 1. 从 react-router-dom 额外引入 Link 组件
import { Routes, Route, Link } from 'react-router-dom';

import HomePage from './pages/HomePage';
import AboutPage from './pages/AboutPage';
import ProductsPage from './pages/ProductsPage';
import NotFoundPage from './pages/NotFoundPage';

function App() {
  return (
    <div className="App">
      <header>
        <h1>我的应用</h1>
        {/* 2. 创建导航栏 */}
        <nav>
          {/* 3. 使用 <Link> 组件替代 <a> 标签 */}
          {/*    注意：属性名是 `to` 而不是 `href` */}
          <Link to="/">首页</Link> | 
          <Link to="/about">关于</Link> | 
          <Link to="/products">产品</Link>
        </nav>
      </header>

      <main>
        {/* 路由表保持不变 */}
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/products" element={<ProductsPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
```

</div>

现在，再次运行你的应用。点击导航栏中的链接，你会体验到真正的SPA魔力：URL在变，内容在变，但页面**完全没有刷新**。切换如丝般顺滑，这正是我们追求的“应用感”体验。

<div class="comparison">

#### 对比：`<a href="...">` vs. `<Link to="...">`

| 特性 | `<a href="...">` (传统HTML标签) | `<Link to="...">` (React Router组件) |
| :--- | :--- | :--- |
| **核心作用** | 在文档间创建超链接。 | 在单页应用内部的“视图”间导航。 |
| **点击行为** | 触发浏览器向服务器发起新请求，导致**整页刷新**。 | **阻止**默认行为，通过History API更新URL，不刷新页面。 |
| **底层机制** | HTTP请求/响应模型。 | 客户端JavaScript接管，进行DOM局部更新。 |
| **适用场景** | 跳转到外部网站，或在MPA中进行页面跳转。 | **构建SPA时进行内部页面导航的唯一正确选择**。 |
| **使用前提** | 无，HTML标准元素。 | 必须在由 `<BrowserRouter>` 包裹的组件树内部使用。 |

</div>

---

### ✅ 第三步核对清单

我们成功地为用户添加了可交互的导航功能，让我们的单页应用真正“活”了起来。

- [x] **理解 `<a>` 的局限性**：认识到在SPA中使用原生`<a>`标签进行内部导航会导致破坏性的整页刷新。
- [x] **引入并使用 `<Link>`**：从 `react-router-dom` 导入 `Link` 组件。
- [x] **掌握 `to` 属性**：记住 `<Link>` 使用 `to` 属性来指定目标路径，而不是 `href`。
- [x] **实现无刷新导航**：通过将所有内部导航都替换为 `<Link>` 组件，实现了流畅的、无缝的页面切换体验。

我们的应用现在功能完备，用户可以在不同页面间自由穿梭。但从UI/UX的角度看，还缺少一个细节：用户如何知道自己当前在哪一个页面？导航栏中当前激活的链接通常需要一个高亮样式。在下一节，我们将学习如何使用一个更强大的链接组件——`<NavLink>`来轻松实现这个功能。