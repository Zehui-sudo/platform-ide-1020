好的，作为一名专业的JavaScript教育专家，我将严格按照您的要求生成以下教学内容。

---

## 基本数据类型（number/string/boolean）

### 🎯 核心概念
基本数据类型是JavaScript编程的基石，它们定义了程序可以处理的最基础的数据种类（如数字、文本、逻辑判断），是构建所有复杂程序和逻辑的原子单位。

### 📚 Level 1: 基础认知（30秒理解）
JavaScript有三种最常用的基本数据类型：`number`（数字）、`string`（字符串）和`boolean`（布尔值）。我们可以使用 `typeof` 操作符来查看一个变量的数据类型。

```javascript
// 1. number: 用于表示任何数字，包括整数和浮点数
const userAge = 28;

// 2. string: 用于表示文本，必须用引号（单引号' '或双引号" "）包裹
const userName = "Alice";

// 3. boolean: 用于表示逻辑上的“是”或“非”，只有两个值：true 和 false
const isLoggedIn = true;

console.log("姓名:", userName, "类型:", typeof userName); // string
console.log("年龄:", userAge, "类型:", typeof userAge); // number
console.log("登录状态:", isLoggedIn, "类型:", typeof isLoggedIn); // boolean
```

### 📈 Level 2: 核心特性（深入理解）
深入了解每种类型的特点和常见操作。

#### 特性1: number类型支持各种数学运算
`number` 类型不仅包含整数和带小数的浮点数，还支持所有标准的算术运算。它还有一些特殊值，如 `NaN` (Not a Number)，表示一个无效的数学运算结果。

```javascript
const price = 19.99; // 浮点数
const quantity = 3; // 整数

// 执行数学运算
const total = price * quantity;
console.log(`商品总价: ${total}`);

// 无效运算会得到 NaN
const invalidCalculation = 0 / 0;
console.log(`0除以0的结果是: ${invalidCalculation}`); // NaN
console.log(`NaN的数据类型仍然是: ${typeof invalidCalculation}`); // number
```

#### 特性2: string类型可以使用不同引号并轻松拼接
`string` 可以用单引号、双引号或反引号（`）定义。反引号提供了“模板字符串”功能，可以方便地在字符串中嵌入变量。

```javascript
const platform = 'Web';
const course = "JavaScript";
const welcomeMessage = `欢迎学习 ${platform} ${course} 教程!`; // 使用反引号嵌入变量

console.log("使用单引号:", platform);
console.log("使用双引号:", course);
console.log("使用反引号（模板字符串）:", welcomeMessage);

// 使用 + 号进行字符串拼接
const traditionalMessage = "欢迎学习 " + platform + " " + course + " 教程!";
console.log("使用+号拼接:", traditionalMessage);
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个常见的陷阱是混淆数字和字符串形式的数字，尤其是在使用 `+` 操作符时。

```javascript
// 完整的对比示例，包含所有必要的变量定义
console.log("=== 错误用法 ===");
// ❌ 错误：将数字和字符串数字相加
// 解释：当 `+` 操作符的一侧是字符串时，它会执行字符串拼接，而不是数学加法。
const stringNumber = "50";
const actualNumber = 100;
const wrongSum = stringNumber + actualNumber; 
console.log(`"50" + 100 的结果是: "${wrongSum}"`); // 结果是字符串 "50100"
console.log(`错误结果的类型是: ${typeof wrongSum}`);


console.log("\n=== 正确用法 ===");
// ✅ 正确：在计算前将字符串显式转换为数字
// 解释：使用 `parseInt()` 或 `Number()` 函数将字符串转换为数字，以确保执行数学运算。
const stringToConvert = "50";
const anotherNumber = 100;
// 使用 parseInt() 将字符串转换为整数
const correctSum = parseInt(stringToConvert) + anotherNumber;
console.log(`parseInt("50") + 100 的结果是: ${correctSum}`); // 结果是数字 150
console.log(`正确结果的类型是: ${typeof correctSum}`);
```

### 🚀 Level 4: 实战应用（真实场景）
假设我们正在开发一个简单的电商功能，根据用户年龄和会员状态来判断其是否可以享受青年或长者折扣。

```javascript
/**
 * 检查用户是否有资格享受折扣
 * @param {string} userName - 用户名
 * @param {string} userAgeString - 用户年龄（通常从输入框获取，为字符串类型）
 * @param {boolean} isMember - 用户是否为会员
 */
function checkDiscountEligibility(userName, userAgeString, isMember) {
  console.log(`正在检查用户: ${userName}`);

  // 步骤 1: 将字符串类型的年龄转换为 number 类型
  const age = parseInt(userAgeString);

  // 步骤 2: 使用 boolean 和 number 类型进行逻辑判断
  // 青年折扣条件：18-24岁 且 是会员
  const isYouth = age >= 18 && age <= 24;
  // 长者折扣条件：65岁及以上 且 是会员
  const isSenior = age >= 65;
  
  let finalMessage = "";

  // 步骤 3: 根据布尔判断结果，生成不同的字符串消息
  if (isMember && (isYouth || isSenior)) {
    finalMessage = `恭喜, ${userName}! 您符合我们的折扣条件。`;
  } else {
    finalMessage = `抱歉, ${userName}, 您暂时不符合我们的特别折扣条件。`;
  }
  
  console.log(finalMessage);
}

// --- 模拟不同用户场景 ---
// 场景1: 符合青年折扣的会员
checkDiscountEligibility("Tom", "22", true);

console.log("---");

// 场景2: 年龄符合但不是会员，无法享受折扣
checkDiscountEligibility("Jerry", "70", false);

console.log("---");

// 场景3: 不符合年龄条件的会员
checkDiscountEligibility("Mary", "35", true);
```

### 💡 记忆要点
- **`number` 用于数学计算**：它包括整数和浮点数，是进行算术运算的基础。
- **`string` 用于表示文本**：必须用引号包裹，使用 `+` 或模板字符串 `` `${}` `` 来组合文本。
- **`boolean` 用于逻辑决策**：只有 `true` 和 `false` 两个值，是 `if` 语句等条件控制的核心。

<!--
metadata:
  syntax: [const, let, function]
  pattern: [error-handling]
  api: [console.log, typeof, parseInt]
  concept: [data-type, type-coercion]
  difficulty: basic
  dependencies: [无]
  related: [js-sec-1-1-3]
-->