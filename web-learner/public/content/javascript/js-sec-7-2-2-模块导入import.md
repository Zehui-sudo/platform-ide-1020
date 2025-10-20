## 模块导入import

### 🎯 核心概念
`import` 语句用于从另一个模块导出的绑定中，导入只读的实时引用。它是JavaScript ES模块系统的核心，让我们可以将代码分割成可复用的、有组织的文件。

### 📚 Level 1: 基础认知（30秒理解）
最基础的用法是导入一个模块的“默认”导出。这就像从一个工具箱里拿出最常用的那个工具。

**注意：** 以下示例展示了两个独立文件 `greeter.js` 和 `main.js` 的内容。在实际环境中，你需要一个支持ES模块的浏览器或Node.js来运行它们。

```javascript
// 文件: greeter.js
// 我们定义一个函数并将其作为默认导出
export default function greet(name) {
  return `Hello, ${name}!`;
}

// =========================================

// 文件: main.js
// 从 'greeter.js' 导入默认导出的函数
import greet from './greeter.js';

const message = greet('World');
console.log(message);

// 假设在HTML中这样运行: <script type="module" src="main.js"></script>
// 输出:
// Hello, World!
```

### 📈 Level 2: 核心特性（深入理解）
`import` 提供了多种灵活的方式来导入模块的功能。

#### 特性1: 命名导入 (Named Imports)
当一个模块导出多个变量或函数时，我们可以使用花括号 `{}` 按需导入它们。

```javascript
// 文件: math.js
export const PI = 3.14159;
export function square(x) {
  return x * x;
}

// =========================================

// 文件: main.js
// 只导入我们需要的部分
import { PI, square } from './math.js';

console.log('圆周率 PI:', PI);
console.log('5 的平方是:', square(5));

// 输出:
// 圆周率 PI: 3.14159
// 5 的平方是: 25
```

#### 特性2: 命名空间导入 (Namespace Import)
如果你想将一个模块的所有导出都收集到一个对象中，可以使用 `import * as ...` 语法。

```javascript
// 文件: stringUtils.js
export function uppercase(str) { return str.toUpperCase(); }
export function lowercase(str) { return str.toLowerCase(); }

// =========================================

// 文件: main.js
// 将 stringUtils.js 的所有导出都放入名为 'strings' 的对象中
import * as strings from './stringUtils.js';

const text = "JavaScript";
console.log(strings.uppercase(text)); // 输出: JAVASCRIPT
console.log(strings.lowercase(text)); // 输出: javascript
```

#### 特性3: 导入时重命名 (Aliasing)
如果导入的名称与当前作用域的变量名冲突，或者你想要一个更简短的名称，可以使用 `as` 关键字进行重命名。

```javascript
// 文件: logger.js
export function log(message) {
  console.log(`[INFO] ${message}`);
}

// =========================================

// 文件: main.js
// 假设 'log' 这个名字已经被占用了
const log = '这是一个日志变量';

// 导入时使用 'as' 关键字重命名
import { log as printLog } from './logger.js';

printLog('模块加载成功!');
console.log(log); // 仍然是我们自己定义的变量

// 输出:
// [INFO] 模块加载成功!
// 这是一个日志变量
```

### 🔍 Level 3: 对比学习（避免陷阱）
`import` 语句是静态的，这是它与动态导入 `import()` 的最大区别。

```javascript
// === 错误用法 ===
// ❌ 'import' 声明必须在模块的顶层。它不能在函数、if语句或循环中。
// 这种设计让打包工具可以在编译时就分析出模块依赖关系。

function tryImport() {
  // 下面这行代码会直接导致语法错误 (SyntaxError)
  // import { PI } from './math.js'; 
  console.log('这段代码不会执行');
}
console.log("错误原因：静态import不能在块级作用域或函数内部使用。");


// === 正确用法 ===
// ✅ 'import' 必须写在文件的最外层。

import { PI } from './math.js'; // 假设math.js存在

function calculate(radius) {
  // 在函数内部使用已经导入的绑定
  return 2 * PI * radius;
}
console.log("正确做法：在顶层导入，在任何地方使用。");
console.log('半径为10的圆周长:', calculate(10));

// 如果你确实需要在条件满足时才加载模块，应该使用动态导入 `import()`，
// 这将在后续的 "动态导入" 章节中详细讲解。
```

### 🚀 Level 4: 实战应用（真实场景）
**场景：🎮 游戏场景 - 组装你的战斗机器人！**

我们将从不同的模块导入机器人的各个部件（CPU、装甲、武器），然后在主程序中将它们组装起来。

```javascript
// 文件: parts/cpu.js
export default function createCPU(cores) {
  console.log(`⚙️ 安装 ${cores} 核 CPU...`);
  return { type: 'CPU', cores };
}

// 文件: parts/armor.js
export const standardArmor = { type: '装甲', defense: 50 };
export const heavyArmor = { type: '重型装甲', defense: 100 };

// 文件: parts/weapons.js
export function laser() { return { type: '武器', name: '激光炮', damage: 30 }; }
export function rocket() { return { type: '武器', name: '火箭发射器', damage: 75 }; }

// =========================================

// 文件: robotBuilder.js
// 混合使用默认导入、命名导入和命名空间导入
import createCPU from './parts/cpu.js';
import { heavyArmor } from './parts/armor.js';
import * as weapons from './parts/weapons.js';

class Robot {
  constructor(name) {
    this.name = name;
    this.parts = [];
    console.log(`🤖 开始建造机器人: ${name}`);
  }

  addPart(part) {
    this.parts.push(part);
  }

  report() {
    console.log(`
📊 机器人 ${this.name} 建造完成，规格如下:`);
    this.parts.forEach(part => {
      console.log(`- ${part.type}:`, JSON.stringify(part));
    });
  }
}

const terminator = new Robot('终结者T-800');
terminator.addPart(createCPU(8));
terminator.addPart(heavyArmor);
terminator.addPart(weapons.laser());
terminator.addPart(weapons.rocket());
terminator.report();

// 输出:
// 🤖 开始建造机器人: 终结者T-800
// ⚙️ 安装 8 核 CPU...
//
// 📊 机器人 终结者T-800 建造完成，规格如下:
// - CPU: {"type":"CPU","cores":8}
// - 重型装甲: {"type":"重型装甲","defense":100}
// - 武器: {"type":"武器","name":"激光炮","damage":30}
// - 武器: {"type":"武器","name":"火箭发射器","damage":75}
```

### 💡 记忆要点
- **静态执行**：`import` 语句在代码执行前处理，必须写在文件的顶层。
- **导入类型**：支持默认导入（`import name from ...`）、命名导入（`import {a, b} from ...`）和命名空间导入（`import * as name from ...`）。
- **只读引用**：通过 `import` 导入的变量是只读的，不能重新赋值。它们是原始模块中导出值的实时引用。

<!--
metadata:
  syntax: ["import", "named-import", "default-import", "namespace-import", "as"]
  pattern: ["module-pattern"]
  api: []
  concept: ["modules", "es-modules", "static-import", "bindings"]
  difficulty: intermediate
  dependencies: ["js-sec-7-2-1"]
  related: ["js-sec-7-2-1", "js-sec-7-2-3", "js-sec-7-2-4"]
-->
