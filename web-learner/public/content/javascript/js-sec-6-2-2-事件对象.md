## 事件对象

### 🎯 核心概念
事件对象是一个在事件触发时自动创建并传递给事件处理函数的对象，它包含了关于该事件的所有相关信息（如鼠标位置、键盘按键、触发元素等），让我们能够对用户的交互做出精确响应。

### 📚 Level 1: 基础认知（30秒理解）
当你监听一个事件时，你的处理函数会自动接收到一个“神秘”的参数。这个参数就是事件对象（通常命名为 `event` 或 `e`），它像一份关于刚刚发生的事件的详细报告。

```javascript
// 为了让代码在任何地方都能独立运行，我们用JS创建HTML元素
document.body.innerHTML = '<button id="myButton">点我一下</button>';

const myButton = document.getElementById('myButton');

// 当按钮被点击时，handleClick函数会自动接收到 event 对象
function handleClick(event) {
  console.log("事件触发了！");
  console.log("这是自动传入的事件对象:", event);
  console.log("事件类型是:", event.type); // "click"
  console.log("事件发生在哪个元素上？", event.target); // <button id="myButton">
}

myButton.addEventListener('click', handleClick);

console.log("请点击上面的 '点我一下' 按钮，查看控制台输出。");
```

### 📈 Level 2: 核心特性（深入理解）
事件对象包含许多有用的属性，让我们深入了解几个最关键的。

#### 特性1: `event.target` vs `event.currentTarget`
- `event.target`: 引发事件的“始作俑者”，即用户实际交互的那个元素。
- `event.currentTarget`: 绑定事件监听器的元素，它可能不是用户直接交互的元素（在事件冒泡中尤其明显）。

```javascript
// 场景：一个div容器里有一个按钮，我们只在容器上监听点击事件
document.body.innerHTML = `
  <div id="container" style="padding: 20px; border: 2px solid blue;">
    我是容器(div)
    <button id="innerButton" style="margin-left: 10px;">我是按钮(button)</button>
  </div>
`;

const container = document.getElementById('container');

container.addEventListener('click', function(event) {
  console.log("事件监听器绑定在 div 上。");
  
  // event.target 是你实际点击的那个东西
  console.log("event.target:", event.target.tagName, `(ID: ${event.target.id})`); 
  
  // event.currentTarget 永远是绑定监听器的那个元素，即 div
  console.log("event.currentTarget:", event.currentTarget.tagName, `(ID: ${event.currentTarget.id})`);

  console.log("---");
  console.log("尝试分别点击按钮和它外面的蓝色边框区域，观察区别。");
});
```

#### 特性2: 鼠标事件坐标 (`clientX`/`clientY`)
对于鼠标事件（如 `click`, `mousemove`），事件对象会提供鼠标指针在浏览器窗口可视区域内的精确坐标。

```javascript
document.body.innerHTML = `
  <div id="tracker" style="width: 300px; height: 150px; border: 2px dashed red; background-color: #f0f0f0;">
    在红色虚线框内移动鼠标
  </div>
`;

const tracker = document.getElementById('tracker');

tracker.addEventListener('mousemove', function(event) {
  // event.clientX 是鼠标相对于浏览器窗口左边的距离
  const x = event.clientX;
  // event.clientY 是鼠标相对于浏览器窗口顶边的距离
  const y = event.clientY;

  // 为了避免刷屏，我们不会一直打印，但可以更新元素内容
  tracker.textContent = `鼠标坐标: X=${x}, Y=${y}`;
  
  // 在控制台输出一次，方便查看
  console.clear(); // 清空控制台，避免信息泛滥
  console.log(`鼠标在窗口中的位置: X=${x}, Y=${y}`);
});
```

#### 特性3: 键盘事件信息 (`key` 和 `code`)
对于键盘事件（如 `keydown`），事件对象提供了关于按下的键的详细信息。
- `event.key`: 按键的“字符”值（例如 'a', 'A', 'Enter', ' '）。
- `event.code`: 按键的“物理”位置码（例如 'KeyA', 'Enter', 'Space'），不受大小写或输入法影响。

```javascript
document.body.innerHTML = '<input type="text" id="keyInput" placeholder="在此输入文字..." />';

const keyInput = document.getElementById('keyInput');

keyInput.addEventListener('keydown', function(event) {
  console.log("--- 键盘按键事件 ---");
  console.log(`你按下的键 (event.key): "${event.key}"`);
  console.log(`对应的物理按键 (event.code): "${event.code}"`);
  
  if (event.key === 'Enter') {
    console.warn("你按下了回车键！准备提交表单？");
  }
});

console.log("请点击输入框并尝试按不同的键（比如 a, Shift+a, Enter, 空格），观察控制台输出。");
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个常见的混淆点是在处理嵌套元素的事件时，错误地使用 `event.currentTarget` 而不是 `event.target`。

```javascript
// 场景：一个购物清单，我们想知道用户点击了哪个具体的水果
document.body.innerHTML = `
  <h3>点击下面的水果：</h3>
  <ul id="fruitList" style="cursor: pointer;">
    <li>🍎 苹果</li>
    <li>🍌 香蕉</li>
    <li>🍓 草莓</li>
  </ul>
`;

const fruitList = document.getElementById('fruitList');

fruitList.addEventListener('click', function(event) {
  console.log("=== 错误用法 ===");
  // ❌ 错误：试图用 currentTarget 获取被点击项的文本
  // event.currentTarget 永远是 <ul> 本身，所以 textContent 会包含所有 <li> 的内容
  const allFruitsText = event.currentTarget.textContent;
  console.log("currentTarget 的文本内容:", allFruitsText.replace(/\s+/g, ' ').trim());
  console.log("为什么错了？因为它获取了整个列表的文本，而不是你点击的那一项。");

  console.log("\n=== 正确用法 ===");
  // ✅ 正确：使用 target 来精确定位被点击的 <li> 元素
  // event.target 就是你实际点击的那个 <li>
  if (event.target.tagName === 'LI') {
    const clickedFruitText = event.target.textContent;
    console.log("你点击的水果是:", clickedFruitText);
    console.log("为什么对了？因为它准确地捕获到了事件的源头——被点击的 <li>。");
  }
});
```

### 🚀 Level 4: 实战应用（真实场景）
🎨 **创意互动：迷你像素画板**

让我们创建一个简单的像素画板。我们不需要为每个像素格子都添加一个事件监听器，而是利用事件对象的 `target` 属性，只在画板容器上设置一个监听器（这叫作“事件委托”），就能知道用户点击了哪个“像素”。

```javascript
// --- 准备工作：创建HTML和CSS ---
const boardSize = 10; // 10x10 的画板
let currentBrushColor = 'crimson'; // 默认画笔颜色

// 创建一个调色板
const colors = ['crimson', 'dodgerblue', 'mediumseagreen', 'gold', 'slateblue', 'black', 'white'];
let paletteHTML = '<div><strong>选择颜色:</strong> ';
colors.forEach(color => {
  paletteHTML += `<span class="color-box" style="background-color:${color};" data-color="${color}"></span>`;
});
paletteHTML += '</div>';

// 创建像素画板的格子
let boardHTML = '<div id="pixel-board">';
for (let i = 0; i < boardSize * boardSize; i++) {
  boardHTML += '<div class="pixel"></div>';
}
boardHTML += '</div>';

// 将画板和调色板添加到页面
document.body.innerHTML = `
  <style>
    #pixel-board { display: grid; grid-template-columns: repeat(${boardSize}, 30px); border: 2px solid #333; width: ${boardSize * 30}px; }
    .pixel { width: 30px; height: 30px; background-color: #eee; border: 1px solid #ddd; }
    .pixel:hover { border-color: #999; }
    .color-box { display: inline-block; width: 25px; height: 25px; border: 2px solid #fff; margin: 0 5px; cursor: pointer; vertical-align: middle; }
    .color-box.selected { border-color: black; transform: scale(1.2); }
  </style>
  <h2>🎨 迷你像素画板 🎨</h2>
  <div id="palette">${paletteHTML}</div>
  <p>点击下方格子进行绘画！</p>
  ${boardHTML}
`;

// --- 核心交互逻辑 ---
const pixelBoard = document.getElementById('pixel-board');
const palette = document.getElementById('palette');

// 1. 监听整个画板的点击事件
pixelBoard.addEventListener('click', function(event) {
  // event.target 就是我们点击的那个 .pixel 元素！
  const clickedPixel = event.target;

  // 确保我们点击的是像素格，而不是格子之间的缝隙
  if (clickedPixel.classList.contains('pixel')) {
    clickedPixel.style.backgroundColor = currentBrushColor;
    console.log(`🎨 你用 [${currentBrushColor}] 颜色在某个像素上画了一笔！艺术诞生了！`);
  }
});

// 2. 监听调色板的点击事件，用于更换画笔颜色
palette.addEventListener('click', function(event) {
  const clickedColorBox = event.target;
  
  if (clickedColorBox.classList.contains('color-box')) {
    // 获取颜色
    currentBrushColor = clickedColorBox.dataset.color;
    
    // 更新视觉提示
    document.querySelectorAll('.color-box').forEach(box => box.classList.remove('selected'));
    clickedColorBox.classList.add('selected');
    
    console.log(`🖌️ 画笔颜色已切换为 [${currentBrushColor}]。准备挥洒创意吧！`);
  }
});

// 初始化时给第一个颜色添加选中状态
document.querySelector('.color-box').classList.add('selected');
```

### 💡 记忆要点
- **自动参数**: 事件处理函数会自动接收一个事件对象作为第一个参数，无需手动创建。
- **`target` vs `currentTarget`**: `event.target`是事件的真正来源（用户交互的元素），而`event.currentTarget`是绑定监听器的元素。
- **信息宝库**: 不同类型的事件（鼠标、键盘等）会向事件对象中添加不同的专属属性（如 `clientX`, `key`），提供了丰富的上下文信息。

<!--
metadata:
  syntax: [function, const, let]
  pattern: [event-handling, event-delegation]
  api: [addEventListener, console.log, event.target, event.currentTarget, event.clientX, event.clientY, event.key, event.code, document.getElementById, document.querySelector]
  concept: [event-object, event-bubbling, DOM]
  difficulty: intermediate
  dependencies: [无]
  related: [js-sec-6-2-1]
-->