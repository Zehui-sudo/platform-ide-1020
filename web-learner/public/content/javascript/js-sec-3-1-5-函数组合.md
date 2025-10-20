## 函数组合

### 🎯 核心概念
函数组合是一种将多个简单函数合并成一个更复杂函数的技术，它就像建立一条数据处理的“流水线”，前一个函数的输出会成为后一个函数的输入，从而实现清晰、可复用、可维护的代码逻辑。

### 📚 Level 1: 基础认知（30秒理解）
想象一下，我们有两个简单的任务：先把一个数字加倍，然后再给结果加1。我们可以把这两个任务（函数）嵌套起来，这就是最基础的函数组合。

```javascript
// 任务1: 将数字加倍
const double = (x) => x * 2;

// 任务2: 将数字加1
const addOne = (x) => x + 1;

// 初始数字
const initialNumber = 5;

// 最基础的函数组合：将 double 的结果作为 addOne 的输入
const result = addOne(double(initialNumber));

console.log(`对数字 ${initialNumber} 执行加倍再加一的操作，结果是: ${result}`);
// 预期输出: 对数字 5 执行加倍再加一的操作，结果是: 11
```

### 📈 Level 2: 核心特性（深入理解）
为了更优雅、更通用地组合函数，我们可以创建专门的辅助函数。

#### 特性1: 创建可复用的 `compose` 辅助函数
我们可以编写一个 `compose` 函数，它接收任意数量的函数作为参数，并返回一个新的函数。这个新函数会从右到左依次执行传入的函数。

```javascript
// compose 辅助函数，它接收多个函数，并从右向左组合它们
// (...fns) => (initialValue) => ... 这是一个高阶函数的写法
const compose = (...fns) => (initialValue) => fns.reduceRight((acc, fn) => fn(acc), initialValue);

// 定义一些简单的功能函数
const toUpperCase = (str) => str.toUpperCase();
const exclaim = (str) => `${str}!`;
const greet = (name) => `Hello, ${name}`;

// 使用 compose 将三个函数组合成一个新的函数
const loudGreeting = compose(exclaim, toUpperCase, greet);

// 调用新生成的函数
const result = loudGreeting('Alice');

console.log(result);
// 预期输出: HELLO, ALICE!
// 执行顺序: greet('Alice') -> 'Hello, Alice'
//          toUpperCase('Hello, Alice') -> 'HELLO, ALICE'
//          exclaim('HELLO, ALICE') -> 'HELLO, ALICE!'
```

#### 特性2: 数据处理流水线 (Pipeline)
与从右到左的 `compose` 相对，有时从左到右的执行顺序更符合阅读习惯，我们称之为 `pipe`（管道）。它的实现与 `compose` 类似，只是将 `reduceRight` 换成 `reduce`。

```javascript
// pipe 辅助函数，从左向右组合函数
const pipe = (...fns) => (initialValue) => fns.reduce((acc, fn) => fn(acc), initialValue);

// 定义一系列数学运算函数
const add5 = (x) => x + 5;
const multiplyBy3 = (x) => x * 3;
const subtract10 = (x) => x - 10;

// 使用 pipe 创建一个计算流水线
// 阅读顺序与执行顺序一致：先+5，再*3，最后-10
const calculate = pipe(add5, multiplyBy3, subtract10);

const initialValue = 10;
const result = calculate(initialValue);

console.log(`计算流水线: ((${initialValue} + 5) * 3) - 10 = ${result}`);
// 预期输出: 计算流水线: ((10 + 5) * 3) - 10 = 35
```

### 🔍 Level 3: 对比学习（避免陷阱）
函数组合的强大之处在于函数的输出与下一个函数的输入能够完美衔接。如果数据类型不匹配，流水线就会“堵塞”。

```javascript
// 定义一些处理不同数据类型的函数
const splitString = (str) => str.split(' '); // 输入: string, 输出: array
const countItems = (arr) => arr.length;      // 输入: array, 输出: number
const isEven = (num) => num % 2 === 0;       // 输入: number, 输出: boolean

// pipe 辅助函数，从左向右组合
const pipe = (...fns) => (initialValue) => fns.reduce((acc, fn) => fn(acc), initialValue);

console.log("=== 错误用法 ===");
// ❌ 错误地组合了函数，countItems 的输出是 number，但 splitString 需要 string
try {
    const wrongCombination = pipe(countItems, splitString);
    wrongCombination(['hello', 'world']);
} catch (error) {
    console.log("出错了:", error.message);
    console.log("原因: countItems返回一个数字，但splitString需要一个字符串作为输入，导致 .split() 方法不存在而出错。");
}


console.log("\n=== 正确用法 ===");
// ✅ 正确的组合，确保前一个函数的输出类型是后一个函数的期望输入类型
const processSentence = pipe(splitString, countItems, isEven);

const sentence1 = "this is a sample sentence"; // 6个单词
const sentence2 = "another one"; // 2个单词

const result1 = processSentence(sentence1);
const result2 = processSentence(sentence2);

console.log(`句子 "${sentence1}" 的单词数是偶数吗? ${result1}`);
console.log(`句子 "${sentence2}" 的单词数是偶数吗? ${result2}`);
// 预期输出:
// 句子 "this is a sample sentence" 的单词数是偶数吗? true
// 句子 "another one" 的单词数是偶数吗? true
```

### 🚀 Level 4: 实战应用（真实场景）
#### 🎨 创意互动：ASCII 艺术角色生成器

让我们用函数组合来创建一个有趣的ASCII艺术角色生成器。每个函数都是一个“装备”或“部件”，我们可以自由组合它们来创造独一无二的角色！

```javascript
// compose 辅助函数，从右向左组合
const compose = (...fns) => (initialValue) => fns.reduceRight((acc, fn) => fn(acc), initialValue);

// --- 角色部件函数 (每个函数都接收一个字符串数组并返回一个新的字符串数组) ---

// 添加头部
const addHead = (character) => ['  O  ', ...character];

// 添加身体
const addBody = (character) => [...character, ' /|\\ ', '  |  '];

// 添加腿部
const addLegs = (character) => [...character, ' / \\ '];

// 穿上盔甲
const addArmor = (character) => {
    character[1] = ' /|█|\\'; // 替换身体部分
    character[2] = '  █  ';
    return character;
};

// 拿起宝剑
const addSword = (character) => {
    character[0] = '  O  <-- Master Sword!';
    character[1] = ' /|█|\\o'; // 手持剑
    return character;
};

// 戴上巫师帽
const addWizardHat = (character) => {
    character[0] = '  ^  '; // 帽子
    character[1] = ' (O) '; // 戴帽子的头
    return character;
};

// --- 角色创建流水线 ---

// 创建一个基础村民
const createVillager = compose(addLegs, addBody, addHead);

// 创建一个全副武装的骑士
const createKnight = compose(addSword, addArmor, addLegs, addBody, addHead);

// 创建一个神秘的巫师
const createWizard = compose(addWizardHat, addLegs, addBody, addHead);

// --- 开始生成！ ---

// 初始状态是一个空的角色画布（一个空数组）
const emptyCanvas = [];

console.log("--- 生成一个村民 ---");
const villager = createVillager(emptyCanvas);
console.log(villager.join('\n'));

console.log("\n--- 生成一个骑士 ---");
const knight = createKnight(emptyCanvas);
console.log(knight.join('\n'));

console.log("\n--- 生成一个巫师 ---");
const wizard = createWizard(emptyCanvas);
console.log(wizard.join('\n'));

/*
预期输出:

--- 生成一个村民 ---
  O  
 /|\ 
  |  
 / \ 

--- 生成一个骑士 ---
  O  <-- Master Sword!
 /|█|\o
  █  
 / \ 

--- 生成一个巫师 ---
  ^  
 (O) 
 /|\ 
  |  
 / \ 

*/
```

### 💡 记忆要点
- **流水线思维**：函数组合就是创建一条数据处理流水线，每个函数是流水线上的一个工序。
- **执行顺序**：`compose` 通常从右到左执行，`pipe` 从左到右执行，选择更符合你阅读习惯的方式。
- **函数纯粹性**：函数组合最适用于“纯函数”（输入相同，输出永远相同，且无副作用），这使得代码行为可预测且易于测试。

<!--
metadata:
  syntax: ["function", "arrow-function"]
  pattern: ["closure", "functional-programming"]
  api: ["Array.reduce", "Array.reduceRight", "console.log"]
  concept: ["function-composition", "pure-function", "higher-order-function"]
  difficulty: advanced
  dependencies: []
  related: []
-->