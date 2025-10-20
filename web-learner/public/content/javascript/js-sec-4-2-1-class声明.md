## class声明

### 🎯 核心概念
`class` 声明提供了一种更清晰、更简洁的方式来创建对象“蓝图”，它是 JavaScript 现有原型继承模型的语法糖，让面向对象编程的写法更直观、更易于理解。

### 📚 Level 1: 基础认知（30秒理解）
`class` 就像一个模具，用来创建具有相同属性和方法的对象。`constructor` 是一个特殊的方法，在创建新对象时自动运行，用于初始化对象的属性。

```javascript
// 定义一个“宠物猫”的蓝图 (class)
class PetCat {
  // 构造函数，当使用 new 创建实例时被调用
  constructor(name, color) {
    this.name = name;
    this.color = color;
  }

  // 一个方法，所有 PetCat 实例都会有这个方法
  meow() {
    console.log(`我是${this.color}的猫咪，我叫${this.name}，喵~`);
  }
}

// 使用 class 蓝图创建一个具体的猫咪实例
const garfield = new PetCat('加菲', '橘色');
const tom = new PetCat('汤姆', '蓝灰色');

// 调用实例的方法
garfield.meow();
tom.meow();
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: `extends` 继承
继承允许一个类（子类）获取另一个类（父类）的属性和方法，实现代码复用和层级关系。

```javascript
// 父类：定义所有动物的通用特性
class Animal {
  constructor(name) {
    this.name = name;
    this.speed = 0;
  }

  run(speed) {
    this.speed = speed;
    console.log(`${this.name} 正在以每小时 ${this.speed} 公里的速度奔跑！`);
  }

  stop() {
    this.speed = 0;
    console.log(`${this.name} 停了下来。`);
  }
}

// 子类：Rabbit 继承自 Animal
// 它拥有 Animal 的所有属性和方法，并可以添加自己的特性
class Rabbit extends Animal {
  // Rabbit 可以有自己的方法
  hide() {
    console.log(`${this.name} 找到一个洞，藏了起来！`);
  }
}

const bugsBunny = new Rabbit('兔八哥');

// 调用从 Animal 父类继承来的方法
bugsBunny.run(40); 
bugsBunny.stop();

// 调用 Rabbit 自己独有的方法
bugsBunny.hide();
```

#### 特性2: `static` 静态方法
静态方法属于类本身，而不是类的实例。它们通常用于创建与类相关的工具函数，可以直接通过类名调用，无需创建实例。

```javascript
class MathHelper {
  // 这是一个静态方法，直接通过 MathHelper.add() 调用
  static add(a, b) {
    return a + b;
  }
  
  // 这是一个普通方法，需要先创建实例才能调用
  multiply(a, b) {
    return a * b;
  }
}

// 直接调用静态方法，无需创建实例
const sum = MathHelper.add(5, 10);
console.log(`静态方法计算结果: ${sum}`);

// 尝试在实例上调用静态方法会导致错误
// const helperInstance = new MathHelper();
// console.log(helperInstance.add(2, 3)); // 这会抛出错误：helperInstance.add is not a function

// 调用普通方法，必须先创建实例
const helperInstance = new MathHelper();
const product = helperInstance.multiply(5, 10);
console.log(`实例方法计算结果: ${product}`);
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个常见的错误是忘记使用 `new` 关键字来创建类的实例。类不是一个普通的函数，必须通过 `new` 来实例化。

```javascript
class Player {
  constructor(name) {
    this.name = name;
    this.score = 0;
  }

  increaseScore() {
    this.score += 10;
    console.log(`${this.name} 的分数增加了，现在是 ${this.score}`);
  }
}

console.log("=== 错误用法 ===");
try {
  // ❌ 错误：直接像调用普通函数一样调用 class 构造函数
  // 这会抛出一个 TypeError，因为类构造函数不能在没有 'new' 的情况下被调用
  const player1 = Player('Alex'); 
  player1.increaseScore();
} catch (e) {
  console.error("出错了:", e.message);
  console.log("解释: Class 构造函数必须使用 'new' 关键字来调用，否则无法创建实例。");
}

console.log("\n=== 正确用法 ===");
// ✅ 正确：使用 'new' 关键字创建 Player 的一个实例
const player2 = new Player('Betty');
player2.increaseScore();
console.log("解释: 'new' 关键字创建了一个 Player 的新实例，并正确地将 this 指向这个新实例，然后调用构造函数进行初始化。");
```

### 🚀 Level 4: 实战应用（真实场景）
**🎮 游戏场景：魔法师与战士的冒险对决**

在这个场景中，我们创建一个基础的 `Character` 类，然后派生出具有不同技能的 `Mage` (魔法师) 和 `Warrior` (战士) 子类，让他们进行一场有趣的模拟对决。

```javascript
// 基础角色蓝图
class Character {
  constructor(name, hp, attackPower) {
    this.name = name;
    this.hp = hp;
    this.attackPower = attackPower;
  }

  attack(target) {
    console.log(`💥 ${this.name} 对 ${target.name} 发动了普通攻击!`);
    target.takeDamage(this.attackPower);
  }

  takeDamage(damage) {
    this.hp -= damage;
    if (this.hp <= 0) {
      this.hp = 0;
      console.log(`💀 ${this.name} 受到了 ${damage} 点伤害，倒下了...`);
    } else {
      console.log(`💔 ${this.name} 受到了 ${damage} 点伤害, 剩余 HP: ${this.hp}`);
    }
  }

  showStatus() {
    console.log(`[状态] ${this.name} | HP: ${this.hp}`);
  }
}

// 魔法师子类，继承自 Character
class Mage extends Character {
  constructor(name, hp, attackPower, mana) {
    super(name, hp, attackPower); // 调用父类的构造函数
    this.mana = mana;
  }

  // 魔法师的特殊技能
  castFireball(target) {
    if (this.mana >= 20) {
      this.mana -= 20;
      const spellDamage = this.attackPower * 2; // 火球术伤害翻倍
      console.log(`🔥 ${this.name} 吟唱咒语，对 ${target.name} 释放了火球术! (消耗20点法力)`);
      target.takeDamage(spellDamage);
    } else {
      console.log(`💧 ${this.name} 的法力不足，施法失败!`);
      this.attack(target); // 法力不够，改为普通攻击
    }
  }
}

// 战士子类，继承自 Character
class Warrior extends Character {
  constructor(name, hp, attackPower, rage) {
    super(name, hp, attackPower);
    this.rage = rage;
  }
  
  // 战士的特殊技能
  charge(target) {
    if (this.rage >= 15) {
      this.rage -= 15;
      const chargeDamage = this.attackPower + 10; // 冲锋造成额外伤害
      console.log(`🛡️ ${this.name} 发动英勇冲锋，撞向 ${target.name}! (消耗15点怒气)`);
      target.takeDamage(chargeDamage);
    } else {
      console.log(`😠 ${this.name} 怒气不足，冲锋失败!`);
      this.attack(target); // 怒气不够，改为普通攻击
    }
  }
}

// --- 冒险开始！ ---
console.log("--- ⚔️ 决斗开始! ⚔️ ---");
const gandalf = new Mage('甘道夫', 80, 15, 50); // 法师：血少，攻高，有法力
const aragorn = new Warrior('阿拉贡', 120, 10, 40); // 战士：血厚，攻低，有怒气

gandalf.showStatus();
aragorn.showStatus();
console.log("\n--- 第一回合 ---");

aragorn.charge(gandalf);
gandalf.castFireball(aragorn);

console.log("\n--- 第二回合 ---");

aragorn.attack(gandalf);
gandalf.castFireball(aragorn);

console.log("\n--- 决斗结束 ---");
gandalf.showStatus();
aragorn.showStatus();
```

### 💡 记忆要点
- **蓝图思想**：`class` 是创建对象的“蓝图”，`new` 关键字是根据蓝图建造实例的“工厂”。
- **构造函数**：`constructor` 是类的“初始化程序”，在 `new` 一个实例时自动执行，负责设置初始属性。
- **继承扩展**：`extends` 关键字是“继承”的标志，允许子类复用并扩展父类的功能，实现代码的层级化和复用。

<!--
metadata:
  syntax: [class, constructor, extends, static, new]
  pattern: [object-oriented-programming]
  api: [console.log, console.error]
  concept: [prototype, this-binding, inheritance]
  difficulty: intermediate
  dependencies: [无]
  related: []
-->