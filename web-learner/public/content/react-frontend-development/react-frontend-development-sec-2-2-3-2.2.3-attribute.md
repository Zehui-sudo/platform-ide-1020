好的，作为一位资深的技术教育作者，我将为你撰写这篇关于“在JSX中指定属性”的教学段落。

---

### 2.2.3 工具二：指定属性(Attribute)

在上一节中，我们学会了如何使用JSX创建基本的UI元素，就像搭建了房子的骨架。现在，我们要为这个骨架“添砖加瓦”，赋予它更多的信息和功能，比如为图片指定来源、为段落添加样式、或者让一个按钮可以被点击。这就是通过为JSX元素**指定属性**来实现的。

JSX中的属性指定，在很大程度上借鉴了HTML的语法，但有几个至关重要的区别，这也是React初学者最容易混淆的地方。让我们逐一攻克。

#### 基础属性：与HTML的相似之处

对于大多数属性，JSX的写法与你在HTML中的经验完全一致。你可以使用双引号 `""` 来传递字符串作为属性值。

***
<div class="code_example">
<p><strong>代码示例：创建一个带链接的图片</strong></p>
<p>一个常见的场景是创建一个可点击的图片。在HTML中，你会用一个 <code>&lt;a&gt;</code> 标签包裹一个 <code>&lt;img&gt;</code> 标签。</p>
<pre><code class="language-jsx">
// 一个简单的图片链接组件
const imageLink = (
  &lt;a href="https://react.dev" target="_blank"&gt;
    &lt;img 
      id="react-logo"
      src="logo.svg" 
      alt="React Logo" 
    /&gt;
  &lt;/a&gt;
);

// 你可以将 imageLink 渲染到页面上
</code></pre>
<p>在这个例子中，<code>href</code>, <code>target</code>, <code>id</code>, <code>src</code>, 和 <code>alt</code> 的用法都和原生HTML完全相同，非常直观。</p>
</div>
***

#### 关键差异点：React的“特别规定”

尽管有相似之处，但为了与JavaScript的语法更好地融合，React对一些特定属性做了调整。掌握这些差异是写出正确React代码的关键。

##### 1. `className` 而不是 `class`

这是最常见也最重要的一个区别。在HTML中，我们使用 `class` 属性来为元素指定CSS类。但在JavaScript中，`class` 是一个用于创建类的保留关键字。为了避免冲突，**在JSX中，你必须使用 `className` 来代替 `class`**。

***
<div class="comparison">
<p><strong>对比：HTML vs. JSX</strong></p>
<table>
<thead>
<tr>
<th></th>
<th>HTML</th>
<th>JSX</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>语法</strong></td>
<td><code>&lt;div class="user-profile"&gt;...&lt;/div&gt;</code></td>
<td><code>&lt;div className="user-profile"&gt;...&lt;/div&gt;</code></td>
</tr>
</tbody>
</table>
</div>

<div class="common_mistake_warning">
<p><strong>⚠️ 常见错误警告</strong></p>
<p>如果你不小心写了 <code>class</code>，React通常会在浏览器的控制台中给出一个警告。虽然在某些情况下页面可能仍然能“看似正常”地工作，但这是一种错误实践，应该立即修正为 <code>className</code>。</p>
</div>
***

##### 2. `style` 属性接收一个对象

在HTML中，`style` 属性接收一个包含CSS规则的字符串。但在JSX中，为了更好地利用JavaScript的动态能力，**`style` 属性接收一个JavaScript对象**。

这个语法看起来有点特别：`style={{...}}`。

*   **第一层花括号 `{}`**：表示这是一个JSX的表达式，我们需要在其中嵌入JavaScript代码。
*   **第二层花括号 `{}`**：表示我们传入的是一个JavaScript对象字面量。

此外，这个对象中的CSS属性名需要遵循**小驼峰命名法（camelCase）**，而不是CSS中带连字符的命名法。例如，`background-color` 变成 `backgroundColor`，`font-size` 变成 `fontSize`。

***
<div class="code_example">
<p><strong>代码示例：使用内联样式</strong></p>
<pre><code class="language-jsx">
// 定义一个样式对象
const errorTextStyle = {
  color: 'red',
  fontSize: '14px',
  backgroundColor: '#fdd', // 注意是 backgroundColor
  padding: '10px',
  borderRadius: '5px'
};

// 在JSX中应用这个样式对象
const errorMessage = (
  &lt;p style={errorTextStyle}&gt;
    错误：用户名或密码不正确。
  &lt;/p&gt;
);

// 或者直接以内联对象形式提供
const successMessage = (
  &lt;p style={{ color: 'green', fontSize: '14px' }}&gt;
    登录成功！
  &lt;/p&gt;
);
</code></pre>
</div>
***

##### 3. 事件处理：`onClick` 等驼峰命名

在HTML中，事件处理器通常是全小写的，如 `onclick`, `onchange`。在JSX中，这些事件处理器同样遵循小驼峰命名法，如 `onClick`, `onChange`。

更重要的是，传递给事件处理器的值**不是一个字符串，而是一个JavaScript函数**。我们将在后续章节深入探讨事件处理，这里先了解其命名和值的类型。

***
<div class="comparison">
<p><strong>对比：HTML vs. JSX</strong></p>
<table>
<thead>
<tr>
<th></th>
<th>HTML</th>
<th>JSX</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>语法</strong></td>
<td><code>&lt;button onclick="alert('Clicked!')"&gt;...&lt;/button&gt;</code></td>
<td><code>&lt;button onClick={() => alert('Clicked!')}&gt;...&lt;/button&gt;</code></td>
</tr>
<tr>
<td><strong>值类型</strong></td>
<td>字符串</td>
<td>函数</td>
</tr>
</tbody>
</table>
</div>
***

#### 要点回顾

现在，我们已经掌握了为JSX元素添加属性的“第二件工具”。虽然大部分属性与HTML类似，但请务必牢记以下三个核心差异：

*   **CSS 类名**：使用 `className` 而不是 `class`。
*   **内联样式**：`style` 属性接收一个JavaScript对象，且属性名需使用小驼峰命名法（`backgroundColor`）。
*   **事件监听**：事件处理器（如 `onClick`）同样使用小驼峰命名，并接收一个函数作为值。

熟练掌握这些规则，你就能自如地为你的React组件添加丰富的外观和行为了。