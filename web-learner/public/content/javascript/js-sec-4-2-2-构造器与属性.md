## 构造器与属性

### 🎯 核心概念
构造器（constructor）是一个特殊的类方法，它像一个“对象工厂蓝图”，用于在创建新对象实例时，为其设置初始状态（即属性）。

### 📚 Level 1: 基础认知（30秒理解）
构造器在 `new` 一个新对象时被自动调用。它的主要工作就是接收参数，并将这些参数赋值给新对象的属性。

```javascript
// 定义一个“宠物”蓝图 (class)
class Pet {
  // 构造器：当创建一个新宠物时，这个函数会自动运行
  constructor(name, type) {
    console.log(`正在创建一只新的宠物...`);
    // `this` 指向新创建的对象实例
    // 将传入的 name 和 type 赋值给新对象的属性
    this.name = name;
    this.type = type;
  }
}

// 使用 new 关键字，根据 Pet 蓝图创建一个具体的宠物实例
const myCat = new Pet('咪咪', '猫');

// 访问实例的属性
console.log(`我的宠物叫 ${myCat.name}，它是一只${myCat.type}。`);
console.log(myCat);
```

### 📈 Level 2: 核心特性（深入理解）
构造器不仅可以简单赋值，还可以包含更复杂的逻辑和默认值。

#### 特性1: 构造器参数可以有默认值
如果创建实例时没有提供某些参数，构造器可以使用预设的默认值，让对象创建更加灵活。

```javascript
class Player {
  // 为 level 和 score 设置默认值
  constructor(name, level = 1, score = 0) {
    this.name = name;
    this.level = level;
    this.score = score;
  }
}

// 创建玩家时只提供了名字，level 和 score 会使用默认值
const newPlayer = new Player('新手玩家');
console.log('新玩家信息:', newPlayer);

// 创建一个提供了所有参数的玩家
const proPlayer = new Player('高玩大神', 99, 150000);
console.log('高手玩家信息:', proPlayer);
```

#### 特性2: 在构造器中进行逻辑判断
构造器是一个函数，因此你可以在其中编写任何逻辑代码，来动态地决定对象的初始属性。

```javascript
class Monster {
  constructor(type) {
    this.type = type;
    this.createdAt = new Date().toLocaleTimeString();

    // 根据传入的怪物类型，动态设置不同的属性
    if (type === '哥布林') {
      this.health = 50;
      this.attack = 5;
      this.loot = '金币';
    } else if (type === '史莱姆') {
      this.health = 30;
      this.attack = 2;
      this.loot = '凝胶';
    } else {
      this.health = 100;
      this.attack = 10;
      this.loot = '未知物品';
    }
  }
}

const goblin = new Monster('哥布林');
console.log('遭遇了哥布林!', goblin);

const slime = new Monster('史莱姆');
console.log('发现了史莱姆!', slime);
```

### 🔍 Level 3: 对比学习（避免陷阱）
在构造器中，必须使用 `this` 关键字来将属性附加到新创建的实例上。如果忘记使用 `this`，属性将不会被正确设置。

```javascript
console.log("=== 错误用法 ===");
// ❌ 忘记使用 `this` 关键字
class Book_Wrong {
  constructor(title, author) {
    // 这里的 title 和 author 只是构造函数内部的局部变量
    // 它们在函数执行完毕后就会消失，并不会成为实例的属性
    let bookTitle = title;
    let bookAuthor = author;
  }
}

const wrongBook = new Book_Wrong('JavaScript高级程序设计', 'Nicholas C. Zakas');
// 尝试访问属性，会得到 undefined，因为它们从未被附加到实例上
console.log('书名:', wrongBook.bookTitle); // 输出: undefined
console.log('作者:', wrongBook.bookAuthor); // 输出: undefined
console.log('错误创建的实例:', wrongBook); // 输出: Book_Wrong {} (一个空对象)


console.log("\n=== 正确用法 ===");
// ✅ 使用 `this` 关键字将属性绑定到实例
class Book_Correct {
  constructor(title, author) {
    // `this` 指向即将被创建的 book 实例
    // this.title = ... 这行代码的意思是：“给这个新实例添加一个名为 title 的属性”
    this.title = title;
    this.author = author;
  }
}

const correctBook = new Book_Correct('你不知道的JavaScript', 'Kyle Simpson');
// 可以成功访问到实例的属性
console.log('书名:', correctBook.title);
console.log('作者:', correctBook.author);
console.log('正确创建的实例:', correctBook);
```

### 🚀 Level 4: 实战应用（真实场景）
**场景：🎮 RPG游戏角色生成器**

让我们创建一个游戏角色生成器。每次创建新角色时，构造器会根据玩家选择的种族和职业，自动分配不同的初始属性和技能，让每个角色都独一无二！

```javascript
// 角色生成器
class GameCharacter {
  constructor(name, race, job) {
    this.name = name;
    this.race = race;
    this.job = job;
    this.level = 1;
    this.inventory = ['面包', '水'];

    console.log(`🌟 英雄诞生！欢迎，${this.race}族的${this.job}——${this.name}！`);

    // --- 根据种族分配基础属性 ---
    if (this.race === '兽人') {
      this.health = 120;
      this.strength = 15;
      this.agility = 8;
    } else if (this.race === '精灵') {
      this.health = 80;
      this.strength = 8;
      this.agility = 15;
    } else { // 默认人类
      this.health = 100;
      this.strength = 10;
      this.agility = 10;
    }

    // --- 根据职业分配初始技能 ---
    if (this.job === '战士') {
      this.skills = ['猛击', '冲锋'];
      this.strength += 3; // 战士有额外的力量加成
    } else if (this.job === '弓箭手') {
      this.skills = ['精准射击', '后跳'];
      this.agility += 3; // 弓箭手有额外的敏捷加成
    } else {
      this.skills = ['火球术', '治疗术'];
    }
  }

  // 一个简单的方法来展示角色状态
  showStatus() {
    console.log(`
    --- 角色状态面板 ---
    姓名: ${this.name}
    种族: ${this.race}
    职业: ${this.job}
    等级: ${this.level}
    生命值: ${this.health}
    力量: ${this.strength}
    敏捷: ${this.agility}
    技能: ${this.skills.join(', ')}
    背包: ${this.inventory.join(', ')}
    --------------------
    `);
  }
}

// 创建一个兽人战士
const orcWarrior = new GameCharacter('格罗姆', '兽人', '战士');
orcWarrior.showStatus();

// 创建一个精灵弓箭手
const elfArcher = new GameCharacter('莉雅', '精灵', '弓箭手');
elfArcher.showStatus();
```

### 💡 记忆要点
- **蓝图与实例**：`class` 是蓝图，`constructor` 是构建过程，`new` 关键字是启动构建的指令，最终产生一个对象实例。
- **`this`是关键**：在 `constructor` 内部，`this` 指向正在被创建的新对象实例。必须用 `this.propertyName = value` 的方式来添加属性。
- **灵活初始化**：构造器是一个函数，可以利用参数默认值、条件判断等逻辑，实现复杂和动态的对象初始化。

<!--
metadata:
  syntax: ["class", "constructor"]
  pattern: ["object-creation"]
  api: ["console.log"]
  concept: ["this-binding", "instance", "class", "object-properties"]
  difficulty: intermediate
  dependencies: []
  related: ["js-sec-4-2-1", "js-sec-4-2-3"]
-->