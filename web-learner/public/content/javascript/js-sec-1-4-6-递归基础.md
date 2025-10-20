## 递归基础

### 🎯 核心概念
递归是一种编程技巧，一个函数通过调用自身来解决问题，通常用于将一个大问题分解为一系列结构相同的、更小的子问题。

### 📚 Level 1: 基础认知（30秒理解）
想象一下一个倒计时机器人，它的任务是报数。当被要求从3开始倒数时，它会先喊出“3”，然后把“从2开始倒数”这个稍小的任务交给另一个自己来完成。

```javascript
// 一个简单的倒计时函数
function countdown(number) {
  // 如果数字大于0，就继续
  if (number > 0) {
    console.log(`倒计时: ${number}`);
    // 调用自身，但数字减1
    countdown(number - 1);
  } else {
    // 当数字为0时，停止并打印发射
    console.log("🚀 发射!");
  }
}

// 从3开始倒计时
countdown(3);
```

### 📈 Level 2: 核心特性（深入理解）
递归函数必须包含两个关键部分才能正常工作：基本情况和递归步骤。

#### 特性1: 基本情况 (Base Case)
基本情况是递归的“停止信号”。它是一个明确的条件，当满足该条件时，函数将不再调用自身，从而结束递归，防止无限循环。

```javascript
// 计算阶乘的函数：n! = n * (n-1) * ... * 1
function factorial(n) {
  // 基本情况：当n为1或0时，阶乘就是1，停止递归
  if (n <= 1) {
    console.log(`基本情况达成: n = ${n}，返回 1`);
    return 1;
  }
  
  // 递归步骤（将在下一个特性中详细说明）
  console.log(`递归步骤: n = ${n}, 计算 ${n} * factorial(${n - 1})`);
  return n * factorial(n - 1);
}

const result = factorial(4); // 4 * 3 * 2 * 1 = 24
console.log("4的阶乘是:", result);
```

#### 特性2: 递归步骤 (Recursive Step)
递归步骤是函数调用自身的部分。在每次调用中，它都会修改参数，使其朝着“基本情况”靠近一步，确保递归最终能够结束。

```javascript
// 计算数组中所有数字的和
function sumArray(arr) {
  // 基本情况：如果数组为空，和为0
  if (arr.length === 0) {
    console.log("基本情况：数组为空，返回 0");
    return 0;
  }

  // 递归步骤：
  // 取出第一个元素
  const firstElement = arr[0];
  // 对剩余的数组部分调用自身
  const restOfArray = arr.slice(1);
  
  console.log(`递归步骤: 取出 ${firstElement}, 递归计算 [${restOfArray}] 的和`);
  
  return firstElement + sumArray(restOfArray);
}

const numbers = [5, 2, 8];
const total = sumArray(numbers);
console.log(`数组 [${numbers.join(', ')}] 的总和是:`, total);
```

### 🔍 Level 3: 对比学习（避免陷阱）
最常见的递归错误就是忘记设置“基本情况”，导致无限递归，最终使程序崩溃。

```javascript
// 完整的对比示例
console.log("=== 错误用法 ===");
// ❌ 错误：没有基本情况的递归函数
function infiniteGreeting(count) {
  // 这个函数缺少一个停止条件
  console.log(`Hello, this is greeting #${count}!`);
  // 它会无休止地调用自己，直到程序崩溃
  // infiniteGreeting(count + 1); // 为了防止浏览器卡死，这里注释掉了
}
console.log("❌ 错误示例：如果取消注释，`infiniteGreeting(1)` 将导致'Maximum call stack size exceeded'错误。");


console.log("\n=== 正确用法 ===");
// ✅ 正确：有明确基本情况的递归函数
function controlledGreeting(count, maxGreetings) {
  // 基本情况：当问候次数达到上限时，停止
  if (count > maxGreetings) {
    console.log("✅ 达到问候上限，停止递归！");
    return;
  }

  // 递归步骤：打印问候语并调用自身，同时向基本情况靠近
  console.log(`Hello, this is greeting #${count}!`);
  controlledGreeting(count + 1, maxGreetings);
}

console.log("✅ 正确示例：开始有限次数的问候...");
controlledGreeting(1, 3); // 最多问候3次
```

### 🚀 Level 4: 实战应用（真实场景）
**🚀 科幻冒险：探索神秘的俄罗斯套娃宝箱**

你是一名星际探险家，发现了一个来自外星文明的神秘宝箱。这个宝箱像俄罗斯套娃一样，里面可能装着更小的宝箱，也可能装着终极宝藏——“宇宙之心”！我们来写一个递归函数，自动探索所有宝箱，直到找到宝藏。

```javascript
// 定义宝箱的结构，一个嵌套的对象
const alienTreasureChest = {
  color: '银色',
  content: {
    type: 'box',
    color: '蓝色',
    content: {
      type: 'box',
      color: '金色',
      content: {
        type: 'treasure',
        name: '宇宙之心'
      }
    }
  }
};

// 递归函数，用来探索宝箱
function exploreChest(chest) {
  console.log(`🕵️‍ 正在打开一个【${chest.color}】的宝箱...`);

  // 检查宝箱里的内容
  const content = chest.content;

  // 基本情况：如果内容是宝藏，就找到了！
  if (content.type === 'treasure') {
    console.log(`🎉 哇！找到了终极宝藏：【${content.name}】！任务完成！`);
    return;
  }

  // 递归步骤：如果内容是另一个箱子，就继续探索
  if (content.type === 'box') {
    console.log(`...发现里面还有一个更小的【${content.color}】宝箱。继续深入！`);
    exploreChest(content); // 对内部的宝箱调用自身
  }
}

console.log("--- 星际探险开始！---");
exploreChest(alienTreasureChest);
console.log("--- 探险结束！---");
```

### 💡 记忆要点
- **函数调用自身**：递归的核心是函数在自己的代码块内部调用自己。
- **必须有出口**：每个递归函数都必须有一个“基本情况”（Base Case），作为递归的终止条件，否则会造成无限循环。
- **问题规模递减**：在每次递归调用时，传递给函数的参数必须向“基本情况”靠近，例如数字减小、数组变短等。

<!--
metadata:
  syntax: ["function"]
  pattern: ["recursion"]
  api: ["console.log", "Array.slice"]
  concept: ["call-stack", "recursion", "base-case"]
  difficulty: intermediate
  dependencies: []
  related: []
-->