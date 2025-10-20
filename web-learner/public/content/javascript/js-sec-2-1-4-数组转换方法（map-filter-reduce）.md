## 数组转换方法（map/filter/reduce）

### 🎯 核心概念
`map`, `filter`, 和 `reduce` 是JavaScript中处理数组的“三剑客”，它们能让你用一种更声明式、更简洁的方式来操作数组，而无需手动编写 `for` 循环。核心思想是**不修改原数组**，而是根据指定规则**返回一个全新的数组或值**，这也是函数式编程的基础。

### 📚 Level 1: 基础认知（30秒理解）
想象你有一篮子苹果，你想得到一篮子同样数量的苹果汁。`map` 就是那个榨汁机，它会对每个苹果进行处理，并返回一个新的东西。

```javascript
// 有一个数字数组，代表每个苹果的重量（克）
const appleWeights = [150, 180, 210, 165];

// 使用 map 方法，将每个苹果的重量转换为苹果汁的毫升数（假设 1g = 0.7ml）
const juiceVolumes = appleWeights.map(weight => weight * 0.7);

console.log("苹果重量数组:", appleWeights);
console.log("榨出的果汁量数组:", juiceVolumes);
// 注意：原始的 appleWeights 数组没有被改变
```

### 📈 Level 2: 核心特性（深入理解）
这三个方法各有分工，适用于不同场景。

#### 特性1: `map` - 转换器（一对一映射）
`map` 会遍历数组中的每个元素，并根据你提供的函数对每个元素进行处理，最后返回一个**长度与原数组相同**的新数组。

```javascript
// 游戏角色数据
const characters = [
  { name: '英雄A', level: 10 },
  { name: '法师B', level: 20 },
  { name: '刺客C', level: 15 }
];

// 需求：我们不关心等级，只想得到一个包含所有角色名字的列表
const characterNames = characters.map(char => char.name);

console.log("原始角色对象数组:", characters);
console.log("转换后的角色名数组:", characterNames);

// 另一个例子：给每个角色增加一个'title'属性
const charactersWithTitle = characters.map(char => {
  return {
    name: char.name,
    level: char.level,
    title: `Lv.${char.level} 的勇者` // 基于原始数据创建新属性
  };
});

console.log("添加了称号的新角色数组:", charactersWithTitle);
```

#### 特性2: `filter` - 过滤器（筛选符合条件的）
`filter` 像一个筛子，它会遍历数组，只保留那些通过你指定测试（函数返回 `true`）的元素，并返回一个**新数组**，其长度小于或等于原数组。

```javascript
// 一队冒险者，他们的生命值(hp)各不相同
const party = [
  { name: '战士', hp: 150 },
  { name: '弓箭手', hp: 80 },
  { name: '牧师', hp: 95 },
  { name: '坦克', hp: 200 }
];

// 需求：找出所有生命值低于100，需要治疗的队员
const needsHealing = party.filter(member => member.hp < 100);

console.log("完整的冒险队伍:", party);
console.log("需要治疗的队员:", needsHealing);

// 另一个例子：找出名字长度大于2的队员
const longNameMembers = party.filter(member => member.name.length > 2);
console.log("名字较长的队员:", longNameMembers);
```

#### 特性3: `reduce` - 汇总器（多合一）
`reduce` 是最强大的一个，它可以将数组中的所有元素“减少”为一个单一的值。这个值可以是数字、字符串、甚至是一个对象。它接受两个参数：一个回调函数和一个初始值。

```javascript
// 背包里有一堆战利品，每个都有价值
const loot = [
  { item: '金币', value: 50 },
  { item: '宝石', value: 200 },
  { item: '草药', value: 5 },
  { item: '金币', value: 25 }
];

// 需求：计算背包里所有物品的总价值
// reduce 回调函数接收两个主要参数：(accumulator, currentValue)
// accumulator 是上一次迭代返回的值，currentValue 是当前处理的元素
// 第二个参数 0 是 accumulator 的初始值
const totalValue = loot.reduce((sum, currentItem) => {
  console.log(`当前总和: ${sum}, 正在加上: ${currentItem.item} (价值 ${currentItem.value})`);
  return sum + currentItem.value;
}, 0);

console.log("背包里的战利品:", loot);
console.log("战利品总价值:", totalValue);
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个常见的陷阱是，在 `map` 或 `filter` 的回调函数中忘记 `return`。

```javascript
const numbers = [1, 2, 3];

console.log("=== 错误用法 ===");
// ❌ 错误: map 的回调函数使用了大括号但没有显式 return
const wrongMapResult = numbers.map(num => {
  // 只是执行了操作，但没有返回任何值
  num * 2;
});
console.log("错误 map 结果:", wrongMapResult);
console.log("解释: 当使用 `{}` 定义函数体时，必须使用 `return` 关键字返回值。否则，函数默认返回 `undefined`，新数组的每个元素都会是 `undefined`。");

console.log("\n=== 正确用法 ===");
// ✅ 正确: 使用显式 return
const correctMapResult1 = numbers.map(num => {
  return num * 2;
});
console.log("正确 map 结果 (带 return):", correctMapResult1);

// ✅ 正确: 使用箭头函数的隐式 return (当函数体只有一行时)
const correctMapResult2 = numbers.map(num => num * 2);
console.log("正确 map 结果 (隐式 return):", correctMapResult2);
console.log("解释: 两种正确方式都确保了回调函数为每个元素返回了一个计算后的新值，从而正确地构建了新数组。");
```

### 🚀 Level 4: 实战应用（真实场景）
**场景：🎨 创意互动 - 表情符号生成器**

我们来创建一个简单的“表情符号料理”游戏。玩家选择一些“原料”表情符号，我们将通过数组方法将它们“烹饪”成一道新的“表情符号菜肴”。

```javascript
// 烹饪原料库：每个原料都有名字、表情符号、类型和“风味值”
const ingredients = [
  { name: '番茄', emoji: '🍅', type: 'vegetable', flavor: 5 },
  { name: '奶酪', emoji: '🧀', type: 'dairy', flavor: 8 },
  { name: '面包', emoji: '🍞', type: 'grain', flavor: 3 },
  { name: '生菜', emoji: '🥬', type: 'vegetable', flavor: 2 },
  { name: '牛排', emoji: '🥩', type: 'meat', flavor: 10 },
  { name: '冰淇淋', emoji: '🍦', type: 'dessert', flavor: 9 },
];

// 玩家选择的菜谱（原料名称列表）
const recipe = ['番茄', '奶酪', '面包', '牛排'];
console.log(`📜 玩家的神秘菜谱: ${recipe.join(' + ')}`);
console.log("---");

// 第1步: 筛选出菜谱中包含的原料对象 (使用 filter 和 includes)
const selectedIngredients = ingredients.filter(ingredient => recipe.includes(ingredient.name));
console.log("✅ 已选出的原料对象:", selectedIngredients);
console.log("---");

// 第2步: 将选出的原料“摆盘”，只提取它们的表情符号 (使用 map)
const dishEmojis = selectedIngredients.map(ingredient => ingredient.emoji);
console.log(`🍽️ 正在摆盘... 盘子里现在有: ${dishEmojis.join(' ')}`);
console.log("---");

// 第3步: 计算这道菜的总“风味值” (使用 reduce)
const totalFlavor = selectedIngredients.reduce((sum, ingredient) => {
  return sum + ingredient.flavor;
}, 0);
console.log(`😋 正在品尝... 这道菜的风味值为: ${totalFlavor}`);
console.log("---");

// 最后，根据风味值给出一个有趣的评价
let finalDish;
if (totalFlavor > 20) {
  finalDish = `[${dishEmojis.join('')}] = 🍕 神级美味！`;
} else if (totalFlavor > 10) {
  finalDish = `[${dishEmojis.join('')}] = 🍔 相当不错！`;
} else {
  finalDish = `[${dishEmojis.join('')}] = 🥪 嗯...还行吧。`;
}

console.log("🎉 铛铛铛！你的表情符号料理完成了！");
console.log(finalDish);

// 链式操作一步到位！
const finalDishChained = ingredients
    .filter(i => recipe.includes(i.name)) // 筛选
    .map(i => i.emoji) // 转换
    .join(''); // 组合成字符串

console.log(`\n🚀 链式操作也能快速上菜: [${finalDishChained}]`);
```

### 💡 记忆要点
- **`map` -> 转换器**: 对每个元素进行“一对一”的加工，返回一个长度**相同**的新数组。
- **`filter` -> 过滤器**: 根据条件“筛选”元素，返回一个只包含合格成员的新数组（长度可能**变短**）。
- **`reduce` -> 汇总器**: 将所有元素“浓缩”成一个**单一的值**（如总和、平均值或一个新对象）。

<!--
metadata:
  syntax: [arrow-function]
  pattern: [method-chaining, functional-programming]
  api: [Array.map, Array.filter, Array.reduce, console.log, Array.includes, Array.join]
  concept: [immutability, callback-function]
  difficulty: intermediate
  dependencies: [js-sec-2-1-1, js-sec-1-4-3]
  related: [js-sec-2-1-5]
-->