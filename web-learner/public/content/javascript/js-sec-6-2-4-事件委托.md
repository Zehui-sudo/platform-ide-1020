## 事件委托

### 🎯 核心概念
事件委托是一种利用事件冒泡原理，将事件监听器添加到父元素上，用以管理所有子元素上发生的事件的技巧。它解决了需要为大量子元素（尤其是动态添加的子元素）绑定事件时，代码冗余和性能低下的问题。

### 📚 Level 1: 基础认知（30秒理解）
想象一个装满按钮的容器。与其给每个按钮都派一个保安（事件监听器），不如只在容器的出口派一个保安。当有人（事件）从任何一个按钮出来时，保安在出口处检查他的身份（`event.target`）就知道是哪个按钮被按下了。

```javascript
// 模拟一个DOM环境，以便在任何JS环境中运行
function createMockElement(tagName, id = '', children = []) {
  const element = {
    tagName: tagName.toUpperCase(),
    id: id,
    children: children,
    addEventListener: function(type, listener) {
      this._listener = listener; // 存储监听器
      console.log(`事件监听器已附加到 <${this.tagName.toLowerCase()} id="${this.id}">`);
    },
    // 模拟点击事件，事件会从被点击的子元素“冒泡”到父元素
    simulateClick: function(targetChild) {
      const event = {
        target: targetChild, // 真正被点击的元素
        currentTarget: this, // 监听器所在的元素
      };
      console.log(`\n模拟点击: <${targetChild.tagName.toLowerCase()}> 被点击了!`);
      if (this._listener) {
        this._listener(event);
      }
    }
  };
  children.forEach(child => child.parentElement = element);
  return element;
}

// 创建我们的“容器”和“按钮”
const button1 = { tagName: 'BUTTON', id: 'btn-1', textContent: '按钮1' };
const button2 = { tagName: 'BUTTON', id: 'btn-2', textContent: '按钮2' };
const container = createMockElement('div', 'container', [button1, button2]);

// 事件委托：只在父容器上设置一个监听器
container.addEventListener('click', (event) => {
  // event.target 是我们实际点击的那个按钮
  const clickedElement = event.target;
  console.log(`事件在容器捕获! 真正被点击的是: ${clickedElement.textContent} (ID: ${clickedElement.id})`);
});

// 模拟点击第一个按钮
container.simulateClick(button1);
// 模拟点击第二个按钮
container.simulateClick(button2);
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 动态添加的元素也能响应事件
事件委托最强大的功能之一，就是能够自动处理后来动态添加到父元素中的子元素，无需为新元素重新绑定事件。

```javascript
// 模拟一个更真实的DOM环境
function createMockDOM() {
  const dom = {
    elements: {},
    create: function(tagName, id, textContent) {
      this.elements[id] = {
        tagName: tagName.toUpperCase(),
        id,
        textContent,
        parentElement: null,
        matches(selector) { return selector === `#${this.id}`; }
      };
      return this.elements[id];
    },
    get: function(id) { return this.elements[id]; },
    appendTo: function(childId, parentId) {
      this.elements[childId].parentElement = this.elements[parentId];
      this.elements[parentId].children = this.elements[parentId].children || [];
      this.elements[parentId].children.push(this.elements[childId]);
    }
  };
  return dom;
}

const mockDOM = createMockDOM();
const list = mockDOM.create('ul', 'task-list', '');
const task1 = mockDOM.create('li', 'task-1', '学习 JavaScript');
const task2 = mockDOM.create('li', 'task-2', '阅读文档');
mockDOM.appendTo('task-1', 'task-list');
mockDOM.appendTo('task-2', 'task-list');

// 在父元素 <ul> 上设置事件监听器
list.addEventListener = function(type, callback) {
  this._listener = callback;
  console.log('任务列表的事件监听器已设置!');
};

list.simulateClick = function(targetId) {
  const event = { target: mockDOM.get(targetId) };
  this._listener(event);
};

list.addEventListener('click', (event) => {
  // 使用 .matches() 检查被点击的元素是否是我们想要的 <li>
  if (event.target.tagName === 'LI') {
    console.log(`任务 "${event.target.textContent}" 已完成!`);
  }
});

console.log('--- 初始任务列表 ---');
list.simulateClick('task-1');

console.log('\n--- 动态添加一个新任务 ---');
const task3 = mockDOM.create('li', 'task-3', '编写代码');
mockDOM.appendTo('task-3', 'task-list');
console.log('新任务 "编写代码" 已添加，无需重新绑定事件。');

console.log('\n--- 点击新添加的任务 ---');
// 新添加的元素也能被正确处理！
list.simulateClick('task-3');
```

#### 特性2: 显著的性能优势
当元素数量非常多时，只创建一个事件监听器比创建成百上千个监听器，在内存和CPU占用上都有巨大优势。

```javascript
// 模拟一个有1000个子项的列表
const createHeavyList = (itemCount) => {
  const parent = { tagName: 'UL', children: [] };
  for (let i = 1; i <= itemCount; i++) {
    parent.children.push({ tagName: 'LI', id: `item-${i}` });
  }
  return parent;
};

const list = createHeavyList(1000);

// 方法1: 事件委托 (高性能)
function setupWithDelegation(parent) {
  let listenerCount = 0;
  parent.addEventListener = () => {
    listenerCount++;
  };
  parent.addEventListener('click', () => {}); // 模拟添加事件
  console.log(`[事件委托] 列表有 ${parent.children.length} 个子项，但只创建了 ${listenerCount} 个事件监听器。`);
}

// 方法2: 循环绑定 (低性能)
function setupWithoutDelegation(parent) {
  let listenerCount = 0;
  parent.children.forEach(child => {
    child.addEventListener = () => {
      listenerCount++;
    };
    child.addEventListener('click', () => {}); // 模拟添加事件
  });
  console.log(`[循环绑定] 列表有 ${parent.children.length} 个子项，创建了 ${listenerCount} 个事件监听器。`);
}

console.log("比较两种方法的性能开销：");
setupWithDelegation(list);
setupWithoutDelegation(list);
console.log("\n结论: 事件委托在处理大量子元素时，内存和性能优势非常明显。");
```

### 🔍 Level 3: 对比学习（避免陷阱）
让我们通过一个场景，看看不使用事件委托会遇到什么问题。

```javascript
// 模拟一个简单的DOM操作环境
const createMockList = () => {
  let items = {
    'item-1': { id: 'item-1', textContent: '苹果' },
    'item-2': { id: 'item-2', textContent: '香蕉' }
  };
  let listeners = {};

  return {
    addItem: (id, text) => {
      console.log(`...添加新项目: ${text}`);
      items[id] = { id, textContent: text };
    },
    bindListener: (id, callback) => {
      listeners[id] = callback;
    },
    clickItem: (id) => {
      console.log(`> 模拟点击 ${items[id].textContent}`);
      if (listeners[id]) {
        listeners[id]({ target: items[id] });
      } else {
        console.log(`!! <${items[id].textContent}> 上没有找到监听器!`);
      }
    },
    getItems: () => Object.values(items)
  };
};

// =========================================================
console.log("=== 错误用法: 为每个已知元素单独绑定 ===");
// ❌ 这种方法无法处理动态添加的元素
const wrongList = createMockList();
// 初始时为每个存在的元素绑定事件
wrongList.getItems().forEach(item => {
  wrongList.bindListener(item.id, (e) => {
    console.log(`好吃! 你点击了 ${e.target.textContent}。`);
  });
});

wrongList.clickItem('item-1'); // 正常工作
wrongList.addItem('item-3', '橙子'); // 动态添加一个新水果
wrongList.clickItem('item-3'); // 失败！因为“橙子”被添加时，我们没有为它绑定事件。
console.log("错误原因：事件监听器是在新元素被添加 *之前* 绑定的，新元素错过了绑定过程。");

// =========================================================
console.log("\n=== 正确用法: 使用事件委托 ===");
// ✅ 在父元素上设置一次监听器，一劳永逸
const correctList = {
  items: {
    'item-1': { id: 'item-1', textContent: '苹果' },
    'item-2': { id: 'item-2', textContent: '香蕉' }
  },
  // 模拟父元素的事件监听
  listener: (event) => {
    // 检查被点击的是否是目标子元素
    if (event.target.id.startsWith('item-')) {
      console.log(`太棒了! 你点击了 ${event.target.textContent}。`);
    }
  },
  clickItem: function(id) {
    console.log(`> 模拟点击 ${this.items[id].textContent}`);
    this.listener({ target: this.items[id] });
  },
  addItem: function(id, text) {
    console.log(`...添加新项目: ${text}`);
    this.items[id] = { id, textContent: text };
  }
};

correctList.clickItem('item-2'); // 正常工作
correctList.addItem('item-3', '橙子'); // 动态添加一个新水果
correctList.clickItem('item-3'); // 依然正常工作！
console.log("正确原因：事件监听器在父元素上，无论子元素如何增删，只要点击事件冒泡到父元素，就能被捕获和处理。");
```

### 🚀 Level 4: 实战应用（真实场景）

**🎮 游戏场景：像素画板 (Pixel Art Pad)**

在这个场景中，我们将创建一个简单的像素画板。画板由很多个小方格（像素）组成。如果给每个像素都添加一个点击事件，当画板尺寸很大时（比如64x64），性能会很差。使用事件委托，我们只需要在整个画板容器上添加一个监听器，就能轻松控制所有像素的颜色。

```javascript
// 模拟一个像素画板游戏
class PixelArtPad {
  constructor(width, height) {
    this.width = width;
    this.height = height;
    this.grid = this.createGrid(width, height);
    this.currentColor = '🔴'; // 默认颜色是红色
    this.eventListener = null; // 父容器的监听器

    console.log(`🎨 一个 ${width}x${height} 的像素画板已创建!`);
  }

  // 创建像素格子数据
  createGrid(width, height) {
    const grid = {};
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const id = `pixel-${x}-${y}`;
        grid[id] = { id, x, y, color: '⚪️', type: 'pixel' };
      }
    }
    return grid;
  }

  // 在画板容器上设置事件监听器
  attachListener() {
    // 事件委托的核心：监听器在父容器上
    this.eventListener = (event) => {
      const target = event.target;
      // 确保我们点击的是一个像素，而不是容器背景
      if (target && target.type === 'pixel') {
        console.log(`🖌️ 你在坐标 (${target.x}, ${target.y}) 使用 ${this.currentColor} 进行了绘制!`);
        target.color = this.currentColor;
        this.render();
      } else if (target && target.type === 'color-palette') {
        this.currentColor = target.color;
        console.log(`🎨 颜色已切换为: ${this.currentColor}`);
      }
    };
    console.log('事件监听器已附加到整个画板，而不是每个像素。');
  }

  // 模拟点击事件
  simulateClick(targetId) {
    // 模拟点击画板上的一个像素或调色板
    const target = this.grid[targetId] || this.palette[targetId];
    if (!target) {
      console.log('无效点击目标！');
      return;
    }
    const event = { target };
    this.eventListener(event);
  }

  // 模拟调色板
  createPalette() {
    this.palette = {
      'color-red': { id: 'color-red', color: '🔴', type: 'color-palette' },
      'color-blue': { id: 'color-blue', color: '🔵', type: 'color-palette' },
      'color-green': { id: 'color-green', color: '🟢', type: 'color-palette' },
    };
  }

  // 在控制台渲染画板
  render() {
    console.log('--- 当前画板状态 ---');
    let output = '';
    for (let y = 0; y < this.height; y++) {
      for (let x = 0; x < this.width; x++) {
        output += this.grid[`pixel-${x}-${y}`].color + ' ';
      }
      output += '\n';
    }
    console.log(output);
  }
}

// --- 开始游戏 ---
const myPad = new PixelArtPad(5, 5);
myPad.createPalette();
myPad.attachListener(); // 设置事件委托
myPad.render();

// 模拟用户操作
myPad.simulateClick('pixel-2-2'); // 在中间点一下
myPad.simulateClick('color-blue'); // 切换到蓝色
myPad.simulateClick('pixel-0-0'); // 在左上角点一下
myPad.simulateClick('pixel-4-4'); // 在右下角点一下
```

### 💡 记忆要点
- **要点1**：事件委托是将监听器绑定在父元素上，而不是子元素上。
- **要点2**：利用事件冒泡机制，通过 `event.target` 来识别并操作真正被触发的子元素。
- **要点3**：核心优势是提升性能和简化对动态添加元素（如AJAX加载的内容）的事件管理。

<!--
metadata:
  syntax: ["function", "const", "let", "class"]
  pattern: ["event-delegation"]
  api: ["addEventListener", "console.log", "Element.matches"]
  concept: ["event-bubbling", "event-handling", "event-target"]
  difficulty: intermediate
  dependencies: ["无"]
  related: []
-->