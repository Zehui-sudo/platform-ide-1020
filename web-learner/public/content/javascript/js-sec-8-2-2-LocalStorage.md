## LocalStorage

### 🎯 核心概念
LocalStorage 允许你在用户的浏览器中持久地存储键值对数据，即使用户关闭了浏览器或电脑，这些数据依然存在，直到被手动清除。

### 📚 Level 1: 基础认知（30秒理解）
```javascript
// 清理一下，确保我们从一个干净的状态开始
localStorage.clear();

console.log("--- 存储前 ---");
// 尝试获取一个还不存在的数据，会返回 null
const myNameBefore = localStorage.getItem('username');
console.log("我的名字是:", myNameBefore); // 输出: null

console.log("\n--- 存储后 ---");
// 使用 setItem 存储数据，键是 'username'，值是 'CodeMaster'
localStorage.setItem('username', 'CodeMaster');

// 再次获取数据
const myNameAfter = localStorage.getItem('username');
console.log("我的名字是:", myNameAfter); // 输出: CodeMaster
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 数据持久性
LocalStorage 中的数据没有过期时间，它会一直存在，除非被代码（`removeItem` 或 `clear`）或用户（手动清除浏览器缓存）删除。

```javascript
// 模拟第一次访问：存储用户偏好
// 假设这是用户第一次访问我们的网站
localStorage.setItem('theme', 'dark');
console.log("用户首次访问，设置主题为 'dark'");

// 模拟用户关闭浏览器后再次打开
// 在这个独立的代码块中，我们直接尝试获取数据
// 如果你刷新页面或关闭再打开，这个值依然存在
const savedTheme = localStorage.getItem('theme');
console.log(`欢迎回来！你之前保存的主题是: ${savedTheme}`); // 输出: dark
```

#### 特性2: 只能存储字符串
LocalStorage 只能存储字符串类型的数据。如果你尝试存储其他类型（如数字、布尔值、对象），它会自动调用 `toString()` 方法将其转换为字符串。

```javascript
// 存储不同类型的数据
localStorage.setItem('userAge', 25); // 数字 25
localStorage.setItem('isVip', true); // 布尔值 true
localStorage.setItem('userInfo', { name: 'Alice', level: 99 }); // 对象

// 取出数据，并检查它们的类型
const age = localStorage.getItem('userAge');
const vipStatus = localStorage.getItem('isVip');
const user = localStorage.getItem('userInfo');

console.log(`获取到的年龄: ${age}, 类型是: ${typeof age}`); // 输出: "25", 类型是: string
console.log(`获取到的VIP状态: ${vipStatus}, 类型是: ${typeof vipStatus}`); // 输出: "true", 类型是: string
console.log(`获取到的用户信息: ${user}, 类型是: ${typeof user}`); // 输出: "[object Object]", 类型是: string
```

#### 特性3: 完整的CRUD操作
LocalStorage 提供了一套简单的方法来管理数据：创建(Create)、读取(Read)、更新(Update)、删除(Delete)。

```javascript
// 1. 清空所有存储，以防之前有残留数据
localStorage.clear();
console.log("LocalStorage 已清空。");

// 2. 创建 (Create) / 更新 (Update) 数据
// setItem 如果键不存在则创建，如果存在则更新
localStorage.setItem('player', 'Zelda');
localStorage.setItem('score', '100');
console.log("创建数据: player='Zelda', score='100'");

// 3. 读取 (Read) 数据
const currentPlayer = localStorage.getItem('player');
console.log(`读取玩家: ${currentPlayer}`);

// 4. 删除 (Delete) 单个数据
localStorage.removeItem('score');
console.log("删除了 'score'。");

// 5. 验证删除
const currentScore = localStorage.getItem('score');
console.log(`再次读取分数: ${currentScore}`); // 输出: null

// 6. 清空所有数据
localStorage.setItem('tempData1', 'abc');
localStorage.setItem('tempData2', '123');
console.log("添加了一些临时数据...");
localStorage.clear();
console.log("执行 clear() 后，所有数据均被删除。");
const temp1 = localStorage.getItem('tempData1');
console.log(`获取临时数据1: ${temp1}`); // 输出: null
```

### 🔍 Level 3: 对比学习（避免陷阱）
最常见的错误是直接存储和读取 JavaScript 对象，这会导致数据丢失。正确的方式是使用 `JSON.stringify()` 和 `JSON.parse()`。

```javascript
// 准备一个玩家对象
const playerProfile = {
  name: "Link",
  level: 10,
  inventory: ["Sword", "Shield", "Potion"]
};

console.log("=== 错误用法 ===");
// ❌ 直接存储对象
localStorage.setItem('playerWrong', playerProfile);
const wrongData = localStorage.getItem('playerWrong');
console.log("直接存储对象后取出的值:", wrongData); // 输出: [object Object]
console.log("数据类型:", typeof wrongData); // 输出: string
// 解释: 对象被转换成了字符串 "[object Object]"，所有有用的信息都丢失了。

console.log("\n=== 正确用法 ===");
// ✅ 使用 JSON.stringify() 将对象转换为 JSON 字符串
const playerProfileString = JSON.stringify(playerProfile);
localStorage.setItem('playerCorrect', playerProfileString);
console.log("用JSON.stringify转换后的字符串:", playerProfileString);

// 从 LocalStorage 取出字符串
const correctDataString = localStorage.getItem('playerCorrect');
// 使用 JSON.parse() 将字符串解析回原始对象
const correctDataObject = JSON.parse(correctDataString);
console.log("用JSON.parse解析回的对象:", correctDataObject);
console.log("玩家名字:", correctDataObject.name); // 输出: Link
console.log("玩家等级:", correctDataObject.level); // 输出: 10
// 解释: 通过序列化和反序列化，我们完美地保存和恢复了整个对象结构。
```

### 🚀 Level 4: 实战应用（真实场景）

**场景：🐾 虚拟宠物养成游戏**

你正在开发一个简单的网页版虚拟宠物游戏。玩家可以给宠物喂食和陪它玩耍，并希望在关闭浏览器后，宠物的状态（饥饿度、快乐度）能够被保存下来。

```javascript
// 虚拟宠物状态管理器
function virtualPetGame() {
  const PET_STORAGE_KEY = 'myVirtualPet';

  // 1. 尝试从 LocalStorage 加载宠物数据
  let pet;
  const savedPetData = localStorage.getItem(PET_STORAGE_KEY);

  if (savedPetData) {
    pet = JSON.parse(savedPetData);
    console.log(`🌟 欢迎回来！找到了你上次照顾的宠物: ${pet.name}！`);
  } else {
    // 如果没有找到数据，就创建一只新宠物
    pet = {
      name: "皮卡丘",
      hunger: 50, // 0-100, 越低越好
      happiness: 50, // 0-100, 越高越好
    };
    console.log(`🐾 欢迎新主人！你领养了一只叫 ${pet.name} 的新宠物！`);
  }

  // 显示宠物当前状态的函数
  function showStatus() {
    console.log(`--- ${pet.name} 的状态 ---`);
    console.log(`🍔 饥饿度: ${pet.hunger}/100`);
    console.log(`😊 快乐度: ${pet.happiness}/100`);
    if (pet.hunger > 70) console.log("（咕噜咕噜... 我好饿呀！）");
    if (pet.happiness < 30) console.log("（呜... 感觉有点孤单...）");
    console.log("----------------------");
  }

  // 喂食函数
  function feed() {
    console.log("🍖 你给它吃了一个美味的树果...");
    pet.hunger = Math.max(0, pet.hunger - 20); // 饥饿度降低
    pet.happiness = Math.min(100, pet.happiness + 5); // 快乐度稍微增加
  }

  // 玩耍函数
  function play() {
    console.log("🎾 你和它玩了扔球游戏...");
    pet.hunger = Math.min(100, pet.hunger + 10); // 玩耍会消耗体力，增加饥饿度
    pet.happiness = Math.min(100, pet.happiness + 25); // 快乐度大幅增加
  }

  // 保存进度的函数
  function saveProgress() {
    localStorage.setItem(PET_STORAGE_KEY, JSON.stringify(pet));
    console.log("💾 游戏进度已保存！下次见！");
  }

  // --- 模拟游戏流程 ---
  console.log("\n--- 游戏开始 ---");
  showStatus();

  console.log("\n--- 互动时间 ---");
  feed();
  play();
  
  console.log("\n--- 互动后状态 ---");
  showStatus();

  console.log("\n--- 游戏结束，保存进度 ---");
  saveProgress();
  console.log("提示：再次运行此代码块，你会看到宠物状态被成功加载了！");
}

// 运行游戏
virtualPetGame();
```

### 💡 记忆要点
- **要点1**：LocalStorage 中的数据是**持久**的，关闭浏览器也不会丢失。
- **要点2**：它只能存储**字符串**，对于对象或数组，必须使用 `JSON.stringify()` 和 `JSON.parse()` 进行转换。
- **要点3**：数据存储是与**浏览器和域名**绑定的，在 `a.com` 存储的数据在 `b.com` 是无法访问的。

<!--
metadata:
  syntax: ["let", "const", "function", "if-else"]
  pattern: ["data-persistence", "JSON-serialization"]
  api: ["localStorage.setItem", "localStorage.getItem", "localStorage.removeItem", "localStorage.clear", "JSON.stringify", "JSON.parse", "console.log"]
  concept: ["web-storage", "data-persistence", "serialization"]
  difficulty: basic
  dependencies: ["无"]
  related: ["js-sec-8-2-3"]
-->