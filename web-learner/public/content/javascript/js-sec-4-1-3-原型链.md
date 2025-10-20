## 原型链

### 🎯 核心概念
原型链是JavaScript实现继承的核心机制，它允许一个对象访问并使用另一个对象的属性和方法，形成一个属性查找的链条。

### 📚 Level 1: 基础认知（30秒理解）
每个JavaScript对象都有一个隐藏的内部属性 `[[Prototype]]`（可以通过 `Object.getPrototypeOf()` 访问）。当你试图访问一个对象的属性时，如果对象本身没有这个属性，JavaScript引擎就会沿着这个 `[[Prototype]]` 链接去它的“原型对象”上查找，这就是最简单的原型链。

```javascript
// 定义一个构造函数，它有一个原型方法
function Dog(name) {
  this.name = name;
}

// 在Dog的原型上添加一个方法
Dog.prototype.bark = function() {
  return "Woof woof!";
};

// 创建一个Dog实例
const myDog = new Dog("Buddy");

// myDog本身没有bark方法，但它能通过原型链找到并使用它
console.log(`小狗 ${myDog.name} 在叫: ${myDog.bark()}`);
console.log("myDog自身有'bark'方法吗?", myDog.hasOwnProperty('bark')); // false
console.log("myDog的原型有'bark'方法吗?", Dog.prototype.hasOwnProperty('bark')); // true
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 链式查找（Chained Lookup）
当访问一个对象的属性时，JavaScript会沿着原型链向上查找，直到找到该属性或到达链的末端（`null`）为止。这个链可以有多层。

```javascript
// 祖先：生物
function Creature() {}
// 在原型上定义共享属性和方法
Creature.prototype.isAlive = true;
Creature.prototype.breathe = function() {
  return "Breathing...";
};

// 父类：动物
function Animal() {}
// 将Animal的原型链接到Creature的原型
Animal.prototype = Object.create(Creature.prototype);
Animal.prototype.hasLegs = true;

// 子类：猫
function Cat(name) {
  this.name = name;
}
// 将Cat的原型链接到Animal的原型
Cat.prototype = Object.create(Animal.prototype);
Cat.prototype.meow = function() {
  return "Meow!";
};

const myCat = new Cat("Mimi");

// 访问自己的属性
console.log(`我的猫叫: ${myCat.name}`);
// 访问原型链上的方法 (Cat.prototype)
console.log(`它在叫: ${myCat.meow()}`);
// 访问原型链上更远的方法 (Creature.prototype)
console.log(`它在呼吸吗? ${myCat.breathe()}`);
// 访问原型链上的属性 (Creature.prototype)
console.log(`它还活着吗? ${myCat.isAlive}`);
```

#### 特性2: 属性屏蔽（Property Shadowing）
如果实例对象自身定义了与原型链上同名的属性或方法，那么访问时会优先使用实例自身的，这称为“属性屏蔽”。

```javascript
function Hero(name) {
  this.name = name;
}

// 英雄原型上有一个通用的攻击方法
Hero.prototype.attack = function() {
  return `${this.name} 使用了普通攻击!`;
};

// 创建一个普通英雄
const genericHero = new Hero("路人甲");
console.log(genericHero.attack()); // 输出: 路人甲 使用了普通攻击!

// 创建一个特殊的英雄，并给他一个自己的、更强的攻击方法
const superHero = new Hero("超人");
superHero.attack = function() {
  return `${this.name} 使用了【激光眼】! 伤害+999!`;
};

// superHero的attack方法“屏蔽”了原型上的attack方法
console.log(superHero.attack()); // 输出: 超人 使用了【激光眼】! 伤害+999!

// 删除实例上的方法后，原型上的方法又可见了
delete superHero.attack;
console.log(superHero.attack()); // 输出: 超人 使用了普通攻击!
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个常见的严重错误是直接修改所有对象的顶级原型 `Object.prototype`。这会污染全局，导致意外的行为。

```javascript
console.log("=== 错误用法 ===");
// ❌ 错误：直接给 Object.prototype 添加方法
// 这会导致所有对象（包括数组、普通对象等）都拥有这个方法，可能与库或代码中的其他部分冲突。
Object.prototype.sayHi = function() {
  console.log("Hi from global prototype!");
};

const myObject = {};
myObject.sayHi(); // 输出: Hi from global prototype!

const myArray = [];
myArray.sayHi(); // 数组也受到了污染! 输出: Hi from global prototype!

// 更糟糕的是，它会干扰 for...in 循环
for (let key in myObject) {
  console.log(`发现属性: ${key}`); // 输出: 发现属性: sayHi，这不是我们想要的！
}
// 清理污染，以免影响后续示例
delete Object.prototype.sayHi;


console.log("\n=== 正确用法 ===");
// ✅ 正确：通过创建自定义构造函数或类来扩展功能
function Greeter(greeting) {
    this.greeting = greeting;
}

Greeter.prototype.sayHi = function() {
    console.log(`${this.greeting}, I am a proper instance!`);
};

const myGreeter = new Greeter("Hello");
myGreeter.sayHi(); // 输出: Hello, I am a proper instance!

const anotherObject = {};
// anotherObject.sayHi(); // 抛出错误: anotherObject.sayHi is not a function，因为它没有被污染
console.log("anotherObject 有 sayHi 方法吗?", typeof anotherObject.sayHi === 'function'); // false
```

### 🚀 Level 4: 实战应用（真实场景）
**🎮 游戏场景：怪兽军团的进化之路**

在这个场景中，我们将创建一个简单的怪兽进化系统。从最基础的“史莱姆”开始，它可以进化成“火焰史莱姆”，再进化成“熔岩史莱姆王”。每一级都会继承上一级的能力，并可能拥有更强或全新的技能。

```javascript
// Level 1: 基础怪兽 - 史莱姆
function Slime(name, hp) {
  this.name = name;
  this.hp = hp;
}

Slime.prototype.attack = function() {
  console.log(`💧 ${this.name} 发起了【撞击】，造成 5 点伤害!`);
};

Slime.prototype.showStatus = function() {
  console.log(`[${this.name}] HP: ${this.hp}`);
};

// Level 2: 进化 - 火焰史莱姆
function FireSlime(name, hp) {
  // 调用父类的构造函数，继承基础属性
  Slime.call(this, name, hp);
  this.element = "火";
}

// 关键一步：建立原型链，让 FireSlime 继承 Slime 的方法
FireSlime.prototype = Object.create(Slime.prototype);
FireSlime.prototype.constructor = FireSlime; // 修复构造函数指向

// "属性屏蔽": 覆盖父类的 attack 方法，使其更强大
FireSlime.prototype.attack = function() {
  console.log(`🔥 ${this.name} 喷射【火焰弹】，造成 15 点伤害!`);
};

// Level 3: 终极进化 - 熔岩史莱姆王
function MagmaSlimeKing(name, hp) {
  FireSlime.call(this, name, hp);
  this.title = "王";
}

MagmaSlimeKing.prototype = Object.create(FireSlime.prototype);
MagmaSlimeKing.prototype.constructor = MagmaSlimeKing;

// 新增终极技能
MagmaSlimeKing.prototype.ultimateAttack = function() {
  console.log(`🌋👑 ${this.name} ${this.title} 释放了【末日熔岩】，全屏燃烧，造成 99 点伤害!`);
};


// --- 开始我们的冒险！---
console.log("一只弱小的史莱姆出现了...");
const basicSlime = new Slime("噗噗", 50);
basicSlime.showStatus();
basicSlime.attack();

console.log("\n史莱姆沐浴在火焰中进化了！");
const fireSlime = new FireSlime("燃燃", 120);
fireSlime.showStatus(); // 继承自Slime
fireSlime.attack();     // 使用自己的attack方法

console.log("\n最终，它成为了熔岩之王！");
const king = new MagmaSlimeKing("暴君", 500);
king.showStatus();      // 继承自Slime
king.attack();          // 继承自FireSlime
king.ultimateAttack();  // 使用自己的终极技能
```

### 💡 记忆要点
- **查找路径**: 当访问一个对象的属性时，JavaScript会先在对象自身查找，找不到则沿着`[[Prototype]]`链向上查找，直至终点`null`。
- **继承方式**: 原型链是JavaScript实现对象间属性和方法共享（即继承）的主要方式。
- **属性屏蔽**: 在实例上定义的同名属性会“屏蔽”或覆盖原型链上层的同名属性。

<!--
metadata:
  syntax: function, constructor
  pattern: inheritance
  api: Object.create, Object.prototype.hasOwnProperty, console.log
  concept: prototype, prototype-chain, inheritance, property-shadowing
  difficulty: advanced
  dependencies: [无]
  related: [js-sec-4-1-2, js-sec-4-1-4]
-->