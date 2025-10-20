## 构造函数

### 🎯 核心概念
构造函数就像一个“对象蓝图”，它允许我们使用相同的结构和行为，快速、重复地创建多个相似的对象实例。

### 📚 Level 1: 基础认知（30秒理解）
想象一下，我们要创建一个游戏角色。使用构造函数，我们可以定义一个“玩家”模板，然后用它来创建具体的玩家。

```javascript
// 定义一个玩家构造函数 (蓝图)
// 按照惯例，构造函数名首字母大写
function Player(name, level) {
  this.name = name;
  this.level = level;
}

// 使用 new 关键字，根据蓝图创建一个具体的玩家对象
const player1 = new Player('勇者爱丽丝', 99);

// 查看我们创建的玩家
console.log('新玩家已创建:', player1);
console.log(`玩家名称: ${player1.name}`);
console.log(`玩家等级: ${player1.level}`);
```

### 📈 Level 2: 核心特性（深入理解）
构造函数有两个核心特性：`new`关键字的背后机制和共享方法的实现。

#### 特性1: `new` 关键字的魔法
当你使用 `new` 关键字时，JavaScript 在背后默默为你做了四件事：
1.  创建一个全新的空对象。
2.  将这个新对象的原型 (`__proto__`) 链接到构造函数的 `prototype` 属性。
3.  将构造函数内部的 `this` 关键字绑定到这个新对象上。
4.  如果构造函数没有显式返回其他对象，那么就自动返回这个新创建的对象。

```javascript
function Monster(name, hp) {
  console.log(`(1) 一个新的怪兽对象正在创建... this 指向它`);
  this.name = name;
  this.hp = hp;
  // (2) 由于没有 return 语句，函数会自动返回 this
  console.log(`(3) 怪兽 ${this.name} 创建完毕!`);
}

// 使用 new 调用构造函数
console.log('--- 开始召唤怪兽 ---');
const slime = new Monster('史莱姆', 50);

// slime 就是构造函数返回的新对象
console.log('--- 召唤成功 ---');
console.log('召唤出的怪兽:', slime);
console.log(`它的名字是 ${slime.name}，生命值是 ${slime.hp}`);
```

#### 特性2: 使用原型（prototype）共享方法
如果每个怪兽都有一个 `attack` 方法，直接在构造函数里定义（`this.attack = ...`）会为每个实例都创建一个新的函数，浪费内存。更好的方法是把共享的方法放在 `prototype` 上。

```javascript
function Robot(model) {
  // 每个机器人实例独有的属性
  this.model = model;
  this.energy = 100;
}

// 将共享的方法定义在原型上
// 所有 Robot 实例都能访问这个 sayHello 方法，但它只在内存中存在一份
Robot.prototype.sayHello = function() {
  console.log(`你好，我是 ${this.model} 型号机器人。`);
};

const robotA = new Robot('T-800');
const robotB = new Robot('R2-D2');

robotA.sayHello();
robotB.sayHello();

// 验证两个实例是否共享同一个方法
console.log('两个机器人是否共享同一个 sayHello 方法?', robotA.sayHello === robotB.sayHello); // 输出 true
```

### 🔍 Level 3: 对比学习（避免陷阱）
忘记 `new` 关键字是使用构造函数时最常见的错误，这会导致意想不到的后果。

```javascript
function Spell(name, type) {
  this.name = name;
  this.type = type;
  console.log(`'this' 在函数内部指向:`, this);
}

console.log("=== ❌ 错误用法: 忘记使用 new ===");
// 如果不使用 new，Spell 就像一个普通函数被调用
// 在非严格模式下，'this' 会指向全局对象 (在浏览器中是 window)
// 这会污染全局作用域！
const fireball = Spell('火球术', '火焰');
console.log('fireball 的值:', fireball); // undefined, 因为函数没有显式 return
// 尝试访问全局变量，你会发现它们被意外创建了
// 在浏览器环境中取消下面一行的注释会看到结果
// console.log('全局变量 name:', window.name); // '火球术'


console.log("\n=== ✅ 正确用法: 使用 new 关键字 ===");
// 使用 new 会创建一个新的对象，并将 'this' 指向它
const iceBlast = new Spell('寒冰箭', '冰霜');
console.log('iceBlast 的值:', iceBlast);
console.log(`创建的法术是: ${iceBlast.name}，属于 ${iceBlast.type} 系。`);
```

### 🚀 Level 4: 实战应用（真实场景）
**场景：🐾 虚拟赛博宠物养成**

让我们创建一个“赛博宠物”构造函数。每个宠物都有自己的名字、类型和状态。我们可以通过方法与它互动，比如喂食和玩耍，这些互动会改变它的能量和快乐值。

```javascript
// 赛博宠物构造函数
function CyberPet(name, type) {
  this.name = name;
  this.type = type; // 例如: '电子狗', '像素猫'
  this.energy = 100; // 能量值
  this.happiness = 100; // 快乐值

  console.log(`✨ 哇！一只叫做 ${this.name} 的 ${this.type} 诞生了！`);
}

// 在原型上添加互动方法
CyberPet.prototype.play = function() {
  if (this.energy >= 20) {
    this.energy -= 20;
    this.happiness += 15;
    console.log(`🎾 你和 ${this.name} 玩了激光笔，它的快乐值上升了！`);
  } else {
    console.log(`💤 ${this.name} 太累了，不想玩...`);
  }
  this.checkStatus();
};

CyberPet.prototype.feed = function() {
  this.energy += 30;
  this.happiness += 5;
  console.log(`🍖 你喂了 ${this.name} 一块能量方块，它的能量恢复了！`);
  this.checkStatus();
};

CyberPet.prototype.checkStatus = function() {
  console.log(
    `--- ${this.name} 的状态 --- 能量: ${this.energy}, 快乐: ${this.happiness} ---`
  );
};

// --- 开始游戏 ---
// 领养一只宠物
const myPet = new CyberPet('比特', '电子狗');
myPet.checkStatus();

// 和它互动
console.log('\n--- 一天过去了 ---');
myPet.play();
myPet.play();
myPet.feed();
myPet.play();
myPet.play();
myPet.play(); // 能量不足
```

### 💡 记忆要点
-   **首字母大写**：构造函数的名称通常以大写字母开头，这是一个广泛遵守的约定。
-   **`new`是关键**：必须使用 `new` 关键字来创建实例，否则 `this` 的指向会出错。
-   **`this`指代实例**：在构造函数内部，`this` 关键字指向正在被创建的新对象实例。

<!--
metadata:
  syntax: ["function", "constructor"]
  pattern: ["object-creation"]
  api: ["console.log"]
  concept: ["this-binding", "prototype", "instance"]
  difficulty: intermediate
  dependencies: ["无"]
  related: ["js-sec-4-1-2"]
-->