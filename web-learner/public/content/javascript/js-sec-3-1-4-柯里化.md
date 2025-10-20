## 柯里化

### 🎯 核心概念
柯里化是一种将接受多个参数的函数，转变为接受一个单一参数（最初函数的第一个参数）的函数，并且返回接受余下参数的新函数的技术。它能让你轻松地部分应用函数，创建出更具体、更可复用的新函数。

### 📚 Level 1: 基础认知（30秒理解）
想象一个加法函数 `add(a, b)`，它一次性接收两个参数。柯里化就是把它变成 `curriedAdd(a)(b)` 的形式，每次只接收一个参数，像是在分步操作。

```javascript
// 传统函数：一次性传入所有参数
function add(a, b) {
  return a + b;
}
console.log(`传统函数调用: add(5, 3) = ${add(5, 3)}`);

// 柯里化函数：分步传入参数
function curriedAdd(a) {
  return function(b) {
    return a + b;
  };
}

// 调用柯里化函数
const addFive = curriedAdd(5); // 得到一个新函数，它会给传入的参数加上5
const result = addFive(3);     // 调用新函数

console.log(`柯里化函数调用: curriedAdd(5)(3) = ${result}`);
console.log(`addFive(10) 的结果是: ${addFive(10)}`);
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 参数的延迟执行与部分应用 (Partial Application)
柯里化最大的魅力在于可以固定一个或多个参数，生成一个更具体的新函数。这就像是模板，你先设置好一部分，剩下的部分以后再填。

```javascript
// 一个通用的日志函数
function log(level, time, message) {
  console.log(`[${level}] @ ${time.toTimeString()}: ${message}`);
}

// 手动进行部分应用
function curryLog(level) {
  return function(time) {
    return function(message) {
      console.log(`[${level}] @ ${time.toTimeString()}: ${message}`);
    }
  }
}

// 1. 创建一个专门用于记录“调试”信息的日志函数
const logDebug = curryLog('DEBUG');
// 2. 在未来的某个时间点，用这个专门的函数记录信息
// 我们不需要再每次都传入 'DEBUG'
logDebug(new Date())('用户点击了按钮A');
setTimeout(() => {
  logDebug(new Date())('数据加载完成');
}, 1000);

// 也可以创建其他类型的日志函数
const logError = curryLog('ERROR');
logError(new Date())('API请求失败');
```

#### 特性2: 动态创建函数，提高复用性
通过柯里化，我们可以基于一个通用函数，动态地创建出无数个“定制版”函数，极大地提高了代码的复用性，避免了编写大量相似的函数。

```javascript
// 一个通用的乘法函数
function multiply(a, b) {
  return a * b;
}

// 一个简单的柯里化转换器
function curry(fn) {
  return function curried(...args) {
    // 如果传入的参数数量足够，就直接执行原函数
    if (args.length >= fn.length) {
      return fn.apply(this, args);
    } else {
      // 否则，返回一个新函数，等待接收剩余的参数
      return function(...args2) {
        return curried.apply(this, args.concat(args2));
      }
    }
  };
}

const curriedMultiply = curry(multiply);

// 基于 curriedMultiply 动态创建新函数
const double = curriedMultiply(2); // 创建一个“翻倍”函数
const triple = curriedMultiply(3); // 创建一个“三倍”函数
const tenTimes = curriedMultiply(10); // 创建一个“十倍”函数

console.log("使用'double'函数:", double(5));   // 输出: 10
console.log("使用'triple'函数:", triple(5));   // 输出: 15
console.log("使用'tenTimes'函数:", tenTimes(5)); // 输出: 50
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个常见的误解是，任何返回函数的函数都是柯里化。真正的柯里化函数更加灵活，它允许你一次性传入所有参数，也可以分步传入。

```javascript
// 一个通用的函数，用于格式化消息
function formatMessage(sender, receiver, message) {
  return `From ${sender} to ${receiver}: ${message}`;
}

// 通用的柯里化工具函数
function curry(fn) {
  return function curried(...args) {
    if (args.length >= fn.length) {
      return fn.apply(this, args);
    } else {
      return function(...nextArgs) {
        return curried.apply(this, args.concat(nextArgs));
      };
    }
  };
}


console.log("=== 错误用法 ===");
// ❌ 这是一个“硬编码”的、不灵活的类柯里化函数
function inflexibleCurryFormat(sender) {
  return function(receiver, message) { // 强制要求后面两个参数一起传入
    return formatMessage(sender, receiver, message);
  };
}

const aliceSends = inflexibleCurryFormat("Alice");
// aliceSends("Bob", "Hello!"); // 这样可以工作
// aliceSends("Bob")("Hello!"); // 这样会报错! TypeError: aliceSends(...) is not a function

console.log("❌ 无法分步调用所有参数: inflexibleCurryFormat('Alice')('Bob')('Hello!') 会导致 TypeError");
console.log("这种方式限制了函数的组合能力，不够灵活。");


console.log("\n=== 正确用法 ===");
// ✅ 使用通用的柯里化函数，它非常灵活
const curriedFormat = curry(formatMessage);

// 我们可以根据需要，以任何组合方式传递参数
const msg1 = curriedFormat("Alice", "Bob", "Hello!"); // 1. 一次性调用
const msg2 = curriedFormat("Alice")("Bob", "Hello!"); // 2. 分步调用
const msg3 = curriedFormat("Alice", "Bob")("Hello!"); // 3. 混合调用

const aliceSendsFlexible = curriedFormat("Alice");
const aliceToBob = aliceSendsFlexible("Bob");
const msg4 = aliceToBob("See you tomorrow!"); // 4. 创建多个中间函数

console.log("✅ 一次性调用:", msg1);
console.log("✅ 完全分步调用:", msg2);
console.log("✅ 混合调用:", msg3);
console.log("✅ 创建中间函数后调用:", msg4);
console.log("正确的柯里化提供了极大的灵活性，方便函数组合和复用。");
```

### 🚀 Level 4: 实战应用（真实场景）
**场景：🍕 披萨配料计算器**

想象一下，你正在开发一个披萨店的点餐页面。顾客可以选择不同尺寸的披萨，并添加各种配料。每种尺寸的基础价格不同，每种配料的价格也不同。我们可以用柯里化来优雅地处理价格计算。

```javascript
// 通用的柯里化工具函数
function curry(fn) {
  return function curried(...args) {
    if (args.length >= fn.length) {
      return fn.apply(this, args);
    } else {
      return function(...nextArgs) {
        return curried.apply(this, args.concat(nextArgs));
      };
    }
  };
}

/**
 * 基础价格计算函数
 * @param {string} size - 尺寸 ('S', 'M', 'L')
 * @param {Array<string>} toppings - 配料列表
 * @param {number} discount - 折扣 (例如 0.1 表示 10% off)
 * @returns {string} - 最终价格描述
 */
function calculatePizzaPrice(size, toppings, discount) {
  const basePrices = { S: 50, M: 70, L: 90 };
  const toppingPrice = 5; // 每份配料5元

  const basePrice = basePrices[size];
  if (!basePrice) return "无效的尺寸！";

  const toppingsCost = toppings.length * toppingPrice;
  const total = (basePrice + toppingsCost) * (1 - discount);

  return `一个${size}寸披萨，加了[${toppings.join(', ')}]，
  享受${discount * 100}%折扣后，总价: ${total.toFixed(2)}元！🍕`;
}

// 将我们的价格计算函数柯里化
const curriedPriceCalculator = curry(calculatePizzaPrice);

// --- 模拟顾客点餐流程 ---

// 步骤1: 顾客选定了尺寸，我们生成一个“中号披萨”计算器
console.log("👨‍🍳 欢迎光临！请选择您的披萨尺寸。");
const calculateMediumPizza = curriedPriceCalculator('M');
console.log("👍 您选择了中号披萨，现在请添加配料。");

// 步骤2: 顾客添加了配料，我们生成一个“中号加了芝士和蘑菇”的计算器
const toppings = ['双倍芝士', '蘑菇', '青椒'];
const mediumPizzaWithToppings = calculateMediumPizza(toppings);
console.log(`👌 配料已添加: [${toppings.join(', ')}]，正在为您计算价格...`);

// 步骤3: 应用不同的折扣
console.log("\n--- 应用不同折扣 ---");
const studentDiscount = 0.1; // 学生9折
const vipDiscount = 0.2;     // VIP 8折

const finalPriceForStudent = mediumPizzaWithToppings(studentDiscount);
const finalPriceForVIP = mediumPizzaWithToppings(vipDiscount);

console.log("🎓 学生优惠价:", finalPriceForStudent);
console.log("🌟 VIP会员价:", finalPriceForVIP);
```

### 💡 记忆要点
- **要点1**：柯里化是将 `f(a, b, c)` 转换为 `f(a)(b)(c)` 的过程，让函数可以分步接收参数。
- **要点2**：核心优势是“部分应用”，即固定一个或多个参数，生成一个功能更具体的新函数。
- **要点3**：真正的柯里化实现是灵活的，既支持 `f(a,b,c)` 也支持 `f(a)(b)(c)`，这让它在函数组合时非常强大。

<!--
metadata:
  syntax: ["function", "arrow-function", "...rest"]
  pattern: ["closure", "higher-order-function"]
  api: ["console.log", "Function.length", "Array.concat", "Function.apply"]
  concept: ["closure", "higher-order-function", "partial-application", "currying"]
  difficulty: advanced
  dependencies: []
  related: []
-->