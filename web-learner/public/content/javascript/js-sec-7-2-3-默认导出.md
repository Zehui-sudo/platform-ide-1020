## 默认导出

### 🎯 核心概念
默认导出（Default Export）用于从一个模块中导出一个“主要”或“唯一”的功能，使得在导入时语法更简洁，无需使用花括号，并且可以为其指定任意名称。

### 📚 Level 1: 基础认知（30秒理解）
在ES模块中，文件即模块。`export default` 关键字可以轻松地将一个函数、类或对象作为模块的默认输出。

> **注意**: 为了让代码块可独立运行，我们将在一个代码块内用注释模拟两个文件：`module.js` 和 `main.js`。

```javascript
// 假设这是文件: greetings.js
// 我们定义一个函数并将其作为默认导出
const createGreeting = (name) => {
  return `你好, ${name}! 欢迎来到 JavaScript 世界。`;
};
// 在真实文件中，你会写: export default createGreeting;


// 假设这是文件: main.js
// 在真实文件中，你会写: import myGreetingFunction from './greetings.js';
// 为了演示，我们直接使用上面定义的函数
const myGreetingFunction = createGreeting;

// 现在我们可以使用这个导入的函数了
const message = myGreetingFunction("探险家");
console.log(message);
// 输出: 你好, 探险家! 欢迎来到 JavaScript 世界。
```

### 📈 Level 2: 核心特性（深入理解）
默认导出有一些非常方便的特性，比如支持匿名导出和导入时自由命名。

#### 特性1: 支持匿名导出
`export default` 后面可以直接跟一个匿名的函数、类或值的定义。

```javascript
// 模拟文件: anonymous-module.js
// 我们可以直接导出一个匿名的箭头函数
const anonymousGreeter = (name) => `Hello, ${name}! This is an anonymous function.`;
// 真实语法: export default (name) => `Hello, ${name}! This is an anonymous function.`;

// 也可以导出一个匿名的对象
const anonymousConfig = {
    version: '1.0.0',
    author: 'Anonymous'
};
// 真实语法: export default { version: '1.0.0', author: 'Anonymous' };


// 模拟文件: main.js
// 导入匿名的函数
const greeter = anonymousGreeter;
console.log(greeter('Alice'));
// 输出: Hello, Alice! This is an anonymous function.

// 导入匿名的对象
const config = anonymousConfig;
console.log(`App Version: ${config.version} by ${config.author}`);
// 输出: App Version: 1.0.0 by Anonymous
```

#### 特性2: 导入时可任意命名
这是默认导出的最大便利之一。因为每个模块只有一个默认导出，所以在导入时，你可以根据自己的喜好给它起任何名字。

```javascript
// 模拟文件: user-profile.js
// 定义一个类作为默认导出
class UserProfile {
  constructor(name, level) {
    this.name = name;
    this.level = level;
  }
  getInfo() {
    return `${this.name} (Level ${this.level})`;
  }
}
// 真实语法: export default UserProfile;


// 模拟文件: app.js
// 我们可以用任何我们喜欢的名字来导入它
const Profile = UserProfile; // 命名为 Profile
const Player = UserProfile;  // 或者命名为 Player

const user1 = new Profile('Byte Explorer', 99);
const user2 = new Player('Code Ninja', 50);

console.log('使用 "Profile" 名称导入:', user1.getInfo());
console.log('使用 "Player" 名称导入:', user2.getInfo());
// 输出:
// 使用 "Profile" 名称导入: Byte Explorer (Level 99)
// 使用 "Player" 名称导入: Code Ninja (Level 50)
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个常见的错误是混淆默认导出和命名导出的导入语法。一个模块可以同时有默认导出和命名导出，但它们的导入方式完全不同。

```javascript
// 模拟文件: mixed-exports.js
const mainFunction = () => "这是默认导出的主要功能。";
const helperFunction = () => "这是一个命名导出的辅助工具。";
// 真实语法:
// export default mainFunction;
// export { helperFunction };


console.log("=== 错误用法 ===");
// ❌ 错误1: 尝试用花括号导入默认导出
try {
  // 模拟: import { mainFunction } from './mixed-exports.js';
  // 这会失败，因为 mainFunction 是默认导出，不是命名导出
  const { mainFunction: wrongImport1 } = { default: mainFunction, helperFunction };
  // 在真实模块环境中，上面的导入会得到 undefined
  if (typeof wrongImport1 === 'undefined') {
    console.log("错误1: 无法用 {} 导入默认导出，得到 undefined。");
  }
} catch (e) {
  console.log("错误1: ", e.message);
}

// ❌ 错误2: 尝试不用花括号导入命名导出
try {
  // 模拟: import helperFunction from './mixed-exports.js';
  // 这会把默认导出的内容赋值给 helperFunction 变量，而不是导入真正的 helperFunction
  const wrongImport2 = mainFunction;
  console.log("错误2: 'import helperFunction' 实际上导入了默认导出:", wrongImport2());
} catch (e) {
  console.log("错误2: ", e.message);
}


console.log("\n=== 正确用法 ===");
// ✅ 正确: 同时导入默认导出和命名导出
// 模拟: import MyMain, { helperFunction } from './mixed-exports.js';
const MyMain = mainFunction;
const { helperFunction: correctHelper } = { helperFunction };

console.log("默认导出 (重命名为 MyMain):", MyMain());
console.log("命名导出 (helperFunction):", correctHelper());
// 输出:
// === 错误用法 ===
// 错误1: 无法用 {} 导入默认导出，得到 undefined。
// 错误2: 'import helperFunction' 实际上导入了默认导出: 这是默认导出的主要功能。
//
// === 正确用法 ===
// 默认导出 (重命名为 MyMain): 这是默认导出的主要功能。
// 命名导出 (helperFunction): 这是一个命名导出的辅助工具。
```

### 🚀 Level 4: 实战应用（真实场景）
**场景：🚀 科幻冒险 - 创建你的专属飞船**

在这个场景中，我们将创建一个 `Spaceship` 模块，它默认导出一个 `Spaceship` 类。这个类将成为我们太空冒险游戏的核心。主程序将导入这个类来建造和控制飞船。

```javascript
// 模拟文件: spaceship-factory.js
// 这个模块的核心功能就是定义和导出一个飞船类
class Spaceship {
  constructor(name, pilot) {
    this.name = name;
    this.pilot = pilot;
    this.fuel = 100;
    this.isLaunched = false;
    console.log(`🔧 飞船 "${this.name}" 建造完毕，舰长是 ${this.pilot}！`);
  }

  launch() {
    if (this.fuel <= 0) {
      console.log(`💥 发射失败！ "${this.name}" 燃料耗尽了！`);
      return;
    }
    this.isLaunched = true;
    this.fuel -= 10;
    console.log(`🚀 倒计时 3...2...1... 发射！ "${this.name}" 号已升空，目标星辰大海！`);
  }

  reportStatus() {
    const status = this.isLaunched ? '在轨飞行中' : '停靠在港口';
    console.log(
      `📊 状态报告: 飞船 "${this.name}", 舰长: ${this.pilot}, 燃料: ${this.fuel}%, 状态: ${status}`
    );
  }
}
// 真实语法: export default Spaceship;


// 模拟文件: mission-control.js
// 我们的主程序，负责启动任务
// 真实语法: import MyCoolShip from './spaceship-factory.js';
const MyCoolShip = Spaceship;

console.log("--- 星际任务控制中心 ---");

// 创建第一艘飞船，并用我们喜欢的名字 MyCoolShip 来接收导入的类
const voyager = new MyCoolShip("旅行者号", "柯克");
voyager.reportStatus();
voyager.launch();
voyager.reportStatus();

console.log("\n--- 第二舰队准备 ---");

// 创建第二艘飞船，展示了类的可复用性
const enterprise = new MyCoolShip("企业号", "皮卡德");
enterprise.reportStatus();
// 输出:
// --- 星际任务控制中心 ---
// 🔧 飞船 "旅行者号" 建造完毕，舰长是 柯克！
// 📊 状态报告: 飞船 "旅行者号", 舰长: 柯克, 燃料: 100%, 状态: 停靠在港口
// 🚀 倒计时 3...2...1... 发射！ "旅行者号" 号已升空，目标星辰大海！
// 📊 状态报告: 飞船 "旅行者号", 舰长: 柯克, 燃料: 90%, 状态: 在轨飞行中
//
// --- 第二舰队准备 ---
// 🔧 飞船 "企业号" 建造完毕，舰长是 皮卡德！
// 📊 状态报告: 飞船 "企业号", 舰长: 皮卡德, 燃料: 100%, 状态: 停靠在港口
```

### 💡 记忆要点
- **要点1**：`export default` 用于导出一个模块最核心或唯一的成员。
- **要点2**：每个模块最多只能有一个 `export default`。
- **要点3**：导入默认导出时无需花括号 `{}`，且可以为其指定任意合法的变量名。

<!--
metadata:
  syntax: default-export
  concept: es-modules
  difficulty: intermediate
  dependencies: [无]
  related: [js-sec-7-2-2]
-->