## 数组遍历（for/forEach）

### 🎯 核心概念
数组遍历就像是按顺序点名一个班级的学生，你需要一种方法来访问数组中的每一个元素，并对它们执行某些操作，比如打印、计算或修改。

### 📚 Level 1: 基础认知（30秒理解）
想象你有一个水果篮（数组），想把里面的水果名字都喊一遍。最经典的方法就是使用`for`循环，像数手指一样，从第一个数到最后一个。

```javascript
// 水果篮里有三种水果
const fruits = ['🍎 苹果', '🍌 香蕉', '🍊 橘子'];

console.log("水果篮里有什么？");

// 使用 for 循环，从索引 0 开始，逐个访问
for (let i = 0; i < fruits.length; i++) {
  // fruits[i] 可以获取到当前循环到的水果
  console.log(`找到了: ${fruits[i]}`);
}
```

### 📈 Level 2: 核心特性（深入理解）
`for`循环很经典，但ES5之后，数组有了一个更简洁的遍历方法：`forEach`。

#### 特性1: `forEach`的简洁语法
`forEach`方法让我们告别手写索引 `i`，代码更易读。它接受一个函数作为参数，数组中的每个元素都会调用一次这个函数。

```javascript
const heroes = ['孙悟空', '猪八戒', '沙悟净'];

console.log("--- 西天取经团队点名 ---");

// forEach 接收一个函数，该函数有三个可选参数：
// 1. element: 当前元素的值
// 2. index: 当前元素的索引
// 3. array: 正在遍历的数组本身
heroes.forEach(function(hero, index, arr) {
  console.log(`队员${index + 1}: ${hero}`);
  // 在最后一次迭代时，打印整个团队信息
  if (index === arr.length - 1) {
    console.log(`\n团队全员 (${arr.length}人) 已到齐!`);
  }
});
```

#### 特性2: `for`循环的完全控制权
`for`循环虽然代码多一点，但它给了你完全的控制权。你可以使用 `break` 提前跳出循环，或使用 `continue` 跳过当前这次循环，而这些是 `forEach` 做不到的。

```javascript
const treasureMapClues = ['往东走', '找到大树', '危险！有妖怪！', '挖三尺', '找到宝藏'];

console.log("--- 开始寻宝！---");

for (let i = 0; i < treasureMapClues.length; i++) {
  const clue = treasureMapClues[i];
  
  if (clue.includes('危险')) {
    console.log(`发现线索: "${clue}"。太危险了，我们得停下来！`);
    break; // 遇到危险，立刻停止寻宝（跳出循环）
  }

  console.log(`执行线索: "${clue}"`);
}

console.log("--- 寻宝结束 ---");
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个常见的误区是试图在`forEach`中使用`break`或`continue`。这是行不通的，并可能导致意外的结果。

```javascript
// 假设我们只想找到第一个偶数就停止
const numbers = [1, 3, 5, 4, 7, 8];

console.log("=== 错误用法 ===");
// ❌ 尝试在 forEach 中使用 break 是无效的，甚至会直接导致语法错误。
//    我们用 return 来模拟“跳过”或“停止”的意图，但它只会结束当前这次函数调用，循环会继续。
let foundNumber_wrong;
numbers.forEach(num => {
  if (foundNumber_wrong) {
    return; // 以为可以停止，但其实只是结束了本次回调，循环仍在继续
  }
  if (num % 2 === 0) {
    console.log(`(错误的方式) 找到了偶数: ${num}`);
    foundNumber_wrong = num;
  }
});
console.log(`最终找到的数字是: ${foundNumber_wrong}。但注意，循环其实没有停下！`);


console.log("\n=== 正确用法 ===");
// ✅ 当需要提前中断循环时，应该使用传统的 for 循环。
let foundNumber_correct;
for (let i = 0; i < numbers.length; i++) {
  const num = numbers[i];
  if (num % 2 === 0) {
    console.log(`(正确的方式) 找到了偶数: ${num}，停止搜索。`);
    foundNumber_correct = num;
    break; // 使用 break 立刻终止整个循环
  }
}
console.log(`最终找到的数字是: ${foundNumber_correct}`);

```

### 🚀 Level 4: 实战应用（真实场景）
**场景：🚀 科幻冒险 - 飞船启动自检程序**

你即将驾驶 "开拓者号" 飞船进行星际穿越！在起飞前，AI助手需要遍历所有关键系统，进行一次快速自检。

```javascript
// 定义飞船的关键系统列表
const shipSystems = [
  { name: '🚀 主引擎', status: 'offline' },
  { name: '🧭 导航系统', status: 'offline' },
  { name: '🛡️ 能量护盾', status: 'offline' },
  { name: '🌡️ 生命维持', status: 'offline' },
  { name: '🤖 AI助手', status: 'error' } // 噢不，有个系统出错了！
];

let allSystemsGo = true; // 启动标志，默认为true

console.log("--- “开拓者号” 启动前自检程序 ---");

// 使用 forEach 遍历所有系统
shipSystems.forEach((system, index) => {
  console.log(`\n[${index + 1}/${shipSystems.length}] 正在检查: ${system.name}...`);
  
  // 模拟一个随机的检测结果
  const isOk = Math.random() > 0.2 && system.status !== 'error'; // 80%的几率正常，除非本身就是error状态
  
  if (isOk) {
    system.status = 'online';
    console.log(`✅ ${system.name}... 状态正常，已上线！`);
  } else {
    system.status = 'critical_error';
    allSystemsGo = false; // 任何一个系统出错，都不能起飞
    console.log(`❌ 警告! ${system.name} 出现严重故障！`);
  }
});

console.log("\n--- 自检程序结束 ---");

if (allSystemsGo) {
  console.log("🎉 所有系统准备就绪！引擎点火，准备起飞！");
} else {
  console.log("🚨 检测到关键系统故障！起飞程序已中止！请立即联系工程师！");
}
```

### 💡 记忆要点
- **`for`循环**：最经典，功能最全。当你需要使用 `break` 或 `continue` 来精确控制循环流程时，它是你的首选。
- **`forEach`方法**：语法更简洁、现代。当你需要对数组中的**每一个**元素执行相同操作，且不关心循环中断时，用它能让代码更优雅。
- **关键区别**：`forEach` 无法中途跳出整个循环，`return` 只能跳出当前的回调函数。

<!--
metadata:
  syntax: ["for-loop", "arrow-function"]
  pattern: ["iteration"]
  api: ["Array.forEach", "console.log"]
  concept: ["array-traversal", "callback", "control-flow"]
  difficulty: basic
  dependencies: ["js-sec-2-1-1"]
  related: ["js-sec-2-1-5", "js-sec-2-1-4"]
-->