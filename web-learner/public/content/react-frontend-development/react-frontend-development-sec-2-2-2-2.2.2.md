好的，作为一位资深的技术教育作者，我将为你撰写这篇关于“在JSX中使用花括号嵌入动态表达式”的教学段落。

---

### 2.2.2 工具一：使用花括号`{}`嵌入动态表达式

在上一节中，我们学习了如何像编写 HTML 一样来书写 JSX，创建了静态的用户界面结构。但这仅仅是开始。一个应用的强大之处在于其动态性——能够根据用户数据、程序状态或计算结果来展示不同的内容。如果我们的界面只能显示写死的文本，那它和一张静态图片没有太大区别。

那么，我们如何在 JSX 这片“类 HTML”的领土上，注入来自 JavaScript 世界的动态能量呢？React 为此提供了一个极其简洁且强大的工具——**花括号 `{}`**。

你可以将花括号 `{}` 理解为 JSX 中的一个“魔法传送门”。一旦在 JSX 中使用了它，你就可以在其中编写任何合法的 JavaScript **表达式**（Expression），React 会计算这个表达式的结果，并将其渲染到最终的 UI 中。

让我们通过几个核心场景来掌握这个强大的工具。

#### 1. 嵌入变量

这是最基础也是最常见的用法。你可以直接将 JavaScript 变量或常量嵌入到 JSX 中。

`code_example`
```jsx
const userName = "Alice";
const userAge = 28;

// 在 JSX 中直接使用这些变量
const welcomeMessage = (
  <h1>
    你好, {userName}! 欢迎来到 React 的世界。
    你今年 {userAge} 岁了。
  </h1>
);

// ReactDOM.render(welcomeMessage, document.getElementById('root'));
// 浏览器将显示：你好, Alice! 欢迎来到 React 的世界。你今年 28 岁了。
```

#### 2. 进行算术运算

花括号内可以直接进行数学计算，其计算结果会被渲染出来。

`code_example`
```jsx
const price = 99.8;
const quantity = 3;

const shoppingCartInfo = (
  <div>
    <h2>订单详情</h2>
    <p>商品单价：¥{price}</p>
    <p>购买数量：{quantity}</p>
    <p>总计金额：¥{price * quantity}</p> 
  </div>
);

// 浏览器将显示总计金额：¥299.4
```

#### 3. 调用函数

你可以调用一个函数，并将其返回值渲染到界面上。这使得封装复杂的UI逻辑成为可能。

`code_example`
```jsx
// 定义一个格式化用户名的函数
function formatUserName(user) {
  if (user) {
    return `${user.firstName} ${user.lastName}`;
  }
  return '陌生人';
}

const currentUser = {
  firstName: 'Chris',
  lastName: 'Wang'
};

const greeting = <h2>欢迎回来, {formatUserName(currentUser)}!</h2>; // "欢迎回来, Chris Wang!"

const guestGreeting = <h2>欢迎你, {formatUserName(null)}!</h2>; // "欢迎你, 陌生人!"
```

#### 4. 访问对象属性与在属性中使用

不仅可以在标签内容中嵌入表达式，还可以在标签的**属性**（Attributes）中使用花括号。这对于动态设置 `src`、`href`、`className` 等属性至关重要。

`code_example`
```jsx
const userProfile = {
  name: '开发者小明',
  avatarUrl: 'https://i.pravatar.cc/150?u=a042581f4e29026704d', // 一个随机头像图片URL
  theme: 'dark-theme'
};

const profileCard = (
  <div className={userProfile.theme}>
    {/* 属性中的花括号 */}
    <img 
      src={userProfile.avatarUrl} 
      alt={`${userProfile.name}的头像`} 
    />
    {/* 内容中的花括号 */}
    <h1>{userProfile.name}</h1>
  </div>
);

// 这段 JSX 将生成一个 div，其 class 是 "dark-theme"，
// img 的 src 和 alt 属性都来自 userProfile 对象。
```
**注意**：在 JSX 中，HTML 的 `class` 属性需要写成 `className`，这是 JSX 的一个特殊规则，我们将在后续章节中详细探讨。

#### 一个重要的规则：花括号内只能放表达式

请务必记住，`{}` 中只能包含 **JavaScript 表达式**，而不能是**语句**（Statement）。

*   **表达式（Expression）**：任何可以计算出值的代码片段。例如 `2 + 2`、`user.name`、`formatName()`。
*   **语句（Statement）**：执行某个动作的代码。例如 `if...else` 块、`for` 循环、变量声明 `let x = 5;`。

因此，你不能在 JSX 的花括号中直接使用 `if/else` 语句。

```jsx
// ❌ 错误的做法
<div>
  {
    if (user.isLoggedIn) {
      return <p>欢迎回来！</p>;
    } else {
      return <p>请登录。</p>;
    }
  }
</div>
```

不过别担心，React 提供了其他更优雅的方式来实现条件渲染（例如使用三元运算符或逻辑与运算符），我们很快就会学到。

---

`checklist`
#### 要点回顾

*   **核心工具**：花括号 `{}` 是在 JSX 中嵌入动态内容的唯一方式。
*   **功能**：它充当了从 JSX 到 JavaScript 的“入口”，允许你执行 JavaScript 代码。
*   **内容**：花括号内可以放置任何合法的 JavaScript **表达式**，包括变量、算术运算、函数调用、对象属性访问等。
*   **位置**：不仅可以用于标签之间的文本内容，也可以用于标签的属性值中，如 `src={imageUrl}`。
*   **限制**：不能在花括号内直接使用 `if/else` 等 JavaScript **语句**。