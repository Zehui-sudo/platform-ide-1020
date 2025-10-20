## SessionStorage

### 🎯 核心概念
`SessionStorage` 解决了在**单次浏览器会话**期间临时存储少量数据的需求，例如保存用户在当前页面标签页中的临时状态，当标签页关闭后数据即被清除。

### 📚 Level 1: 基础认知（30秒理解）
`SessionStorage` 就像一个页面的临时便签，你可以写入信息，然后在页面刷新后读出来，但关闭这个页面标签后，便签上的内容就消失了。

```javascript
// 清理一下，确保从一个干净的状态开始
sessionStorage.clear();

console.log("--- 初始状态 ---");
// 尝试读取一个不存在的键，会返回 null
const initialPlayer = sessionStorage.getItem('currentPlayer');
console.log("当前玩家是:", initialPlayer); // 输出: null

console.log("\n--- 存储数据 ---");
// 使用 setItem(key, value) 存储数据
sessionStorage.setItem('currentPlayer', 'Mage_Alex');
console.log("已将玩家 'Mage_Alex' 存入 SessionStorage。");

console.log("\n--- 读取数据 ---");
// 使用 getItem(key) 读取数据
const savedPlayer = sessionStorage.getItem('currentPlayer');
console.log("从 SessionStorage 中读取到的玩家是:", savedPlayer); // 输出: Mage_Alex

// 提示：你可以刷新一下页面，然后再次运行这段代码，会发现'Mage_Alex'还在。
// 但如果你关闭这个浏览器标签页再重新打开，它就消失了。
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 会话级别的生命周期
`SessionStorage` 中存储的数据只在当前浏览器标签页的会话期间有效。数据在页面刷新或跳转时依然存在，但当标签页或浏览器关闭后，数据会被永久删除。

```javascript
// 1. 设置一个值
sessionStorage.setItem('session-status', 'Active');
console.log(`当前会话状态: ${sessionStorage.getItem('session-status')}`);
console.log("✅ 数据已存储。请刷新此页面，再次查看控制台。");
console.log("你会发现 'Active' 这条信息依然存在。");

// 2. 移除一个值
sessionStorage.removeItem('session-status');
console.log(`移除后，再次读取会话状态: ${sessionStorage.getItem('session-status')}`); // 输出: null

// 3. 清空所有
sessionStorage.setItem('temp_data_1', '123');
sessionStorage.setItem('temp_data_2', 'abc');
console.log(`清空前，项目数量: ${sessionStorage.length}`); // 输出: 2
sessionStorage.clear();
console.log(`清空后，项目数量: ${sessionStorage.length}`); // 输出: 0
console.log("❌ 现在关闭这个浏览器标签页再重新打开，所有 sessionStorage 数据都会消失。");
```

#### 特性2: 只能存储字符串
`SessionStorage` 的 `key` 和 `value` 都必须是字符串。如果你尝试存储其他类型（如数字、布尔值、对象），它们会被自动转换成字符串。

```javascript
console.log("--- 存储不同类型的数据 ---");

// 存储数字 100
sessionStorage.setItem('playerScore', 100);
const score = sessionStorage.getItem('playerScore');
console.log(`分数: ${score}, 类型: ${typeof score}`); // 输出: 分数: 100, 类型: string

// 存储布尔值 true
sessionStorage.setItem('isGameOver', true);
const gameOver = sessionStorage.getItem('isGameOver');
console.log(`游戏结束: ${gameOver}, 类型: ${typeof gameOver}`); // 输出: 游戏结束: true, 类型: string

// 存储一个对象
const player = { name: 'Knight_Leo', level: 5 };
sessionStorage.setItem('playerObject', player);
const playerObjStr = sessionStorage.getItem('playerObject');
console.log(`玩家对象: ${playerObjStr}, 类型: ${typeof playerObjStr}`); // 输出: 玩家对象: [object Object], 类型: string
console.warn("⚠️ 注意：直接存储对象会得到 '[object Object]' 字符串，这通常不是我们想要的！");
```

### 🔍 Level 3: 对比学习（避免陷阱）
直接存储和读取对象是 `SessionStorage` 最常见的错误。你必须先将对象序列化为 JSON 字符串再存储，读取时再反序列化回来。

```javascript
// 定义一个玩家状态对象
const playerState = {
  name: 'Wizard_Gandalf',
  hp: 85,
  inventory: ['staff', 'spellbook']
};

console.log("=== 错误用法 ===");
// ❌ 直接存储对象
sessionStorage.setItem('playerStateWrong', playerState);
const wrongData = sessionStorage.getItem('playerStateWrong');
console.log("错误读取的数据:", wrongData); // 输出: "[object Object]"
console.log("尝试访问属性:", wrongData.name); // 输出: undefined
console.log("原因：对象被自动转换成了无用的 '[object Object]' 字符串，丢失了所有内部信息。");

console.log("\n=== 正确用法 ===");
// ✅ 使用 JSON.stringify() 转换对象为字符串再存储
sessionStorage.setItem('playerStateCorrect', JSON.stringify(playerState));

// 从 sessionStorage 读取字符串
const correctDataString = sessionStorage.getItem('playerStateCorrect');
// 使用 JSON.parse() 将字符串转换回对象
const correctData = JSON.parse(correctDataString);

console.log("正确读取的数据:", correctData);
console.log("成功访问属性:", correctData.name); // 输出: "Wizard_Gandalf"
console.log("成功访问数组属性:", correctData.inventory); // 输出: ['staff', 'spellbook']
console.log("原因：通过 JSON 格式，我们完整地保留了对象的结构和数据。");
```

### 🚀 Level 4: 实战应用（真实场景）
**场景：🎮 迷你文字冒险游戏 - 洞穴探险**

在这个场景中，我们使用 `SessionStorage` 来保存玩家在一次探险中的进度。如果玩家不小心刷新了页面，他的位置、生命值和收集到的宝物都不会丢失，可以继续游戏！

```javascript
// 游戏逻辑封装在一个函数中，方便管理
function caveAdventure() {
  // 1. 初始化或从 SessionStorage 加载游戏状态
  function loadGame() {
    const savedState = sessionStorage.getItem('caveAdventureState');
    if (savedState) {
      console.log("✨ 欢迎回来，勇敢的探险家！正在从上次的存档点继续...");
      return JSON.parse(savedState);
    } else {
      console.log("🌟 一个新的探险开始了！你站在一个黑暗的洞穴入口。");
      return {
        position: 'Entrance',
        hp: 100,
        inventory: [],
        log: ['你进入了洞穴。']
      };
    }
  }

  let gameState = loadGame();

  // 2. 保存游戏状态到 SessionStorage
  function saveGame() {
    sessionStorage.setItem('caveAdventureState', JSON.stringify(gameState));
    console.log("💾 [游戏状态已自动保存至 SessionStorage]");
  }

  // 3. 游戏动作函数
  function move(direction) {
    let message = '';
    if (gameState.position === 'Entrance' && direction === 'forward') {
      gameState.position = 'Hall';
      message = '你向前走，进入了一个宽敞的大厅。';
    } else if (gameState.position === 'Hall' && direction === 'left') {
      gameState.position = 'Treasure Room';
      message = '你向左拐，发现了一个装满金币的宝箱！';
      gameState.inventory.push('Gold Coins');
    } else if (gameState.position === 'Hall' && direction === 'right') {
      gameState.position = 'Trap Room';
      message = '你向右走，不小心踩到了陷阱！HP -20';
      gameState.hp -= 20;
    } else {
      message = '这个方向没有路可走。';
    }
    gameState.log.push(message);
    saveGame();
    printStatus();
  }
  
  // 4. 打印当前状态
  function printStatus() {
    console.log("--------------------------------");
    console.log(`当前位置: ${gameState.position}`);
    console.log(`❤️  生命值: ${gameState.hp}`);
    console.log(`🎒 背包: [${gameState.inventory.join(', ')}]`);
    console.log(`📜 日志: ${gameState.log[gameState.log.length - 1]}`); // 只显示最新日志
    console.log("--------------------------------");
  }
  
  // --- 模拟玩家操作 ---
  console.log("--- 游戏开始 ---");
  printStatus();
  
  console.log("\n// 玩家选择向前走...");
  move('forward');

  console.log("\n// 玩家选择向左走...");
  move('left');

  console.log("\n🚨 噢不！手滑刷新了页面！别担心，游戏进度还在。");
  console.log("（再次运行此代码块即可模拟刷新后的加载效果）");
}

// 运行游戏
caveAdventure();
```

### 💡 记忆要点
- **会话生命周期**：数据仅在当前浏览器标签页中有效，关闭标签页后数据即被清除。
- **字符串存储**：`SessionStorage` 只能存储字符串。存储对象或数组前，必须使用 `JSON.stringify()`；读取后，需使用 `JSON.parse()`。
- **API简洁**：核心API只有 `setItem(key, value)`, `getItem(key)`, `removeItem(key)`, 和 `clear()`，非常易于使用。

<!--
metadata:
  syntax: []
  pattern: [data-persistence]
  api: [sessionStorage, JSON.stringify, JSON.parse]
  concept: [web-storage, session]
  difficulty: basic
  dependencies: []
  related: [js-sec-8-2-2]
-->