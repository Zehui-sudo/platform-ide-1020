## 数组排序与反转

### 🎯 核心概念
数组排序与反转是整理数组内元素顺序的核心操作，能让我们根据特定规则（如字母顺序、数值大小）重新排列数据，或直接颠倒现有顺序。

### 📚 Level 1: 基础认知（30秒理解）
`sort()` 方法用于按字母顺序排序，`reverse()` 方法用于将数组元素颠倒。

```javascript
// Level 1: 基础用法
const heroes = ['Iron Man', 'Captain America', 'Thor', 'Hulk'];
console.log("原始英雄列表:", heroes);

// 使用 sort() 按字母顺序排序
heroes.sort();
console.log("按字母排序后:", heroes);

// 使用 reverse() 将排序后的列表反转
heroes.reverse();
console.log("反转排序后:", heroes);
```

### 📈 Level 2: 核心特性（深入理解）
深入了解 `sort()` 和 `reverse()` 的工作方式，特别是它们如何处理数字和如何影响原始数组。

#### 特性1: sort() 和 reverse() 会直接修改原数组
这两个方法是“破坏性”的，它们不会创建新数组，而是直接在原始数组上进行修改。

```javascript
// 定义一个原始数组
const originalArray = ['a', 'c', 'b'];
console.log("原始数组:", originalArray);

// 创建一个指向原始数组的引用
const referenceToArray = originalArray;

// 对原始数组进行排序
originalArray.sort();

console.log("排序后的原始数组:", originalArray); // 原始数组被改变
console.log("引用的数组也变了:", referenceToArray); // 引用也指向改变后的数组

// 对已排序的数组进行反转
originalArray.reverse();
console.log("反转后的原始数组:", originalArray); // 再次被改变
```

#### 特性2: sort() 的默认行为与自定义排序函数
默认情况下，`sort()` 方法会将所有元素转换为字符串，然后按 UTF-16 编码顺序进行排序。这对于数字排序通常不是我们想要的结果。

```javascript
// 默认排序（字符串排序）
const scores = [100, 10, 2, 21];
console.log("原始分数:", scores);

// 默认排序会产生意想不到的结果
// 因为 "100" 在字符串中排在 "2" 前面
scores.sort();
console.log("默认排序（错误）:", scores); // 输出 [10, 100, 2, 21]

// 自定义排序（数值排序）
const correctScores = [100, 10, 2, 21];
// 提供一个比较函数 (a, b) => a - b 来实现升序排列
correctScores.sort((a, b) => a - b);
console.log("使用比较函数排序（正确升序）:", correctScores); // 输出 [2, 10, 21, 100]

// 使用 (a, b) => b - a 实现降序排列
correctScores.sort((a, b) => b - a);
console.log("使用比较函数排序（正确降序）:", correctScores); // 输出 [100, 21, 10, 2]
```

### 🔍 Level 3: 对比学习（避免陷阱）
直接对数字数组使用 `sort()` 是一个非常常见的错误，让我们来对比一下。

```javascript
const playerLevels = [5, 8, 1, 12, 30, 2];

console.log("=== 错误用法 ===");
// ❌ 错误：没有提供比较函数，导致按字符串顺序排序
const wrongSortedLevels = [...playerLevels]; // 创建副本以防修改原数组
wrongSortedLevels.sort();
console.log("错误排序结果:", wrongSortedLevels);
// 解释：数字被转为字符串 "5", "8", "1", "12", "30", "2"。
// 排序时 "1" 在 "12" 之后，"12" 在 "2" 之前，因为比较的是第一个字符。

console.log("=== 正确用法 ===");
// ✅ 正确：提供了比较函数 (a, b) => a - b，实现按数值大小升序排序
const correctSortedLevels = [...playerLevels]; // 创建副本
correctSortedLevels.sort((a, b) => a - b);
console.log("正确排序结果:", correctSortedLevels);
// 解释：当 a - b 返回负数时，a排在b前面；返回正数时，b排在a前面。
// 这确保了数组按数值大小正确排序。
```

### 🚀 Level 4: 实战应用（真实场景）
**场景：🎮 复古街机游戏排行榜**

我们正在开发一款像素风格的太空射击游戏，需要一个动态的排行榜来展示玩家的最高分。我们需要对玩家数据进行排序，并展示前三名“宇宙英雄”和垫底的“新手飞行员”。

```javascript
// 游戏玩家数据，每个对象包含名字和分数
const playerScores = [
  { name: '🚀 TopGun', score: 9850 },
  { name: '🧑‍🚀 StarLord', score: 7600 },
  { name: '👾 InvaderX', score: 10500 },
  { name: '✨ Nova', score: 8800 },
  { name: '🤖 C-3PO-ops', score: 5200 },
];

console.log("--- 🚀 太空射击游戏排行榜 ---");
console.log("原始比赛数据:", playerScores);

// 1. 按分数从高到低排序，决出宇宙英雄！
// 我们使用 b.score - a.score 来实现降序排序
playerScores.sort((playerA, playerB) => playerB.score - playerA.score);

console.log("\n🏆 **最终排行榜** 🏆");
playerScores.forEach((player, index) => {
  console.log(`#${index + 1}: ${player.name} - ${player.score} 分`);
});

// 2. 使用 reverse() 快速查看垫底玩家，鼓励他们！
// 注意：这会再次修改已经排好序的数组
playerScores.reverse();

console.log("\n--- 😅 新手飞行员鼓励榜 ---");
console.log("别灰心，下次加油！");
for (let i = 0; i < 3; i++) {
  if (playerScores[i]) {
    console.log(`- ${playerScores[i].name} (${playerScores[i].score} 分)`);
  }
}
```

### 💡 记忆要点
- **要点1**：`sort()` 和 `reverse()` 会直接修改（“破坏”）原始数组，而不是返回一个新数组。
- **要点2**：对数字数组使用 `sort()` 时，必须提供一个比较函数，例如 `(a, b) => a - b`（升序）或 `(a, b) => b - a`（降序）。
- **要点3**：默认的 `sort()` 行为是按字符串的字典顺序进行排序，这对于数字和复杂对象通常是错误的。

<!--
metadata:
  syntax: [arrow-function, function]
  pattern: [callback]
  api: [Array.sort, Array.reverse, console.log, Array.forEach]
  concept: [in-place-algorithm, comparison-function]
  difficulty: intermediate
  dependencies: [无]
  related: []
-->