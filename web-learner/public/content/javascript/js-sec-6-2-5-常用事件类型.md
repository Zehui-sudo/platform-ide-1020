## 常用事件类型

### 🎯 核心概念
事件是网页或程序中发生的特定交互或动作，例如用户点击鼠标、按下键盘、或者窗口大小改变。通过监听和响应这些事件，JavaScript可以创建动态和互动的用户体验，让静态的页面“活”起来。

### 📚 Level 1: 基础认知（30秒理解）
想象一下网页上的一个按钮。当用户点击它时，我们希望执行某个操作，比如显示一条消息。这就是最常见的 `click` (点击) 事件。

在非浏览器环境中，我们可以用一个简单的对象和函数来模拟这个过程。

```javascript
// 模拟一个按钮对象
const myButton = {
  // 定义一个处理点击事件的函数
  // 这个函数被称为“事件处理程序”或“事件监听器”
  onclick: function() {
    console.log("按钮被点击了！你好，世界！");
  }
};

// 模拟用户点击按钮的行为
function simulateClick(button) {
  console.log("用户正在点击...");
  // 检查按钮是否有onclick处理程序，如果有就执行它
  if (button.onclick) {
    button.onclick();
  }
}

// 执行模拟点击
simulateClick(myButton);
```

### 📈 Level 2: 核心特性（深入理解）
除了点击，还有许多其他类型的事件，主要可以分为鼠标事件、键盘事件、表单事件等。

#### 特性1: 鼠标事件 (Mouse Events)
鼠标事件不仅限于点击，还包括鼠标指针的移动。

- `click`: 单击鼠标。
- `mouseover`: 鼠标指针进入元素范围。
- `mouseout`: 鼠标指针离开元素范围。

```javascript
// 模拟一个神奇的魔法石
const magicStone = {
  // 当鼠标进入时，魔法石发光
  onmouseover: () => {
    console.log("🌟 魔法石感应到你的靠近，开始发光！");
  },
  // 当鼠标离开时，光芒减弱
  onmouseout: () => {
    console.log("✨ 魔法石的光芒变暗了。");
  },
  // 当点击时，释放能量
  onclick: () => {
    console.log("💥 你点击了魔法石，一道能量迸发出来！");
  }
};

// 模拟一系列用户鼠标操作
function simulateMouseActions(element) {
  console.log("--- 开始模拟鼠标与魔法石的互动 ---");

  console.log("\n1. 鼠标指针移入...");
  if (element.onmouseover) element.onmouseover();

  console.log("\n2. 用户决定点击！");
  if (element.onclick) element.onclick();

  console.log("\n3. 鼠标指针移出...");
  if (element.onmouseout) element.onmouseout();

  console.log("\n--- 模拟结束 ---");
}

simulateMouseActions(magicStone);
```

#### 特性2: 键盘事件 (Keyboard Events)
键盘事件允许我们响应用户的按键操作。

- `keydown`: 当用户按下键盘上的任意键时触发。如果按住不放，会持续触发。
- `keyup`: 当用户释放键盘上的键时触发。
- `keypress`: (已不推荐使用) 当用户按下产生字符的键时触发。

通常，我们会检查事件对象中的 `key` 属性来判断用户按下了哪个键。

```javascript
// 模拟一个游戏角色的控制器
const gameController = {
  // 按下按键时的处理逻辑
  onkeydown: (event) => {
    console.log(`[KeyDown] 按下了键: "${event.key}"`);
    if (event.key === 'ArrowUp') {
      console.log("角色跳跃！슝~");
    } else if (event.key === ' ') {
      console.log("角色正在蓄力...");
    }
  },
  // 释放按键时的处理逻辑
  onkeyup: (event) => {
    console.log(`[KeyUp] 释放了键: "${event.key}"`);
    if (event.key === ' ') {
      console.log("大招释放！💥");
    }
  }
};

// 模拟用户玩游戏
function simulateKeyboardInput(controller) {
  console.log("--- 玩家开始操作 ---");
  
  // 模拟按下向上箭头
  controller.onkeydown({ key: 'ArrowUp' });
  // 模拟释放向上箭头
  controller.onkeyup({ key: 'ArrowUp' });

  console.log("---");

  // 模拟按住空格键蓄力，然后释放
  controller.onkeydown({ key: ' ' }); // 按下
  controller.onkeyup({ key: ' ' });   // 释放
  
  console.log("--- 操作结束 ---");
}

simulateKeyboardInput(gameController);
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个常见的混淆是在 `keydown` 和 `keyup` 之间选择。它们触发的时机不同，适用于不同的场景。

**场景**: 制作一个游戏，按住 'A' 键可以持续射击，而按 'R' 键是单次动作“更换弹夹”。

```javascript
console.log("=== 错误用法 ===");
// ❌ 错误：使用 keydown 来处理需要单次触发的“更换弹夹”动作
// 这会导致如果用户按住 'R' 键不放，会一直提示更换弹夹，不符合逻辑。
const playerActionsWrong = {
  isReloading: false,
  handleKeyDown: (key) => {
    if (key === 'A') {
      console.log("biu~ 持续射击！");
    } else if (key === 'R') {
      // 错误点：只要按住R键，就会不停地触发换弹夹
      console.log("❌ 开始更换弹夹！（如果按住会一直提示）");
    }
  }
};
console.log("模拟玩家按住 R 键 0.5 秒...");
playerActionsWrong.handleKeyDown('R');
playerActionsWrong.handleKeyDown('R'); // 模拟持续按住
playerActionsWrong.handleKeyDown('R'); // 模拟持续按住
console.log("解释：使用 keydown 会导致“更换弹夹”这个单次动作被重复触发，逻辑错误。");


console.log("\n=== 正确用法 ===");
// ✅ 正确：使用 keydown 处理持续性动作，使用 keyup 处理单次动作
const playerActionsRight = {
  isReloading: false,
  handleKeyDown: (key) => {
    if (key === 'A') {
      console.log("✅ biu~ 持续射击！");
    }
  },
  handleKeyUp: (key) => {
    if (key === 'R' && !playerActionsRight.isReloading) {
        playerActionsRight.isReloading = true;
        console.log("✅ 更换弹夹！咔嚓！(只触发一次)");
        // 模拟换弹夹需要时间
        setTimeout(() => {
          playerActionsRight.isReloading = false;
          console.log("✅ 弹夹更换完毕！");
        }, 50); // 使用很短的超时来模拟
    }
  }
};
console.log("模拟玩家按下 A 键，然后按下并释放 R 键...");
playerActionsRight.handleKeyDown('A'); // 持续射击
playerActionsRight.handleKeyDown('A');
playerActionsRight.handleKeyUp('R'); // 按下并释放R，触发换弹夹
console.log("解释：keydown 适合“按住时持续生效”的动作，而 keyup 适合“释放时触发一次”的动作。");
```

### 🚀 Level 4: 实战应用（真实场景）
**🎮 游戏场景**: 逃离神秘的像素洞穴！

让我们创建一个简单的文本冒险游戏。玩家 `P` 需要使用键盘（'w', 'a', 's', 'd'）在地图上移动，避开墙壁 `#`，找到宝藏 `$` 和出口 `E`。

```javascript
// 游戏状态和地图
const gameState = {
  player: { x: 1, y: 1 },
  treasureCollected: false,
  map: [
    ['#', '#', '#', '#', '#', '#', '#'],
    ['#', 'P', ' ', '#', ' ', ' ', '#'],
    ['#', ' ', ' ', ' ', ' ', '#', '#'],
    ['#', ' ', '#', '#', ' ', '$', '#'],
    ['#', ' ', ' ', ' ', ' ', ' ', '#'],
    ['#', '#', '#', '#', '#', 'E', '#'],
  ]
};

// 渲染地图到控制台
function renderMap() {
  console.log("\n--- 神秘洞穴 ---");
  // 清空旧的玩家位置标记
  for (let y = 0; y < gameState.map.length; y++) {
    for (let x = 0; x < gameState.map[y].length; x++) {
      if (gameState.map[y][x] === 'P') {
        gameState.map[y][x] = ' ';
      }
    }
  }
  // 放置新的玩家位置
  const { x, y } = gameState.player;
  gameState.map[y][x] = 'P';

  // 打印地图
  gameState.map.forEach(row => console.log(row.join(' ')));
  console.log("使用 w/a/s/d 移动. 你的目标是拿到'$'然后到达'E'!");
}

// 模拟键盘事件处理器
function handleKeyPress(key) {
  console.log(`\n你按下了 '${key}' 键...`);
  const { player } = gameState;
  let nextX = player.x;
  let nextY = player.y;

  if (key === 'w') nextY--; // 上
  if (key === 's') nextY++; // 下
  if (key === 'a') nextX--; // 左
  if (key === 'd') nextX++; // 右
  
  const destination = gameState.map[nextY][nextX];

  // 碰撞检测
  if (destination === '#') {
    console.log("哎哟！你撞到了墙壁。");
    return;
  }
  
  // 更新玩家位置
  player.x = nextX;
  player.y = nextY;
  
  // 检查目标格子
  if (destination === '$') {
    console.log("🎉 哇！你找到了闪闪发光的宝藏！");
    gameState.treasureCollected = true;
  } else if (destination === 'E') {
    if (gameState.treasureCollected) {
      console.log("🏆 恭喜！你带着宝藏成功逃离了洞穴！你赢了！");
    } else {
      console.log("🤔 你找到了出口，但是似乎忘记了什么重要的东西... (去找'$'!)");
    }
  } else {
    console.log("你移动到了一个新的位置。");
  }
  
  renderMap();
}

// --- 游戏开始 ---
console.log("欢迎来到《逃离神秘洞穴》！");
renderMap();

// 模拟玩家的一系列操作
handleKeyPress('s'); // 向下
handleKeyPress('d'); // 向右
handleKeyPress('d'); // 向右
handleKeyPress('d'); // 向右
handleKeyPress('s'); // 向下
handleKeyPress('s'); // 向下，找到宝藏
handleKeyPress('d'); // 向右
handleKeyPress('s'); // 向下
handleKeyPress('d'); // 向右，到达出口
```

### 💡 记忆要点
- **事件是交互的信号**：事件是用户（或浏览器）行为的通知，如 `click`, `mouseover`, `keydown`。
- **事件处理程序是响应**：你编写的函数（如 `onclick` 或 `onkeydown` 的处理函数）是用来对这些信号做出反应的代码。
- **选择正确的事件类型**：根据需要选择最合适的事件，`keydown` 用于持续性动作，`keyup` 或 `click` 用于单次触发的动作。

<!--
metadata:
  syntax: ["function", "const", "let"]
  pattern: ["callback", "event-handling"]
  api: ["console.log", "setTimeout"]
  concept: ["event-types", "event-handler"]
  difficulty: basic
  dependencies: ["无"]
  related: ["js-sec-6-2-6"]
-->