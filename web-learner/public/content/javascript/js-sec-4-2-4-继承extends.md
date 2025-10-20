## 继承extends

### 🎯 核心概念
`extends` 关键字用于创建一个类作为另一个类的子类，让子类能够“继承”父类的属性和方法，从而实现代码的复用和层级化管理。

### 📚 Level 1: 基础认知（30秒理解）
`extends` 就像生物学中的“遗传”。比如，“狗”类继承了“动物”类的基本特征，无需重新定义。

```javascript
// 父类：动物
class Animal {
  constructor(name) {
    this.name = name;
  }

  speak() {
    console.log(`${this.name} 发出了一些声音。`);
  }
}

// 子类：狗，通过 extends 继承自动物
class Dog extends Animal {
  // 这个类是空的，但它自动拥有了 Animal 的所有东西
}

// 创建一个 Dog 实例
const myDog = new Dog('旺财');

// 调用继承自 Animal 的 speak 方法
myDog.speak(); // 输出: 旺财 发出了一些声音。

console.log(`我的狗叫: ${myDog.name}`); // 输出: 我的狗叫: 旺财
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: `super` 关键字调用父类
`super` 关键字用于访问和调用父类上的函数。在构造函数中，`super()` 调用父类的构造函数；在普通方法中，`super.method()` 调用父类的方法。

```javascript
class Vehicle {
  constructor(name) {
    this.name = name;
  }

  move() {
    return `${this.name} 正在移动。`;
  }
}

class Car extends Vehicle {
  constructor(name, brand) {
    // 1. 使用 super(name) 调用父类的 constructor(name)
    // 必须在子类构造函数中使用 'this' 之前调用 super()
    super(name);
    this.brand = brand;
  }

  move() {
    // 2. 使用 super.move() 调用父类的 move 方法
    const parentMoveAction = super.move();
    console.log(`${this.brand} 品牌的 ${parentMoveAction} 发动机发出轰鸣！`);
  }
}

const myCar = new Car('探险者', '福特');
myCar.move();
// 输出: 福特 品牌的 探险者 正在移动。 发动机发出轰鸣！
```

#### 特性2: 方法重写 (Method Overriding)
子类可以定义一个与父类同名的方法，这个过程称为“重写”。当调用该方法时，会执行子类中的版本，而不是父类的版本。

```javascript
class GameCharacter {
  attack() {
    console.log("角色使用了基础攻击，造成 10 点伤害！");
  }
}

class Mage extends GameCharacter {
  // 重写了父类的 attack 方法
  attack() {
    console.log("法师吟唱咒语，释放了火球术！🔥🔥🔥 造成 50 点伤害！");
  }

  teleport() {
    console.log("法师使用了闪现！");
  }
}

const genericCharacter = new GameCharacter();
const gandalf = new Mage();

console.log("--- 父类实例调用 ---");
genericCharacter.attack();

console.log("\n--- 子类实例调用 ---");
gandalf.attack(); // 调用的是 Mage 中重写后的方法
gandalf.teleport(); // 调用 Mage 自己独有的方法
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个最常见的错误是在子类的 `constructor` 中，在调用 `super()` 之前就尝试使用 `this` 关键字。

```javascript
// 父类定义
class Person {
  constructor(name) {
    this.name = name;
  }
}

console.log("=== 错误用法 ===");
// ❌ 在 super() 调用前使用 this
try {
  class Student extends Person {
    constructor(name, studentId) {
      // 错误！在 super() 完成初始化之前，'this' 还不存在
      this.studentId = studentId; 
      super(name);
    }
  }
  const student = new Student('小明', 'S001');
} catch (e) {
  console.error("捕获到错误:", e.message);
}
console.log("解释: 子类的 'this' 是由父类的构造函数创建的。因此，必须先调用 super() 来完成这个创建过程，然后才能安全地使用 'this'。");


console.log("\n=== 正确用法 ===");
// ✅ 先调用 super()，再使用 this
class Teacher extends Person {
  constructor(name, subject) {
    // 正确！首先调用父类构造函数，初始化 this
    super(name);
    // 现在 'this' 已经是一个合法的实例，可以给它添加属性
    this.subject = subject;
  }
  
  introduce() {
    console.log(`大家好，我是 ${this.name} 老师，我教 ${this.subject}。`);
  }
}
const mrWang = new Teacher('王老师', 'JavaScript');
mrWang.introduce();
console.log("解释: 先通过 super(name) 完成父类的初始化，创建了 this 上下文，然后子类才能继续添加自己的属性。");
```

### 🚀 Level 4: 实战应用（真实场景）

#### 🚀 科幻冒险：机器人军团

**场景**：我们正在创建一个机器人军队。有一个基础的“机器人”模型，然后我们基于它创造出更专业的战斗机器人和清洁机器人，每个都有自己独特的功能。

```javascript
// 基础机器人 (父类)
class Robot {
  constructor(name) {
    this.name = name;
    this.battery = 100;
  }

  charge() {
    this.battery = 100;
    console.log(`🤖 ${this.name} 正在充电... 电量恢复到 100%！`);
  }

  reportStatus() {
    console.log(`- ${this.name} 状态: 电量 ${this.battery}%`);
  }
}

// 战斗机器人 (子类)
class BattleBot extends Robot {
  constructor(name, weapon) {
    super(name); // 调用父类构造函数设置名字和电量
    this.weapon = weapon;
  }

  // 战斗机器人特有的方法
  attack() {
    if (this.battery >= 10) {
      this.battery -= 10;
      console.log(`💥 ${this.name} 使用 ${this.weapon} 发动攻击！电量消耗 10%。`);
    } else {
      console.log(`🔋 ${this.name} 电量不足，无法攻击！需要充电。`);
    }
  }

  // 重写父类的方法，加入更多信息
  reportStatus() {
    super.reportStatus(); // 先调用父类的方法打印基础信息
    console.log(`  武器装备: ${this.weapon}`); // 再添加子类特有的信息
  }
}

// 清洁机器人 (子类)
class CleanBot extends Robot {
  constructor(name) {
    super(name);
    this.isCleaning = false;
  }

  // 清洁机器人特有的方法
  toggleCleaning() {
    if (this.battery > 5) {
      this.isCleaning = !this.isCleaning;
      if (this.isCleaning) {
        console.log(`🧹 ${this.name} 开始打扫房间！嗡嗡嗡...`);
        this.battery -= 5;
      } else {
        console.log(`⏸️ ${this.name} 停止打扫。`);
      }
    } else {
      console.log(`🔋 ${this.name} 没电了，无法开始打扫。`);
    }
  }
}

console.log("--- 机器人军团集结！ ---");
const terminator = new BattleBot('终结者T-800', '等离子炮');
const wallE = new CleanBot('瓦力');

terminator.reportStatus();
wallE.reportStatus();

console.log("\n--- 开始行动！ ---");
terminator.attack();
terminator.attack();
wallE.toggleCleaning();

console.log("\n--- 行动后状态 ---");
terminator.reportStatus();
wallE.reportStatus();

console.log("\n--- 终结者持续战斗直到电量耗尽 ---");
for(let i = 0; i < 8; i++) {
  terminator.attack();
}
terminator.charge(); // 充电
terminator.attack(); // 再次攻击
```

### 💡 记忆要点
- **要点1**：`extends` 用于创建一个类，该类是另一个类（父类）的子类，实现代码复用。
- **要点2**：在子类的 `constructor` 中，必须在使用 `this` 之前调用 `super()` 来初始化父类。
- **要点3**：使用 `super.methodName()` 可以在子类中调用父类的同名方法，方便扩展功能而不是完全重写。

<!--
metadata:
  syntax: ["class", "extends", "constructor", "super"]
  api: ["console.log", "console.error"]
  concept: ["inheritance", "prototype"]
  difficulty: intermediate
  dependencies: []
  related: []
-->