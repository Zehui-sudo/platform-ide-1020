## 对象创建与属性访问

### 🎯 核心概念
JavaScript对象是一种复合数据类型，它允许你将多个相关的"键-值"对（称为属性）存储在一个集合中，用来模拟现实世界中的事物或构建复杂的数据结构。

### 📚 Level 1: 基础认知（30秒理解）
对象就像一个现实生活中的实体。比如，一只猫有名字、年龄和颜色。在JavaScript中，我们可以用一个对象来表示这只猫。

```javascript
// 创建一个表示宠物的对象
const myPet = {
  name: "咪咪",
  age: 2,
  color: "橘色"
};

// 使用 "点表示法" (dot notation) 访问对象的属性
console.log("我的宠物叫什么名字？", myPet.name);
console.log("它多大了？", myPet.age);
console.log("它是什么颜色的？", myPet.color);
```

### 📈 Level 2: 核心特性（深入理解）
深入了解两种访问属性的方式以及如何动态地修改对象。

#### 特性1: 两种属性访问方式：点表示法 vs. 方括号表示法
点表示法（`.`）更简洁，但方括号表示法（`[]`）更灵活，特别是当属性名包含特殊字符或来自变量时。

```javascript
const character = {
  name: "艾拉",
  "class-type": "法师", // 属性名包含特殊字符'-'
  level: 10
};

// 1. 使用点表示法访问常规属性
console.log("角色名称:", character.name);

// 2. 使用方括号表示法访问包含特殊字符的属性
//    注意：属性名需要用引号包裹，像一个字符串
console.log("角色职业:", character["class-type"]);

// 3. 使用方括号表示法通过变量动态访问属性
const propToAccess = "level";
console.log("角色等级:", character[propToAccess]);
```

#### 特性2: 动态添加与修改属性
JavaScript对象是动态的，你可以在创建后随时添加新属性或修改现有属性的值。

```javascript
// 创建一个无人机对象
const drone = {
  id: "X-001",
  status: "待命"
};

console.log("初始状态:", drone.status);

// 修改现有属性的值
drone.status = "正在飞行";
console.log("更新后状态:", drone.status);

// 添加一个全新的属性
drone.batteryLevel = "87%";
console.log("新增电池信息:", drone.batteryLevel);

console.log("无人机最终信息:", drone);
```

### 🔍 Level 3: 对比学习（避免陷阱）
访问一个不存在的属性是初学者常犯的错误，它不会报错，但会返回 `undefined`，这可能导致后续代码出现问题。

```javascript
const player = {
  username: "CoolGamer123",
  score: 9500
};

console.log("=== 错误用法 ===");
// ❌ 尝试访问一个不存在的属性 `rank`
const playerRank = player.rank;
console.log("玩家等级:", playerRank); // 输出 undefined
// 解释: `player` 对象上没有 `rank` 这个属性，所以返回 `undefined`。
// 如果后续代码依赖 `playerRank` 做计算，比如 playerRank.toUpperCase()，就会立即报错。

console.log("=== 正确用法 ===");
// ✅ 在访问前，先检查属性是否存在
if (player.rank) {
  console.log("玩家等级:", player.rank);
} else {
  console.log("该玩家还没有等级信息。");
}
// 解释: 通过条件判断，我们可以安全地处理属性可能不存在的情况，避免程序因 `undefined` 值而出错。
```

### 🚀 Level 4: 实战应用（真实场景）
**场景：🎮 奇幻冒险游戏 - 角色升级与装备系统**

在这个场景中，我们将创建一个代表游戏英雄的对象。当英雄找到一件新装备时，我们会更新他的属性，并为他添加新的技能。

```javascript
// 1. 创建我们的英雄角色
const hero = {
  name: "阿尔文",
  level: 5,
  hp: 100,
  attack: 15,
  inventory: ["治疗药水", "地图"],
  skills: {
    "普通攻击": "挥剑斩击"
  }
};

console.log(`🌟 冒险开始！英雄 ${hero.name} 踏上了征程！`);
console.log("初始攻击力:", hero.attack);
console.log("当前物品:", hero.inventory);

// 2. 英雄在森林里发现了一把“精灵之刃”！
const newItem = "精灵之刃";
const attackBonus = 10;
const newSkillName = "风之切割"; // 技能名包含中文，最好用方括号

console.log(`\n🎉 哇！${hero.name} 找到了传说中的【${newItem}】！`);

// 3. 更新英雄的属性和物品
// 增加攻击力
hero.attack = hero.attack + attackBonus;
// 将新物品添加到背包
hero.inventory.push(newItem);
// 使用方括号表示法学习一个新技能
hero.skills[newSkillName] = "召唤一阵锋利的风刃攻击敌人";

// 4. 展示英雄升级后的状态
console.log("\n--- 英雄状态更新 ---");
console.log(`💪 攻击力提升至: ${hero.attack} (原 ${hero.attack - attackBonus} + ${attackBonus} 加成)`);
console.log(`🎒 背包更新: ${hero.inventory.join(", ")}`);
console.log(`📖 新学会的技能【${newSkillName}】: ${hero.skills[newSkillName]}`);
console.log("--- 冒险继续！ ---");
```

### 💡 记忆要点
- **要点1**：使用花括号 `{}` 创建对象，属性以 `键: 值` 的形式成对出现。
- **要点2**：使用点表示法 (`.`) 访问简单属性，使用方括号表示法 (`[]`) 访问带特殊字符或由变量决定的属性。
- **要点3**：JavaScript对象是动态的，可以随时添加、修改或删除属性，非常灵活。

<!--
metadata:
  syntax: let, const
  pattern: object-literal
  api: console.log, Array.push, String.join
  concept: object, property-access, dynamic-properties
  difficulty: basic
  dependencies: [无]
  related: [js-sec-2-2-2]
-->