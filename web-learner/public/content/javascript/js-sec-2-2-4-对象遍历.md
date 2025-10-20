## 对象遍历

### 🎯 核心概念
对象遍历让我们能够逐一访问并操作一个对象中的所有“键-值”对，这是读取、处理或转换对象数据的基本操作。

### 📚 Level 1: 基础认知（30秒理解）
最常见的对象遍历方式是使用 `for...in` 循环，它会遍历对象的所有可枚举属性（键）。

```javascript
// 创建一个表示宠物的对象
const myPet = {
  name: "旺财",
  type: "狗狗",
  age: 3
};

console.log("开始介绍我的宠物：");

// 使用 for...in 循环遍历对象的每个属性
for (const key in myPet) {
  // key 是属性名 (如 "name", "type", "age")
  // myPet[key] 是对应的属性值 (如 "旺财", "狗狗", 3)
  console.log(`- ${key}: ${myPet[key]}`);
}
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: `for...in` 会遍历原型链
`for...in` 循环不仅会遍历对象自身的属性，还会遍历其原型链上可枚举的属性。为了避免这种情况，我们通常使用 `hasOwnProperty()` 方法来检查属性是否是对象自身的。

```javascript
// 创建一个“父类”构造函数
function Animal(sound) {
  this.sound = sound;
}

// 在 Animal 的原型上添加一个方法
Animal.prototype.makeSound = function() {
  console.log(this.sound);
};

// 创建一个“子类”实例
const dog = new Animal("汪汪汪");
dog.name = "旺财";
dog.age = 3;

console.log("--- 未使用 hasOwnProperty ---");
// 这个循环会打印出 name, age, sound, 甚至 makeSound
for (const key in dog) {
  console.log(`属性: ${key}`);
}

console.log("\n--- 使用 hasOwnProperty 过滤 ---");
// 这个循环只打印 dog 对象自身的属性
for (const key in dog) {
  if (dog.hasOwnProperty(key)) {
    console.log(`自有属性: ${key}`);
  }
}
```

#### 特性2: 更现代的遍历方法
ES6+ 提供了更直接、更安全的方法来获取对象的键、值或键值对，它们返回一个数组，然后可以配合数组方法（如 `forEach`）使用，并且它们不会遍历原型链。

- `Object.keys(obj)`: 返回一个包含对象自身所有可枚举属性名的数组。
- `Object.values(obj)`: 返回一个包含对象自身所有可枚举属性值的数组。
- `Object.entries(obj)`: 返回一个包含对象自身所有可枚举属性 `[键, 值]` 对的数组。

```javascript
const characterStats = {
  hp: 100,
  mp: 50,
  attack: 15,
  defense: 8
};

// 1. 只遍历键 (Keys)
console.log("--- Object.keys() ---");
const statKeys = Object.keys(characterStats);
statKeys.forEach(key => {
  console.log(`统计项: ${key}`);
});

// 2. 只遍历值 (Values)
console.log("\n--- Object.values() ---");
const statValues = Object.values(characterStats);
statValues.forEach(value => {
  console.log(`数值: ${value}`);
});

// 3. 同时遍历键和值 (Entries)
console.log("\n--- Object.entries() ---");
const statEntries = Object.entries(characterStats);
statEntries.forEach(([key, value]) => {
  console.log(`属性 ${key} 的值为 ${value}`);
});
```

### 🔍 Level 3: 对比学习（避免陷阱）
不正确地使用 `for...in` 是一个常见错误，尤其是在处理可能被扩展了原生 `Object.prototype` 的复杂代码库时。

```javascript
// 假设在某个库或者旧代码中，有人不小心污染了 Object 的原型
Object.prototype.isLegacy = true;

const userProfile = {
  username: "Alice",
  level: 99
};

console.log("=== 错误用法 ===");
// ❌ 直接使用 for...in，没有检查 hasOwnProperty
// 这会把原型链上的 'isLegacy' 也当作 userProfile 的属性打印出来，导致意外行为。
for (const key in userProfile) {
  console.log(`${key}: ${userProfile[key]}`);
}
console.log("错误原因：遍历到了不属于对象自身的、来自原型链的属性 'isLegacy'。");


console.log("\n=== 正确用法 ===");
// ✅ 使用 Object.keys() 配合 forEach，这是最推荐的现代做法
// 它只会遍历对象自身的属性，完全不受原型链污染的影响。
Object.keys(userProfile).forEach(key => {
  console.log(`${key}: ${userProfile[key]}`);
});
console.log("正确原因：Object.keys() 明确只获取对象自身的键，更安全、可预测。");

// 清理原型污染，以免影响其他示例
delete Object.prototype.isLegacy;
```

### 🚀 Level 4: 实战应用（真实场景）

#### 🎮 游戏场景：生成你的专属冒险者角色卡！

在这个场景中，我们将创建一个函数，它接收一个包含角色信息的对象，然后遍历这个对象，生成一张生动、格式化的角色卡片，并根据属性类型添加不同的表情符号，让它看起来像一个真正的游戏角色面板。

```javascript
function createCharacterSheet(character) {
  console.log("================================");
  console.log("⚔️  你的冒险者角色卡  ⚔️");
  console.log("================================");

  const iconMapping = {
    name: "👤",
    class: "🛡️",
    level: "🌟",
    hp: "❤️",
    mp: "💧",
    inventory: "🎒",
    gold: "💰"
  };

  // 使用 Object.entries() 是最优雅的方式，可以同时拿到 key 和 value
  for (const [key, value] of Object.entries(character)) {
    // 根据 key 获取对应的 icon，如果没有就用一个默认的
    const icon = iconMapping[key] || "🔹";

    let displayValue;

    // 如果值是数组（比如 inventory），我们把它格式化成一个漂亮的列表
    if (Array.isArray(value)) {
      displayValue = value.join(", ");
    } else {
      displayValue = value;
    }

    // 将 key 的首字母大写，让输出更美观
    const formattedKey = key.charAt(0).toUpperCase() + key.slice(1);

    console.log(`${icon} ${formattedKey}: ${displayValue}`);
  }

  console.log("================================");
  console.log("旅途愉快，勇敢的冒险者！");
}

// 定义你的角色信息
const myHero = {
  name: "闪电侠客",
  class: "游侠",
  level: 12,
  hp: 150,
  mp: 80,
  inventory: ["长弓", "治疗药水", "地图"],
  gold: 250
};

// 调用函数，生成角色卡！
createCharacterSheet(myHero);
```

### 💡 记忆要点
- **要点1**：`for...in` 循环会遍历对象自身及其原型链上的所有可枚举属性。
- **要点2**：在 `for...in` 循环中，始终使用 `hasOwnProperty()` 来确保你只处理对象自身的属性。
- **要点3**：优先使用 `Object.keys()`, `Object.values()`, 或 `Object.entries()`，它们更现代、更安全，并且不会遍历原型链。

<!--
metadata:
  syntax: ["for-in", "function"]
  pattern: ["iteration"]
  api: ["Object.keys", "Object.values", "Object.entries", "Array.forEach", "console.log", "Object.hasOwnProperty"]
  concept: ["object-properties", "prototype-chain", "enumerable-properties"]
  difficulty: intermediate
  dependencies: ["无"]
  related: ["js-sec-2-2-1", "js-sec-2-2-5"]
-->