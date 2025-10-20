好的，我将以资深技术教育作者的身份，紧密衔接前面的内容，为您续写 **5.1.5 进阶：处理动态路由与URL参数**。

---

我们已经构建了一个基础但功能完备的SPA，用户可以通过清晰的导航链接在首页、关于和产品页面之间无缝切换。但现实世界的应用远不止于此。设想一下我们的“产品”页面：它不应该只是一个静态的标题，而是一个包含多件商品链接的列表。当用户点击其中一件商品时，应用需要跳转到一个展示**该特定商品详情**的页面。

这就引出了一个核心问题：我们难道要为每一件商品都在路由表中写一条`<Route>`规则吗？
```jsx
// 极其糟糕的设计！
<Route path="/products/1" element={<ProductDetailPage1 />} />
<Route path="/products/2" element={<ProductDetailPage2 />} />
<Route path="/products/iphone-15" element={<ProductDetailPageIphone />} />
// ... 无穷无尽
```
这显然是不可行且无法维护的。我们需要一种更智能的方式来处理这类“模式相同，但具体内容不同”的页面。这正是**动态路由（Dynamic Routes）**大显身手的舞台。

### 5.1.5 进阶：处理动态路由与URL参数

动态路由允许我们在路由路径中定义一个“占位符”，它能匹配URL中对应位置的任意字符串。这个字符串随后会作为参数传递给我们的组件，组件便可以根据这个参数来获取并展示特定的数据。最常见的例子就是商品详情页（`/products/:id`）、用户个人资料页（`/users/:username`）等。

#### 1. 定义动态路由规则

我们首先要做的是修改路由表，告诉React Router如何识别一个产品详情页的URL。我们将使用冒号（`:`）语法来定义URL参数。

<div class="code_example">

**修改 `src/App.jsx` 中的路由表:**

在 `<Routes>` 中，我们在 `/products` 路由下方添加一条新的规则。

```jsx
// src/App.jsx
import { Routes, Route, Link } from 'react-router-dom';
// ... 其他页面组件的 imports
import ProductsPage from './pages/ProductsPage';
import ProductDetailPage from './pages/ProductDetailPage'; // 1. 引入即将创建的详情页组件

function App() {
  return (
    <div className="App">
      {/* ... 省略导航栏部分 ... */}
      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/about" element={<AboutPage />} />
          
          {/* 产品相关的路由 */}
          <Route path="/products" element={<ProductsPage />} />
          {/* 
            2. 定义动态路由
            `:productId` 是一个URL参数（param）。
            它可以匹配 /products/1, /products/apple, /products/any-string 等路径。
            React Router会将匹配到的值（'1', 'apple', 'any-string'）
            以 `productId` 为键名存储起来。
          */}
          <Route path="/products/:productId" element={<ProductDetailPage />} />

          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
```

**关键点**：`path="/products/:productId"` 这个定义非常灵活。路径中以冒号开头的 `productId` 部分就是一个**动态段（dynamic segment）**。React Router 会将匹配到的这部分URL值，与 `productId` 这个名字关联起来。

</div>

#### 2. 创建详情页组件并获取URL参数

路由规则已经就位，现在我们需要创建 `ProductDetailPage` 组件。这个组件的核心任务是：**知道当前URL中的产品ID是什么，然后根据这个ID来渲染内容。**

为了从URL中“提取”出这个动态参数，React Router 提供了一个非常方便的Hook：`useParams`。

<div class="code_example">

**创建 `src/pages/ProductDetailPage.jsx`:**

```jsx
// src/pages/ProductDetailPage.jsx
// 1. 从 react-router-dom 引入 useParams Hook
import { useParams } from 'react-router-dom';

function ProductDetailPage() {
  // 2. 调用 useParams() Hook
  // 它会返回一个对象，键是你在路由中定义的参数名，值是URL中实际匹配到的字符串
  const params = useParams();
  
  // 对于路径 /products/123, params 会是 { productId: '123' }
  // 我们可以使用对象解构来直接获取
  const { productId } = params;

  // 让我们在控制台打印看看
  console.log('URL Params:', params);

  return (
    <div>
      <h1>产品详情页</h1>
      <p>
        您正在查看ID为 <strong>{productId}</strong> 的产品信息。
      </p>
      {/* 在真实应用中，这里会根据 productId 去请求API获取产品数据 */}
    </div>
  );
}

export default ProductDetailPage;
```
现在，如果你手动在浏览器地址栏输入 `http://localhost:5173/products/abc`，页面会渲染出 "您正在查看ID为 abc 的产品信息"。如果输入 `http://localhost:5173/products/99`，则会显示 "...ID为 99 的产品信息"。`useParams` 成功地帮助我们从URL中捕获了动态数据！

</div>

#### 3. 从列表页链接到动态路由

最后一步，也是将整个流程串联起来的关键一步：我们需要在产品列表页（`ProductsPage`）中，为每件产品生成一个指向其对应详情页的 `<Link>`。

<div class="case_study">

**案例研究：改造产品列表页**

让我们把 `ProductsPage` 从一个简单的标题，改造成一个包含真实链接的产品列表。

**`src/pages/ProductsPage.jsx`**

```jsx
import { Link } from 'react-router-dom';

// 模拟从服务器获取的产品数据
const productsData = [
  { id: 'p1', name: 'React 高级编程' },
  { id: 'p2', name: 'JavaScript 设计模式' },
  { id: 'p3', name: '现代CSS权威指南' },
];

function ProductsPage() {
  return (
    <div>
      <h1>产品列表</h1>
      <ul>
        {/* 遍历模拟数据，为每个产品创建一个列表项和链接 */}
        {productsData.map((product) => (
          <li key={product.id}>
            {/* 
              关键：使用模板字符串动态构建 to 属性的值。
              对于id为 'p1' 的产品，链接将指向 '/products/p1'
            */}
            <Link to={`/products/${product.id}`}>{product.name}</Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default ProductsPage;
```
现在，当你访问 `/products` 页面时，你会看到一个可点击的书籍列表。点击“React 高级编程”，应用的URL会无刷新地变为 `/products/p1`，并且 `ProductDetailPage` 组件会正确地渲染，显示出 "您正在查看ID为 p1 的产品信息"。

</div>

我们成功地将静态列表页、动态路由定义和参数获取组件完美地结合在了一起，构建了一个常见且实用的“列表-详情”导航模式。

---

### ✅ 要点回顾

通过本节的学习，我们掌握了React Router中一个极其强大的功能：

-   **定义动态路由**: 在 `<Route>` 的 `path` 属性中使用冒号语法（如 `path="/users/:id"`）来定义URL参数占位符。
-   **捕获URL参数**: 在需要接收参数的组件内部，使用 `useParams()` Hook。它返回一个包含所有URL参数键值对的对象。
-   **动态生成链接**: 在创建指向动态路由的 `<Link>` 时，利用模板字符串（` `` `）或字符串拼接，将变量（如产品ID）嵌入到 `to` 属性中，例如 `<Link to={\`/products/${product.id}\`}>`。

掌握了动态路由，你就解锁了构建绝大多数真实世界Web应用的能力，从博客文章、电商商品详情到社交媒体的用户主页，其背后都是这一核心机制在驱动。