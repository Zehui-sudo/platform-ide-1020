## super关键字

### 🎯 核心概念
`super` 关键字用于在子类中调用父类的构造函数或方法，是实现类继承（Inheritance）的关键一环，让你能复用和扩展父类的功能。

### 📚 Level 1: 基础认知（30秒理解）
`super`最常见的用法是在子类的构造函数中调用父类的构造函数，从而完成对父类属性的初始化。

```javascript
// Level 1: 基础认知
// 父类：动物
class Animal {
  constructor(name) {
    this.name = name;
  }
}

// 子类：狗，继承自动物
class Dog extends Animal {
  constructor(name, breed) {
    // 使用 super(name) 调用父类 Animal 的构造函数
    // 必须先调用 super() 才能使用 this
    super(name); 
    this.breed = breed;
  }
}

const myDog = new Dog('旺财', '哈士奇');
console.log(`我的小狗叫 ${myDog.name}，它是一只${myDog.breed}。`);
// 输出: 我的小狗叫 旺财，它是一只哈士奇。
```

### 📈 Level 2: 核心特性（深入理解）
`super`不仅可以调用父类的构造函数，还可以调用父类的普通方法。

#### 特性1: 在构造函数中调用父类构造函数
在子类的`constructor`中，必须在使用`this`关键字之前调用`super()`。这是因为子类实例的`this`对象是由父类构造函数创建和初始化的。

```javascript
// Level 2, 特性1: 在构造函数中调用父类构造函数
class Vehicle {
  constructor(wheels) {
    this.wheels = wheels;
    console.log(`一辆有 ${this.wheels} 个轮子的交通工具被制造出来了。`);
  }
}

class Car extends Vehicle {
  constructor(color) {
    // 调用父类的构造函数，并传递参数 4
    super(4); 
    // 在 super() 被调用后，我们才能安全地使用 'this'
    this.color = color;
    console.log(`这是一辆${this.color}的汽车，它有 ${this.wheels} 个轮子。`);
  }
}

const myCar = new Car('红色');
// 输出:
// 一辆有 4 个轮子的交通工具被制造出来了。
// 这是一辆红色的汽车，它有 4 个轮子。
```

#### 特性2: 调用父类的普通方法
当子类重写（override）了父类的方法时，如果还想执行父类中原始的方法逻辑，就可以使用`super.methodName()`来调用。

```javascript
// Level 2, 特性2: 调用父类的普通方法
class Person {
  constructor(name) {
    this.name = name;
  }

  greet() {
    return `你好，我是 ${this.name}。`;
  }
}

class SuperHero extends Person {
  constructor(name, power) {
    super(name);
    this.power = power;
  }

  // 重写 greet 方法
  greet() {
    // 首先，调用父类的 greet 方法
    const parentGreeting = super.greet();
    // 然后，添加子类自己的逻辑
    return `${parentGreeting} 我的超能力是${this.power}！`;
  }
}

const superman = new SuperHero('超人', '飞行');
console.log(superman.greet());
// 输出: 你好，我是 超人。 我的超能力是飞行！
```

### 🔍 Level 3: 对比学习（避免陷阱）
在子类构造函数中，`super()`的调用时机至关重要。

```javascript
// Level 3: 对比学习
class Parent {
  constructor(name) {
    this.name = name;
  }
}

console.log("=== 错误用法 ===");
try {
  class ChildWrong extends Parent {
    constructor(name, age) {
      // ❌ 错误: 在调用 super() 之前使用了 'this'
      this.age = age; 
      super(name);
    }
  }
  const wrong = new ChildWrong('小明', 10);
} catch (error) {
  console.log(`错误信息: ${error.message}`);
  // 解释: 在子类构造函数中，this 的值在 super() 调用之前是未初始化的。
  // 任何尝试访问 this 的行为都会导致 ReferenceError。
}


console.log("\n=== 正确用法 ===");
class ChildRight extends Parent {
  constructor(name, age) {
    // ✅ 正确: 必须先调用 super() 来初始化父类部分
    super(name);
    // 现在可以安全地使用 'this' 了
    this.age = age;
  }
  
  introduce() {
    return `我叫${this.name}，今年${this.age}岁。`;
  }
}
const right = new ChildRight('小红', 12);
console.log(right.introduce());
// 解释: 正确的顺序是先让父类通过 super() 完成对 this 的基本构建，
// 然后子类再在 this 上添加自己的属性。
```

### 🚀 Level 4: 实战应用（真实场景）
**🎮 游戏场景：角色升级系统**

让我们来创建一个简单的RPG游戏角色系统。有一个基础的`Player`类，然后我们创建一个更专业的`Mage`（法师）子类，它继承了玩家的基本属性，并增加了独特的魔法能力。

```javascript
// Level 4: 游戏角色升级系统

// 基础玩家类
class Player {
  constructor(name, level = 1) {
    this.name = name;
    this.level = level;
    this.health = 100 + level * 10;
  }

  attack() {
    const damage = 5 + this.level * 2;
    console.log(`🪓 ${this.name} 挥舞武器，造成了 ${damage} 点伤害！`);
    return damage;
  }

  showStatus() {
    return `[${this.name} | 等级:${this.level} | ❤️生命:${this.health}]`;
  }
}

// 法师子类，继承自玩家
class Mage extends Player {
  constructor(name, level = 1, magicType = '火焰') {
    // 调用父类构造函数，初始化基础属性
    super(name, level);
    this.mana = 50 + level * 15; // 法师有额外的法力值
    this.magicType = magicType;
  }

  // 法师的特殊技能：施放法术
  castSpell() {
    if (this.mana >= 20) {
      this.mana -= 20;
      const spellDamage = 15 + this.level * 5;
      console.log(`🔮 ${this.name} 吟唱咒语，释放了一个${this.magicType}法术，造成 ${spellDamage} 点伤害！剩余法力: ${this.mana}`);
      return spellDamage;
    } else {
      console.log(`🌀 法力不足！${this.name} 无法施法。`);
      return 0;
    }
  }

  // 重写 showStatus 方法，以显示更多信息
  showStatus() {
    // 调用父类的 showStatus 方法获取基础信息
    const basicStatus = super.showStatus();
    // 在基础信息上添加法师特有的法力值信息
    return `${basicStatus} [💧法力:${this.mana}]`;
  }
}

console.log("--- 欢迎来到JS冒险世界！ ---");

const gandalf = new Mage('甘道夫', 5, '光');

console.log("角色创建成功:");
console.log(gandalf.showStatus());

console.log("\n--- 战斗开始！ ---");
gandalf.attack();
gandalf.castSpell();
gandalf.castSpell();
gandalf.castSpell(); // 尝试施放第三次法术

console.log("\n--- 战斗后状态 ---");
console.log(gandalf.showStatus());
```

### 💡 记忆要点
- **要点1**：`super()`用于在子类构造函数中调用父类的构造函数，并且必须在`this`之前调用。
- **要点2**：`super.methodName()`用于在子类中调用被重写的父类同名方法，实现功能扩展而非完全替代。
- **要点3**：`super`是连接子类与父类的桥梁，是实现代码复用和继承的核心工具。

<!--
metadata:
  syntax: ["super", "class", "constructor", "extends"]
  pattern: ["inheritance"]
  api: ["console.log"]
  concept: ["inheritance", "constructor-chaining", "this-binding", "polymorphism"]
  difficulty: intermediate
  dependencies: ["js-sec-4-2-4"]
  related: ["js-sec-4-2-4"]
-->