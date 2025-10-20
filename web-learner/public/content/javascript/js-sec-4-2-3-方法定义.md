## 方法定义

### 🎯 核心概念
方法是附加到对象上的函数，它定义了该对象可以执行的行为或操作。在`class`语法中，方法是直接在类体中定义的函数，它会自动成为所有由该类创建的实例的共享行为。

### 📚 Level 1: 基础认知（30秒理解）
想象一个“机器人”蓝图（class）。我们可以为这个蓝图定义一个“打招呼”的行为（方法）。所有根据这个蓝图制造出来的机器人（实例）都会这个行为。

```javascript
// 定义一个“机器人”的蓝图
class Robot {
  constructor(name) {
    this.name = name;
  }

  // 定义一个名为 "sayHi" 的方法
  sayHi() {
    console.log(`你好，我是机器人 ${this.name}。`);
  }
}

// 创建一个机器人实例
const terminator = new Robot('T-800');

// 调用实例的 sayHi 方法
terminator.sayHi(); // 输出: 你好，我是机器人 T-800。
```

### 📈 Level 2: 核心特性（深入理解）
在类的方法中，`this`关键字和`getter`/`setter`是两个核心特性。

#### 特性1: 使用 `this` 关键字访问实例属性
在类的方法内部，`this` 关键字是一个特殊的指针，它指向调用该方法的具体实例。这使得方法可以读取或修改该实例自身的属性。

```javascript
class Player {
  constructor(name) {
    this.name = name;
    this.health = 100;
  }

  // 定义一个显示状态的方法
  showStatus() {
    // 'this' 指向调用此方法的 player 实例
    console.log(`玩家: ${this.name}, 生命值: ${this.health}%`);
  }

  // 定义一个受伤的方法
  takeDamage(amount) {
    // 'this' 指向调用此方法的 player 实例，并修改其 health 属性
    this.health -= amount;
    console.log(`${this.name} 受到了 ${amount}点伤害!`);
  }
}

const player1 = new Player('英雄阿杰');

player1.showStatus(); // 调用时 this 指向 player1
player1.takeDamage(15);
player1.showStatus(); // 再次查看状态，health 属性已被修改
```

#### 特性2: Getter 和 Setter
Getter和Setter允许你像访问属性一样调用函数，从而对属性的读取和写入过程进行更精细的控制，例如进行验证或计算。

```javascript
class Circle {
  constructor(radius) {
    this.radius = radius;
  }

  // 定义一个名为 'diameter' 的 getter
  // 访问 circle.diameter 时，这个函数会自动执行
  get diameter() {
    console.log('正在计算直径...');
    return this.radius * 2;
  }

  // 定义一个名为 'diameter' 的 setter
  // 当执行 circle.diameter = newValue 时，这个函数会自动执行
  set diameter(newDiameter) {
    if (newDiameter > 0) {
      console.log('正在通过设置直径来更新半径...');
      this.radius = newDiameter / 2;
    } else {
      console.log('直径必须是正数！');
    }
  }
}

const myCircle = new Circle(10);

// 像访问属性一样调用 getter
console.log(`圆的直径是: ${myCircle.diameter}`);

// 像给属性赋值一样调用 setter
myCircle.diameter = 30;
console.log(`更新后，圆的半径是: ${myCircle.radius}`);
```

### 🔍 Level 3: 对比学习（避免陷阱）
在类的方法中，`this`的指向通常是可靠的。但如果将方法提取出来作为回调函数传递，`this`的上下文可能会丢失，这与普通对象方法遇到的陷阱类似。

```javascript
class GameTimer {
  constructor() {
    this.seconds = 0;
    setInterval(() => {
      this.tick(); // 在箭头函数中，this被正确捕获
    }, 1000);
  }

  tick() {
    console.log(`游戏已进行 ${++this.seconds} 秒。`);
  }
}

// const myGame = new GameTimer(); // 在浏览器中运行会每秒打印一次

// --- 对比演示 ---
class ButtonManager {
  constructor() {
    this.buttonText = '点击我';
  }

  // ✅ 正确用法：在回调中使用箭头函数，保留 this
  setupCorrectListener(button) {
    button.addEventListener('click', () => {
      console.log(`按钮被点击了！按钮文字是: ${this.buttonText}`);
    });
  }

  // ❌ 错误用法：直接传递方法，this 会丢失
  setupWrongListener(button) {
    // 当事件触发时，handleClick 的 this 将是 button 元素或 undefined
    button.addEventListener('click', this.handleClick);
  }
  
  handleClick() {
    // 这里的 this 不再是 ButtonManager 的实例
    console.log(`这个按钮的文字是: ${this.buttonText}`); // this.buttonText 会是 undefined
  }
}

// 模拟一个按钮
const mockButton = { addEventListener: (type, fn) => { fn(); } };
const manager = new ButtonManager();

console.log("=== 正确用法 ===");
manager.setupCorrectListener(mockButton);

console.log("\n=== 错误用法 ===");
manager.setupWrongListener(mockButton); // 会打印出 undefined
```

### 🚀 Level 4: 实战应用（真实场景）
**🎮 游戏场景：史莱姆的冒险**

我们来创建一个史莱姆角色类！它有生命值、攻击力，还有一些有趣的技能（方法），让它在我们的游戏世界里活灵活现。

```javascript
class Slime {
  constructor(name, color = '蓝色') {
    this.name = name;
    this.hp = 50;
    this.maxHp = 50;
    this.attackPower = 5;
    this.color = color;
    console.log(`一只${this.color}的史莱姆'${this.name}'诞生了！`);
  }

  // 方法1: 显示状态
  displayStatus() {
    console.log(`[状态] 我是${this.color}的史莱姆'${this.name}' | HP: ${this.hp}/${this.maxHp}`);
  }

  // 方法2: 攻击敌人
  attack(targetName) {
    console.log(`💥 '${this.name}' 对 '${targetName}' 使用了「撞击」！造成了 ${this.attackPower} 点伤害！`);
  }

  // 方法3: 受到伤害
  takeDamage(damage) {
    this.hp -= damage;
    if (this.hp <= 0) {
      this.hp = 0;
      console.log(`😭 啊哦... '${this.name}' 被击败了，变成了一滩液体...`);
    } else {
      console.log(`😨 '${this.name}' 受到了 ${damage} 点伤害！`);
      this.displayStatus();
    }
  }

  // 方法4: 治愈自己 (不能超过最大HP)
  heal(amount) {
    this.hp += amount;
    if (this.hp > this.maxHp) {
      this.hp = this.maxHp;
    }
    console.log(`✨ '${this.name}' 治愈了自己，恢复了 ${amount} 点HP！`);
    this.displayStatus();
  }
}

// --- 让我们开始一场小小的冒险吧！ ---
console.log("冒险开始！一只史莱姆出现了！");
const slimey = new Slime('噗噗');
slimey.displayStatus();

console.log("\n--- 遭遇了敌人：一只愤怒的小鸡 ---");
slimey.attack("愤怒的小鸡");

console.log("\n--- 史莱姆遭到了反击！ ---");
slimey.takeDamage(20);

console.log("\n--- 史莱姆决定吃掉一颗治愈果冻 ---");
slimey.heal(15);

console.log("\n--- 史莱姆被最终一击击中！ ---");
slimey.takeDamage(100);
```

### 💡 记忆要点
- **要点1**：在 `class` 中，直接在类体里定义的函数就是实例方法。
- **要点2**：方法内部使用 `this` 关键字来访问和操作该实例自身的属性。
- **要点3**：使用 `get` 和 `set` 关键字可以创建计算属性，让属性的读写过程像函数一样可控。

<!--
metadata:
  syntax: ["class", "constructor", "this"]
  pattern: ["object-oriented-programming"]
  api: ["console.log"]
  concept: ["method", "getter", "setter", "this-binding"]
  difficulty: intermediate
  dependencies: ["js-sec-4-2-1"]
  related: ["js-sec-4-2-2"]
-->
