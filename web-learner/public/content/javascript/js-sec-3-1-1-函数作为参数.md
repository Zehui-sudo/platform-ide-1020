## 函数作为参数

### 🎯 核心概念
在 JavaScript 中，函数是“一等公民”，可以像变量一样被传来传去。将一个函数作为参数传递给另一个函数，可以让我们的代码更加灵活和可复用，实现强大的“回调”模式，即“你先忙，忙完了再调用我给你的这个函数”。

### 📚 Level 1: 基础认知（30秒理解）
想象一下，你有一个通用的“打招呼”机器（`greet`函数），但你希望它能用不同的语言说“你好”。你可以把具体的“说话”方式（一个函数）作为参数传给它。

```javascript
// 定义一个说“你好”的函数
function sayHello() {
  console.log("Hello!");
}

// 定义一个说“Hola”的函数
function sayHola() {
  console.log("Hola!");
}

// 这个函数接收另一个函数作为参数，并执行它
function greet(howToSayHi) {
  console.log("准备打招呼...");
  // 在这里调用传入的函数
  howToSayHi();
  console.log("打招呼完毕！");
}

// 将 sayHello 函数作为参数传递给 greet 函数
greet(sayHello);

console.log("---");

// 将 sayHola 函数作为参数传递给 greet 函数
greet(sayHola);
```

### 📈 Level 2: 核心特性（深入理解）
深入了解函数作为参数的两种常见用法。

#### 特性1: 回调函数（Callbacks）
当一个函数（如 `fetchData`）需要时间来完成任务时，我们可以传递一个“回调函数”作为参数。这个回调函数会在主任务完成后被调用，专门用来处理结果。这在异步操作中非常常见。

```javascript
// 模拟一个从服务器获取数据的函数，它需要一些时间
function fetchData(callback) {
  console.log("正在从火星服务器获取用户数据...");
  
  // 使用 setTimeout 模拟网络延迟
  setTimeout(function() {
    const userData = { name: "星际探险家", level: 99 };
    console.log("数据获取成功！");
    // 数据准备好后，调用传入的 callback 函数，并把数据传给它
    callback(userData);
  }, 1500); // 模拟1.5秒的延迟
}

// 定义一个回调函数，用来处理获取到的数据
function displayUserData(user) {
  console.log(`--- 用户信息面板 ---`);
  console.log(`姓名: ${user.name}`);
  console.log(`等级: ${user.level}`);
  console.log(`--------------------`);
}

// 调用 fetchData，并把 displayUserData 作为回调函数传进去
fetchData(displayUserData);
```

#### 特性2: 匿名函数与箭头函数
我们不必总是预先定义一个有名字的函数再传入。可以直接在参数位置定义一个“一次性”的匿名函数或更简洁的箭头函数，让代码更紧凑。

```javascript
// 一个通用的计算器函数，它接受两个数字和一个操作函数
function calculator(a, b, operation) {
  console.log(`准备用特殊方式计算 ${a} 和 ${b}...`);
  const result = operation(a, b);
  console.log(`计算结果是: ${result}`);
}

// 1. 使用匿名函数作为参数
calculator(10, 5, function(x, y) {
  return x * y; // 定义乘法操作
});

console.log("---");

// 2. 使用更简洁的箭头函数作为参数
calculator(10, 5, (x, y) => {
  return x - y; // 定义减法操作
});
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个非常常见的错误是：在传递函数时，不小心把它调用了。你需要传递的是函数本身（像一个菜谱），而不是函数调用的结果（做好的菜）。

```javascript
// 准备一个简单的函数
function announce() {
  return "这是一个重要的通知！";
}

// 一个接收通知函数的“广播站”
function broadcast(notificationFunction) {
  console.log("📢 广播站准备播报：");
  // 正确的做法是在这里调用函数
  const message = notificationFunction();
  console.log(message);
}


console.log("=== 错误用法 ❌ ===");
// 错误：我们传递了 announce() 的 *返回值* ("这是一个重要的通知！")，而不是函数本身。
// broadcast 函数期望得到一个函数，但却得到了一个字符串，所以它在尝试调用字符串时会报错。
try {
  broadcast(announce()); // 错误！这里是 announce() 而不是 announce
} catch (e) {
  console.error("出错了！", e.message);
  console.log("原因：你把一个字符串传给了 broadcast，它没法像函数一样被调用 (notificationFunction is not a function)。");
}


console.log("\n=== 正确用法 ✅ ===");
// 正确：我们传递了 announce 函数的 *引用*（函数本身）。
// broadcast 函数内部可以随时调用它。
broadcast(announce); // 正确！传递的是函数本身
```

### 🚀 Level 4: 实战应用（真实场景）
**🎮 游戏场景：角色技能释放器**

我们来创建一个简单的角色扮演游戏（RPG）的技能系统。有一个核心的 `useSkill` 函数，它负责处理释放技能前的准备工作（比如检查法力值）。具体释放哪个技能，则通过传递不同的“技能函数”作为参数来决定。

```javascript
// 角色状态
const player = {
  name: "闪电法师",
  mana: 100, // 法力值
};

// --- 技能库 ---
function castFireball(target) {
  console.log(`🔥 对 ${target} 施放了【火球术】！造成 50 点伤害！`);
}
// 为函数对象附加一个属性来存储消耗值
castFireball.manaCost = 30;

function castIceShield(target) {
  console.log(`❄️ 为 ${target} 施加了【冰霜护盾】！提升了防御力！`);
}
castIceShield.manaCost = 20;

function summonGolem(target) {
  console.log(`🗿 在 ${target} 面前召唤了【岩石傀儡】！它会为你战斗！`);
}
summonGolem.manaCost = 70;

/**
 * 通用的技能释放器
 * @param {object} character - 释放技能的角色
 * @param {string} target - 技能目标
 * @param {function} skillFunction - 要释放的技能函数
 */
function useSkill(character, target, skillFunction) {
  console.log(`\n--- ${character.name} 的回合 ---
`);
  
  // 从技能函数的属性中获取法力消耗
  const manaCost = skillFunction.manaCost || 0;

  console.log(`准备释放技能... 当前法力: ${character.mana}, 技能消耗: ${manaCost}`);
  
  if (character.mana >= manaCost) {
    skillFunction(target); // 真正释放技能
    character.mana -= manaCost;
    console.log(`技能释放成功！剩余法力: ${character.mana}`);
  } else {
    console.log(`法力不足！无法释放技能。`);
  }
  console.log(`------------------------`);
}

// 让我们开始战斗！
// 1. 闪电法师对巨龙使用火球术
useSkill(player, "巨龙", castFireball);

// 2. 闪电法师为自己施加冰霜护盾
useSkill(player, "自己", castIceShield);

// 3. 闪电法师尝试召唤傀儡，但法力可能不够了
useSkill(player, "战场中央", summonGolem);

// 4. 再次尝试释放火球术
useSkill(player, "巨龙", castFireball);
```

### 💡 记忆要点
- **要点1**：函数可以像变量一样被传递，这被称为“一等公民函数”。
- **要点2**：传递的是函数本身（引用），而不是函数调用的结果。记住是 `myFunction` 而不是 `myFunction()`。
- **要点3**：这种模式常用于回调函数（处理异步结果）和创建可配置、可复用的代码（如数组的 `map`, `filter` 方法）。

<!--
metadata:
  syntax: [function, arrow-function]
  pattern: [callback, higher-order-function]
  api: [console.log, setTimeout]
  concept: [first-class-functions, callback]
  difficulty: intermediate
  dependencies: [js-sec-1-4-1]
  related: [js-sec-3-1-2, js-sec-3-2-1]
-->