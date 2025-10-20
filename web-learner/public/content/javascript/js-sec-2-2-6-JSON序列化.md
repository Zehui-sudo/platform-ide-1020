## JSON序列化

### 🎯 核心概念
JSON序列化是将JavaScript对象或值转换为JSON（JavaScript Object Notation）格式的字符串的过程，以便于存储、传输或在不同系统间交换数据。

### 📚 Level 1: 基础认知（30秒理解）
想象一下，你想把你的游戏角色信息（一个JavaScript对象）保存成一个文本文件。你不能直接保存对象，但可以把它转换成一个字符串。`JSON.stringify()` 就是做这个的魔法棒！

```javascript
// 你的游戏角色信息
const player = {
  name: "Link",
  level: 5,
  hasSword: true
};

// 使用 JSON.stringify() 将对象转换为字符串
const playerString = JSON.stringify(player);

console.log("JavaScript 对象:", player);
console.log("转换后的 JSON 字符串:", playerString);
console.log("字符串的类型是:", typeof playerString);
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 自动忽略“无法传输”的值
`JSON.stringify()` 在转换时，会自动跳过一些它不认识或不适合转换的特殊值，比如函数、`undefined` 和 `Symbol`。

```javascript
const wizard = {
  name: "Gandalf",
  level: 99,
  power: undefined, // undefined 会被忽略
  castSpell: function() { // 函数会被忽略
    return "You shall not pass!";
  },
  secretSymbol: Symbol('Istari') // Symbol 会被忽略
};

// 数组中的特殊值会被转换为 null
const inventory = ["mana potion", undefined, function() {}];

const wizardString = JSON.stringify(wizard);
const inventoryString = JSON.stringify(inventory);

console.log("序列化前的巫师对象:", wizard);
console.log("序列化后的巫师字符串:", wizardString); // 注意 power, castSpell, secretSymbol 都消失了

console.log("--- 分割线 ---");

console.log("序列化前的库存数组:", inventory);
console.log("序列化后的库存字符串:", inventoryString); // 注意 undefined 和函数变成了 null
```

#### 特性2: 格式化输出（让JSON更易读）
`JSON.stringify()` 的第三个参数可以控制输出字符串的缩进，让复杂的JSON数据变得像诗一样整洁。

```javascript
const dragon = {
  name: "Smaug",
  type: "Fire Drake",
  treasures: [
    { name: "Arkenstone", value: 1000000 },
    { name: "Gold Coins", quantity: 500000 }
  ],
  isAwake: true
};

// 不加格式化参数
const compactJson = JSON.stringify(dragon);
console.log("紧凑的JSON字符串:");
console.log(compactJson);

console.log("\n--- 使用2个空格缩进 ---");
// 第三个参数是数字，表示用多少个空格缩进
const prettyJson = JSON.stringify(dragon, null, 2);
console.log(prettyJson);

console.log("\n--- 使用字符串作为缩进 ---");
// 也可以用字符串（比如制表符 \t 或者其他符号）
const fancyJson = JSON.stringify(dragon, null, '🐉 ');
console.log(fancyJson);
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个常见的陷阱是序列化包含“循环引用”的对象，这会导致无限循环，最终抛出错误。

```javascript
// 完整的对比示例，包含所有必要的变量定义
console.log("=== 错误用法 ===");
// ❌ 两个对象互相引用，形成了死循环
const personA = { name: "Alice" };
const personB = { name: "Bob" };

personA.friend = personB;
personB.friend = personA; // 这里创建了循环引用

try {
  JSON.stringify(personA);
} catch (error) {
  console.error("出错了！JSON无法处理循环引用:", error.message);
  console.log("解释: 当 stringify 试图转换 personA 时，它遇到了 friend (personB)。然后它去转换 personB，又遇到了 friend (personA)，如此无限循环，直到栈溢出。");
}


console.log("\n=== 正确用法 ===");
// ✅ 在序列化之前，创建一个“干净”的不包含循环引用的版本
const characterA = { name: "Frodo", id: 1 };
const characterB = { name: "Sam", id: 2 };

// 我们不直接引用整个对象，而是引用其唯一标识符
const cleanCharacterA = {
  name: characterA.name,
  friendId: characterB.id // 只保存朋友的ID，而不是整个对象
};

const characterString = JSON.stringify(cleanCharacterA);
console.log("序列化成功:", characterString);
console.log("解释: 通过只存储ID，我们打破了循环引用。在需要时，我们可以根据这个ID再找到完整的朋友对象。");
```

### 🚀 Level 4: 实战应用（真实场景）
**场景：🐾 虚拟宠物养成游戏存档**

你正在开发一个简单的网页版虚拟宠物游戏。当玩家关闭浏览器时，你需要将宠物的当前状态保存下来，以便下次能恢复。JSON序列化是实现这个“游戏存档”功能的完美工具！

```javascript
// 这是一个代表你虚拟宠物的对象
const myPet = {
  name: "Pikachu",
  type: "Electric Mouse",
  happiness: 80,
  hunger: 40,
  lastPlayed: new Date(), // Date对象在序列化时会变成ISO格式字符串
  // 宠物有一个行为，但我们不希望保存这个行为到存档里
  play: function() {
    this.happiness += 10;
    console.log(`${this.name} is happy! Happiness is now ${this.happiness}.`);
  }
};

console.log("🎮 游戏开始！这是你的宠物：", myPet);
myPet.play(); // 玩了一会儿，宠物心情变好了

console.log("\n🌙 准备睡觉了，需要保存游戏进度...");

// 使用 JSON.stringify 创建游戏存档
// 使用 2 个空格美化存档文件，方便调试查看
const saveFile = JSON.stringify(myPet, null, 2);

console.log("\n💾 游戏存档已生成 (一个JSON字符串):");
console.log(saveFile);
console.log("\n✨ 你看！'play' 函数被自动忽略了，'lastPlayed' 日期变成了标准的字符串格式。");
console.log("这个字符串现在可以轻松地发送到服务器或保存在浏览器的 localStorage 中了！");
```

### 💡 记忆要点
- **要点1**：`JSON.stringify()` 是将JavaScript值（对象、数组等）转换成JSON字符串的“魔法棒”。
- **要点2**：它会自动忽略函数、`undefined`和`Symbol`，并能将`Date`对象转换为ISO 8601格式的字符串。
- **要点3**：小心循环引用！它会导致程序抛出`TypeError`，需要创建不含循环引用的新对象来解决。

<!--
metadata:
  syntax: [function]
  pattern: [data-serialization]
  api: [JSON.stringify, console.log, Date, Symbol]
  concept: [json, serialization, data-interchange, circular-reference]
  difficulty: basic
  dependencies: [无]
  related: [js-sec-2-2-7]
-->