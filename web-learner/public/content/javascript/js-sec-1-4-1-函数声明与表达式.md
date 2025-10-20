好的，作为一名专业的JavaScript教育专家，我将为你生成关于“函数声明与表达式”的学习内容。内容将严格遵循你的要求，结构清晰、代码完整、场景有趣。

---

## 函数声明与表达式

### 🎯 核心概念
在JavaScript中，函数是代码的“积木块”。**函数声明**和**函数表达式**是创建这些积木块的两种主要方式，它们的选择会影响函数在代码中的“可见”时机和使用灵活性。

### 📚 Level 1: 基础认知（30秒理解）
我们用两种方式来定义一个打招呼的函数，它们都能完成同样的工作。

```javascript
// 方式一：函数声明 (Function Declaration)
// 就像给一个行为起了个正式的名字
function greetDeclaration() {
  console.log("你好，我来自函数声明！");
}

// 方式二：函数表达式 (Function Expression)
// 就像创建一个函数，然后把它装进一个叫 greetExpression 的盒子里（变量）
const greetExpression = function() {
  console.log("你好，我来自函数表达式！");
};

// 调用它们
console.log("调用函数声明:");
greetDeclaration();

console.log("调用函数表达式:");
greetExpression();
```

### 📈 Level 2: 核心特性（深入理解）
这两种方式最核心的区别在于“提升”（Hoisting）和它们作为“值”的灵活性。

#### 特性1: 函数声明会被“提升”
JavaScript引擎在执行代码前，会先把函数声明“ उठाकर”（hoist）到作用域的顶部。这意味着你可以在函数定义之前调用它。

```javascript
// 在函数定义之前调用
sayHello(); // 输出: "你好呀！我被提升了！"

// 函数声明
function sayHello() {
  console.log("你好呀！我被提升了！");
}

console.log("即使在定义之前调用，函数声明也能正常工作。");
```

#### 特性2: 函数表达式不会被“提升”
函数表达式本质上是变量赋值，只有变量声明（`const hi`）会被提升，但赋值操作（`= function() {...}`）会留在原地。所以在赋值之前调用它，会得到一个错误。

```javascript
// 尝试在赋值之前调用函数表达式
try {
  sayHi(); // 这会引发一个错误！
} catch (error) {
  console.log("出错了:", error.message);
}

// 函数表达式：将一个匿名函数赋值给一个常量
const sayHi = function() {
  console.log("嗨！我是一个函数表达式，不能被提前调用。");
};

console.log("现在，在定义之后调用就没问题了：");
sayHi();
```

### 🔍 Level 3: 对比学习（避免陷阱）
让我们直观地对比一下这个最常见的“提升”陷阱。

```javascript
// 完整的对比示例，展示提升行为的区别

console.log("=== 错误用法 ❌ ===");
// 尝试调用一个尚未被赋值的函数表达式
try {
  // `wizardSpell` 这个变量存在（被提升），但它还没有被赋值为一个函数
  // 所以此时调用它会失败
  wizardSpell("火焰");
} catch (e) {
  console.log("施法失败:", e.message);
  console.log("原因：函数表达式和普通变量一样，必须在赋值后才能使用。");
}

const wizardSpell = function(spellName) {
  console.log(`🧙‍♂️ 释放咒语: ${spellName}!`);
};


console.log("\n=== 正确用法 ✅ ===");
// 函数声明可以在任意位置被调用，因为它被完整地提升了
godsBlessing("圣光"); // 正常工作

function godsBlessing(blessingName) {
  console.log(`✨ 降下神恩: ${blessingName}!`);
}
console.log("原因：函数声明在代码执行前就被完整加载，所以可以随处调用。");

// 对于函数表达式，在定义后调用是完全正确的
wizardSpell("冰霜"); // 正常工作
```

### 🚀 Level 4: 实战应用（真实场景）
**场景：神秘的占卜屋 🔮**

你走进了一家神秘的占卜屋，占卜师可以为你揭示未来。占卜的核心行为（揭示命运）是固定的，但使用的方法（水晶球、塔罗牌）可以灵活选择。

- **函数声明** 非常适合定义核心的、不变的流程，比如 `revealDestiny`。
- **函数表达式** 非常适合定义可替换的“策略”或“工具”，比如不同的占卜方法。

```javascript
// 核心功能：使用函数声明，因为它总是存在的
function revealDestiny(name, divinationMethod) {
  console.log(`\n欢迎你，勇敢的探险家 ${name}！`);
  console.log("我将为你揭示命运的丝线...");

  // 检查是否提供了有效的占卜方法（一个函数）
  if (typeof divinationMethod === 'function') {
    const fate = divinationMethod(); // 调用作为参数传入的函数
    console.log(`🌟 命运的启示: ${fate}`);
  } else {
    console.log("看来你没有选择占卜工具，命运今天保持了沉默。");
  }
  console.log("--------------------");
}

// 占卜工具：使用函数表达式，它们是可替换的“插件”
const useCrystalBall = function() {
  const outcomes = ["你的财富将如繁星般增长。", "一次意想不到的旅程在等着你。", "小心一个戴着红色帽子的陌生人。"];
  return outcomes[Math.floor(Math.random() * outcomes.length)];
};

const readTarotCards = function() {
  const cards = ["【愚者】：新的开始，无限可能。", "【魔术师】：创造力与机遇。", "【高塔】：突如其来的变革。"];
  return cards[Math.floor(Math.random() * cards.length)];
};

const interpretStars = function() {
    return "星象显示，今晚适合吃一顿大餐来犒劳自己！";
}


// --- 开始占卜！---
// 探险家 Alice 选择用水晶球
revealDestiny("Alice", useCrystalBall);

// 探险家 Bob 选择了塔罗牌
revealDestiny("Bob", readTarotCards);

// 探险家 Charlie 对星象感兴趣
revealDestiny("Charlie", interpretStars);
```

### 💡 记忆要点
- **要点1**：函数声明 `function name() {}` 会被整体提升，可以在定义前调用。
- **要点2**：函数表达式 `const name = function() {}` 不会被提升，必须先定义后使用，像普通变量一样。
- **要点3**：函数表达式更灵活，可以作为变量赋值、作为参数传递给其他函数，或从函数中返回。

<!--
metadata:
  syntax: ["function"]
  pattern: ["callback"]
  api: ["console.log", "Math.random", "Math.floor", "typeof"]
  concept: ["hoisting", "scope", "first-class-functions"]
  difficulty: basic
  dependencies: []
  related: ["js-sec-1-4-2"]
-->