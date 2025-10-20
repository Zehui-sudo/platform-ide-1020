## 内容修改

### 🎯 核心概念
内容修改允许我们用JavaScript动态地改变网页上显示的文本和HTML结构，让页面内容可以根据用户操作或程序逻辑实时更新，创造出丰富的交互体验。

### 📚 Level 1: 基础认知（30秒理解）
想象网页上的一个标题，我们可以像给变量赋值一样，轻松地改变它显示的文字。`textContent`属性就是用来做这个的。

```javascript
// 模拟一个网页上的 <p> 元素
// 在真实浏览器中，你会用 document.getElementById('my-paragraph') 来获取元素
let mockParagraph = {
  textContent: "你好，世界！"
};

console.log("修改前的内容:", mockParagraph.textContent);

// 修改元素的文本内容
mockParagraph.textContent = "你好，JavaScript！";

console.log("修改后的内容:", mockParagraph.textContent);
```

### 📈 Level 2: 核心特性（深入理解）
修改内容主要有两种方式：`textContent` 和 `innerHTML`。它们有关键的区别。

#### 特性1: `textContent` - 只认纯文本
`textContent`会把所有内容都当作普通字符串处理，即使内容里包含HTML标签，它们也只会被当作文字显示出来。这非常安全！

```javascript
// 模拟一个网页上的 <div> 元素
let mockElement = {
  textContent: ""
};

console.log("--- 使用 textContent ---");

// 尝试用 textContent 添加一个包含 <strong> 标签的字符串
mockElement.textContent = "这是<strong>加粗</strong>的文字吗？";

// 输出结果会发现，<strong> 标签被原样当成了文本，并没有加粗效果
console.log("元素现在的 textContent:", mockElement.textContent);
console.log("结论：textContent 会忽略HTML标签，将其视为普通文本。");
```

#### 特性2: `innerHTML` - 能解析HTML
`innerHTML`则会解析字符串中的HTML标签，并将其渲染成真正的HTML结构。这很强大，但也要小心使用。

```javascript
// 模拟一个网页上的 <div> 元素
let mockElement = {
  innerHTML: ""
};

console.log("--- 使用 innerHTML ---");

// 使用 innerHTML 添加一个包含 <strong> 标签的字符串
mockElement.innerHTML = "这是<strong>加粗</strong>的文字！";

// 输出结果会发现，它能识别并“渲染”HTML标签
console.log("元素现在的 innerHTML:", mockElement.innerHTML);
console.log("结论：innerHTML 能够解析并应用HTML标签。");
```

### 🔍 Level 3: 对比学习（避免陷阱）
错误地使用 `innerHTML` 可能会带来安全风险，尤其是当内容来自用户输入时。

```javascript
// 假设这是用户输入的内容
const maliciousUserInput = "你好！<script>alert('你被攻击了！')</script>";

// 模拟两个元素，一个用错误方式，一个用正确方式
let vulnerableElement = { innerHTML: "" };
let safeElement = { textContent: "" };

console.log("=== 错误用法 ===");
// ❌ 直接将用户输入赋值给 innerHTML
vulnerableElement.innerHTML = maliciousUserInput;
console.log("危险内容:", vulnerableElement.innerHTML);
// 解释：这样做会导致字符串中的 <script> 标签被浏览器解析和执行，
// 这被称为跨站脚本攻击 (XSS)，非常危险。

console.log("\n=== 正确用法 ===");
// ✅ 使用 textContent 来处理用户输入的文本
safeElement.textContent = maliciousUserInput;
console.log("安全内容:", safeElement.textContent);
// 解释：textContent 会将所有内容（包括 <script> 标签）都当作纯文本处理，
// 标签不会被执行，从而避免了安全风险。
```

### 🚀 Level 4: 实战应用（真实场景）
让我们来创建一个简单的虚拟宠物互动游戏！根据不同的操作，宠物的状态会实时更新，并显示不同的心情和消息。

**场景：虚拟电子宠物“代码喵”**

```javascript
// 模拟网页上显示宠物状态的元素
const petStatusDisplay = {
  innerHTML: ""
};

// 定义我们的虚拟宠物
let codeCat = {
  name: "代码喵",
  mood: "开心", // 心情: 开心, 饥饿, 无聊
  energy: 100
};

// 更新宠物状态显示的功能
function updateDisplay() {
  let statusHTML = "";
  let moodEmoji = "";

  if (codeCat.mood === "开心") {
    moodEmoji = "😺";
    statusHTML = `<strong>${codeCat.name}</strong> ${moodEmoji} 正开心地摇着尾巴！`;
  } else if (codeCat.mood === "饥饿") {
    moodEmoji = "😿";
    statusHTML = `<strong>${codeCat.name}</strong> ${moodEmoji} 的肚子在咕咕叫，它饿了！`;
  } else if (codeCat.mood === "无聊") {
    moodEmoji = "😼";
    statusHTML = `<strong>${codeCat.name}</strong> ${moodEmoji} 正无聊地看着你，想玩耍。`;
  }
  
  statusHTML += `<br><em>能量值: ${codeCat.energy}/100</em>`;
  
  // 使用 innerHTML 来更新显示，因为我们想加入 <strong> 和 <br> 等HTML标签
  petStatusDisplay.innerHTML = statusHTML;
  console.log(petStatusDisplay.innerHTML.replace(/<br>/g, '\n')); // 用换行符模拟<br>效果
}

// 模拟与宠物的互动
function feedPet() {
  console.log("\n--- 你给代码喵喂了小鱼干 ---");
  codeCat.mood = "开心";
  codeCat.energy = Math.min(100, codeCat.energy + 20); // 能量最多100
  updateDisplay();
}

function playWithPet() {
  console.log("\n--- 你用逗猫棒和代码喵玩耍 ---");
  if (codeCat.energy > 15) {
    codeCat.mood = "开心";
    codeCat.energy -= 15;
  } else {
    codeCat.mood = "无聊";
    console.log("代码喵能量不足，不想动了...");
  }
  updateDisplay();
}

// 游戏开始
console.log("--- 游戏开始！遇见你的新宠物 ---");
updateDisplay();
feedPet();
playWithPet();
playWithPet();
```

### 💡 记忆要点
- **`textContent`**：最安全的选择，用于设置纯文本内容，它会自动转义HTML标签。
- **`innerHTML`**：功能强大，用于插入包含HTML结构的内容，但要警惕安全风险，绝不要直接使用未经验证的用户输入。
- **经验法则**：当不确定时，优先使用 `textContent`。只有当你明确需要渲染HTML标签时，才使用 `innerHTML`。

<!--
metadata:
  api: [innerHTML, textContent]
  concept: [DOM-manipulation, security, XSS]
  difficulty: basic
  dependencies: []
  related: []
-->