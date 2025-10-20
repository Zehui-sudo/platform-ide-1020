## 事件监听

### 🎯 核心概念
事件监听允许你的JavaScript代码对用户的操作（如点击、滚动、按键）或浏览器的行为（如页面加载完成）做出反应。它是构建交互式网页的基石，就像给网页元素安装了“感应器”。

### 📚 Level 1: 基础认知（30秒理解）
最核心的方法是 `addEventListener()`。你告诉一个元素需要“监听”哪种类型的事件，以及事件发生时要执行什么函数（称为“回调函数”）。

**注意：** 为了让代码在非浏览器环境中也能运行和展示，我们将用注释模拟HTML结构。在实际浏览器中，这些代码会直接操作页面。

```javascript
// 模拟一个HTML按钮
document.body.innerHTML = '<button id="myBtn">点我</button>';
const myButton = document.getElementById('myBtn');

// 1. 获取元素
// const myButton = document.getElementById('myBtn');

// 2. 添加事件监听器
// 参数1: 事件类型 ('click')
// 参数2: 回调函数 (事件发生时要做的事)
myButton.addEventListener('click', function() {
  console.log("按钮被点击了！这是一个来自 addEventListener 的响应。");
});

// 3. 在代码中模拟一次点击来触发事件
console.log("正在等待用户点击按钮...");
myButton.click(); // 这会触发上面定义的监听器

// 清理模拟的DOM
document.body.innerHTML = '';
```

### 📈 Level 2: 核心特性（深入理解）
`addEventListener` 非常灵活，可以为一个事件添加多个监听器，也可以在不需要时移除它们。

#### 特性1: 同一事件，多个监听器
你可以为一个元素的同一个事件（例如`click`）添加多个监听函数，它们会按照添加的顺序依次执行。

```javascript
// 模拟HTML按钮
document.body.innerHTML = '<button id="taskBtn">完成任务</button>';
const taskButton = document.getElementById('taskBtn');

// 监听器 1: 记录日志
taskButton.addEventListener('click', () => {
  console.log("日志：任务按钮被点击。");
});

// 监听器 2: 更新UI
taskButton.addEventListener('click', () => {
  console.log("UI更新：按钮变为灰色，显示“已完成”。");
  // taskButton.disabled = true; // 在真实浏览器中会禁用按钮
});

// 监听器 3: 发送分析数据
taskButton.addEventListener('click', () => {
  console.log("分析：发送'task_completed'事件到服务器。");
});

// 模拟点击，所有监听器都会被触发
taskButton.click();

document.body.innerHTML = '';
```

#### 特性2: 使用 `removeEventListener` 移除监听
为了防止内存泄漏或不需要的行为了，可以在适当的时候移除事件监听器。**注意：** 必须传递与添加时完全相同的函数引用。

```javascript
// 模拟HTML
document.body.innerHTML = '<div>这是一个可以关闭的弹窗</div>';
const popup = document.querySelector('div'); // 使用querySelector以匹配模拟的DOM

// 定义一个具名函数作为回调，这样才能移除它
function showWarning() {
  console.log("警告：弹窗即将自动关闭！");
}

// 添加监听：鼠标移入时显示警告
popup.addEventListener('mouseenter', showWarning);
console.log("监听器已添加。请将鼠标移入弹窗。");

// 模拟鼠标移入
popup.dispatchEvent(new Event('mouseenter'));

// 移除监听器
popup.removeEventListener('mouseenter', showWarning);
console.log("监听器已移除。");

// 再次模拟鼠标移入，这次什么都不会发生
console.log("再次将鼠标移入弹窗...");
popup.dispatchEvent(new Event('mouseenter'));
console.log("...没有任何日志输出，因为监听器已被成功移除。");

document.body.innerHTML = '';
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个经典的对比是 `addEventListener` 和旧的 `on-event` 属性（如 `onclick`）。

```javascript
// 模拟HTML按钮
document.body.innerHTML = '<button id="compareBtn">对比按钮</button>';
const compareButton = document.getElementById('compareBtn');

console.log("=== 错误/受限用法 (onclick) ===");
// ❌ 使用 onclick 属性
compareButton.onclick = function() {
  console.log("第一个 onclick 处理器。");
};

// 再次赋值会覆盖掉前一个！
compareButton.onclick = function() {
  console.log("第二个 onclick 处理器，它覆盖了第一个！");
};
// 模拟点击，只有最后一个赋值的函数会执行
compareButton.click();
console.log("解释：onclick 属性只能容纳一个函数，新的赋值会覆盖旧的。");


console.log("\n=== 正确/推荐用法 (addEventListener) ===");
// ✅ 使用 addEventListener
compareButton.addEventListener('click', function() {
  console.log("第一个 addEventListener 监听器。");
});

compareButton.addEventListener('click', function() {
  console.log("第二个 addEventListener 监听器，它不会覆盖第一个。");
});
// 再次模拟点击，所有通过 addEventListener 添加的函数都会执行
compareButton.click();
console.log("解释：addEventListener 允许为同一事件附加任意多个监听器。");

document.body.innerHTML = '';
```

### 🚀 Level 4: 实战应用（真实场景）
**🎨 创意互动：迷你像素画板**

让我们创建一个简单的像素画板。当鼠标在画板上移动并按下时，对应的“像素”会改变颜色。

```javascript
// --- 场景设置 ---
document.body.innerHTML = '
  <h3>迷你像素画板</h3>
  <div id="pixel-board" style="display: grid; grid-template-columns: repeat(10, 20px); width: 200px; border: 1px solid #ccc;">
    <!-- JS将在这里生成像素点 -->
  </div>
  <small>在画板上按住鼠标移动来绘画</small>
';
const board = document.getElementById('pixel-board');
let isDrawing = false;

// 生成 10x10 的像素格子
for (let i = 0; i < 100; i++) {
  const pixel = document.createElement('div');
  pixel.style.width = '20px';
  pixel.style.height = '20px';
  pixel.style.backgroundColor = '#eee';
  pixel.style.border = '1px solid #fff';
  board.appendChild(pixel);
  
  // 监听：当鼠标进入一个像素格子时
  pixel.addEventListener('mouseover', function(event) {
    // 如果鼠标是按下的状态，就给这个像素上色
    if (isDrawing) {
      event.target.style.backgroundColor = '#3498db';
    }
  });
}

// 监听：在整个画板上按下鼠标
board.addEventListener('mousedown', function(event) {
  isDrawing = true;
  console.log("开始绘画！");
  // 让被点击的第一个像素也上色
  if (event.target !== board) {
      event.target.style.backgroundColor = '#3498db';
  }
});

// 监听：在整个窗口松开鼠标
window.addEventListener('mouseup', function() {
  if (isDrawing) {
    isDrawing = false;
    console.log("停止绘画！");
  }
});

// --- 模拟一次绘画动作 ---
console.log("模拟用户在画板上按下鼠标，并划过几个像素...");
const firstPixel = board.children[11];
board.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
firstPixel.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
board.children[12].dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
window.dispatchEvent(new MouseEvent('mouseup'));

// 清理
// setTimeout(() => document.body.innerHTML = '', 2000);
```

### 💡 记忆要点
- **核心API**: `element.addEventListener('事件名', 回调函数)` 是添加监听的标准方式。
- **解绑要用 `removeEventListener`**: 为了移除监听，你需要传入与添加时完全相同的函数引用，所以通常需要使用具名函数。
- **`addEventListener` 优于 `onclick`**: 它功能更强，允许添加多个监听器，不会相互覆盖，是现代Web开发的首选。

<!--
metadata:
  syntax: [function]
  pattern: [event-handler, callback]
  api: [addEventListener, removeEventListener, getElementById, dispatchEvent]
  concept: [event-driven-programming, callback, dom-events]
  difficulty: basic
  dependencies: [js-sec-6-1-1]
  related: [js-sec-6-2-2, js-sec-6-2-3]
-->

```