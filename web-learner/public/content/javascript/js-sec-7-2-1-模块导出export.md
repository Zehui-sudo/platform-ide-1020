## 模块导出export

### 🎯 核心概念
`export` 关键字用于将 JavaScript 文件（模块）中的函数、对象或原始值“暴露”出去，以便其他程序可以通过 `import` 语句使用它们。这是现代 JavaScript 中组织和重用代码的基础。

### 📚 Level 1: 基础认知（30秒理解）
我们可以把一个 `.js` 文件想象成一个工具箱。`export` 就是给工具箱里的某个工具贴上一个“可外借”的标签，这样别的代码就知道可以从这个工具箱里借用它。

```javascript
// 假设这是文件: 'mathUtils.js'
// 我们在这里定义并导出内容

// 导出一个变量
export const PI = 3.14159;

// 导出一个函数
export function circleArea(radius) {
  return PI * radius * radius;
}

// --- 为了让这个代码块能独立运行并展示结果 ---
// 在真实的模块文件中，你通常不会在顶层写这些 console.log。
// 但为了教学演示，我们在这里打印一下导出的内容，证明它们是存在的。
console.log("在 'mathUtils.js' 模块中:");
console.log("导出的常量 PI:", PI);
const area = circleArea(10);
console.log("调用导出的函数 circleArea(10):", area);
console.log("✅ 这个模块已准备好导出 'PI' 和 'circleArea'。");
// 在另一个文件中，你就可以这样使用: import { PI, circleArea } from './mathUtils.js';
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 命名导出 (Named Exports)
一个模块可以导出多个变量、函数或类。这些导出项通过它们的名字来区分，导入时也必须使用完全相同的名字。

有两种常见的命名导出语法：

1.  在声明时直接导出。
2.  在文件末尾用一个 `export` 语句集中导出。

```javascript
// 假设这是文件: 'stringUtils.js'

// 语法1: 在声明时直接导出
export const version = "1.0";

export function toUpperCase(str) {
  return str.toUpperCase();
}

// 语法2: 集中在文件末尾导出
function toLowerCase(str) {
  return str.toLowerCase();
}
const author = "JS Expert";

// 使用一个 export 语句导出多个
export { toLowerCase, author };


// --- 教学演示 ---
console.log("模块 'stringUtils.js' 准备了以下命名导出项：");
console.log("- version:", version);
console.log("- toUpperCase:", toUpperCase("hello"));
console.log("- toLowerCase:", toLowerCase("WORLD"));
console.log("- author:", author);
console.log("在其他文件中可以通过 `import { version, toUpperCase, toLowerCase, author } from './stringUtils.js'` 来使用它们。");
```

#### 特性2: 默认导出 (Default Export)
每个模块可以有一个“默认”导出。它通常是这个模块最核心、最主要的导出内容。在导入时，可以为这个默认导出指定任何你喜欢的名字。一个模块只能有一个 `export default`。

```javascript
// 假设这是文件: 'userProfile.js'

class User {
  constructor(name, age) {
    this.name = name;
    this.age = age;
  }

  getInfo() {
    return `用户: ${this.name}, 年龄: ${this.age}`;
  }
}

// 将 User 类作为默认导出
export default User;


// --- 教学演示 ---
console.log("模块 'userProfile.js' 提供了一个默认导出。");
// 模拟创建一个实例来验证
const defaultExportedClass = User;
const testUser = new defaultExportedClass("Alice", 30);
console.log("导出的内容是一个类，我们可以用它创建实例:");
console.log(testUser.getInfo());
console.log("在其他文件中，可以这样导入: `import MyUser from './userProfile.js'`，其中 'MyUser' 是可以自定义的名称。");
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个常见的陷阱是混淆 `export default` 和命名导出的用法，尤其是试图在一个文件中使用多个 `export default`。

```javascript
// === 错误用法 ===
console.log("=== 错误用法 ===");
// ❌ 语法错误：一个模块中不能有多个 export default
// export default function greet() { console.log("Hello"); }
// export default const name = "World"; // 这会直接导致语法错误

// 为了让代码块能运行，我们将错误代码注释掉并解释
console.log("❌ 错误：一个文件只能有一个 'export default'。");
console.log("   它代表模块的“主要”输出。如果你需要导出多个东西，应该使用命名导出。");


console.log("\n=== 正确用法 ===");
// ✅ 正确做法：结合使用一个默认导出和多个命名导出
// 假设这是文件: 'formatter.js'

// 默认导出：最常用的格式化函数
function formatCurrency(amount) {
  return `$${amount.toFixed(2)}`;
}
export default formatCurrency;

// 命名导出：其他辅助函数
export function formatDate(date) {
  return date.toISOString().split('T')[0];
}
export const version = "2.1";

// --- 教学演示 ---
console.log("✅ 正确：一个模块可以同时拥有一个默认导出和多个命名导出。");
const mainExport = formatCurrency;
console.log("默认导出 (formatCurrency):", mainExport(12.3));
console.log("命名导出 (formatDate):", formatDate(new Date()));
console.log("命名导出 (version):", version);
console.log("导入时可以这样写: `import format, { formatDate, version } from './formatter.js';`");
```

### 🚀 Level 4: 实战应用（真实场景）
**场景：🎮 为一个奇幻角色扮演游戏创建一个角色工具模块 `characterUtils.js`**

这个模块将负责创建角色，提供随机名称生成器和掷骰子功能。我们将使用 `export default` 导出核心的 `Character` 类，并用命名导出提供辅助工具函数。

```javascript
// 假设这是文件: 'characterUtils.js'
// =======================================
// 这个模块提供了创建游戏角色所需的一切！

// 默认导出: 核心的角色类，这是模块的主要功能
class Character {
  constructor(name, race, strength, dexterity, intelligence) {
    this.name = name;
    this.race = race;
    this.stats = { strength, dexterity, intelligence };
    this.hp = 10 + Math.floor(strength / 2); // 生命值基于力量
    this.inventory = [];
  }

  introduce() {
    console.log(`⚔️ 我是 ${this.name}，一个勇敢的${this.race}！我的力量是 ${this.stats.strength}！`);
  }

  addToInventory(item) {
    this.inventory.push(item);
    console.log(`🎒 ${this.name} 的背包里新增了: ${item}`);
  }
}
// 在真实模块中，你会写: export default Character;

// 命名导出: 一些有用的工具函数
const fantasyNames = ["艾拉瑞亚", "格罗姆", "莉安德拉", "索林"];
function generateRandomName() {
  console.log("🔮 命运之轮正在转动，为你选择一个名字...");
  return fantasyNames[Math.floor(Math.random() * fantasyNames.length)];
}
// 在真实模块中，你会写: export { generateRandomName };

function rollD20() {
  console.log("🎲 投掷20面骰子...");
  return Math.floor(Math.random() * 20) + 1;
}
// 在真实模块中，你会写: export { rollD20 };


// --- 模拟在另一个文件 'game.js' 中使用这个模块 ---
console.log("🚀 欢迎来到奇幻世界！开始创建你的游戏角色！\n");

// 假设我们已经导入:
// import Character, { generateRandomName, rollD20 } from './characterUtils.js';

// 使用命名导出的函数生成名字
const playerName = generateRandomName();

// 使用默认导出的 Character 类和命名导出的 rollD20 函数创建英雄
const myHero = new Character(
  playerName,
  "精灵弓箭手",
  rollD20(), // 力量
  rollD20(), // 敏捷
  rollD20()  // 智力
);

myHero.introduce();
myHero.addToInventory("精灵长弓");
myHero.addToInventory("一袋金币");

console.log("\n--- ✨ 角色创建完毕 ---");
console.log("你的英雄信息:", JSON.stringify(myHero, null, 2));
```

### 💡 记忆要点
- **要点1**：`export` 让你的代码可以被其他文件复用，是模块化的基石。
- **要点2**：`export { name1, name2 }` 是命名导出，可以导出多个，导入时名称必须完全一致。
- **要点3**：`export default` 是默认导出，每个文件最多一个，导入时可以自己随便起名字。

<!--
metadata:
  syntax: ["export", "named-export", "default-export", "class", "function"]
  pattern: ["module"]
  api: ["console.log", "Math.random", "Math.floor"]
  concept: ["modules", "encapsulation"]
  difficulty: intermediate
  dependencies: ["无"]
  related: ["js-sec-7-2-2"]
-->