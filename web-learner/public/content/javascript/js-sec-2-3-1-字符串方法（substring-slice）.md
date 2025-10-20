好的，作为一名专业的JavaScript教育专家，我将为您生成关于“字符串方法（substring/slice）”的学习内容。

---

## 字符串方法（substring/slice）

### 🎯 核心概念
`substring` 和 `slice` 都是用来从一个字符串中“切割”或“提取”出一部分新字符串的工具，它们让我们能够精确地获取字符串的某个片段，而无需改变原始字符串。

### 📚 Level 1: 基础认知（30秒理解）
想象一下，你有一把尺子和一根长长的面包。`slice` 和 `substring` 就像是你的两把小刀，可以从指定位置开始，到另一个位置结束，切下一块面包。

```javascript
// 假设 "JavaScript" 是我们的长面包
const message = "Hello, JavaScript!";

// 使用 slice 从索引 7 的位置切到索引 17 的位置（不包含17）
// J(7) a(8) v(9) a(10) S(11) c(12) r(13) i(14) p(15) t(16)
const slicedPart = message.slice(7, 17);
console.log("使用 slice 切出的部分:", slicedPart); // 输出: JavaScript

// 使用 substring 也可以做到同样的事情
const subPart = message.substring(7, 17);
console.log("使用 substring 切出的部分:", subPart); // 输出: JavaScript
```

### 📈 Level 2: 核心特性（深入理解）
虽然它们在基础用法上很相似，但在处理特殊参数时，它们的行为有很大差异。

#### 特性1: 对负数索引的处理
这是 `slice` 和 `substring` 最核心的区别。`slice` 支持从后往前数，而 `substring` 会将负数视为0。

```javascript
const greeting = "Welcome to the future!";

// --- slice 的表现 ---
// slice(-1) 表示从倒数第1个字符开始切到末尾
const sliceNegative = greeting.slice(-7);
console.log("slice(-7):", sliceNegative); // 输出: future!

// --- substring 的表现 ---
// substring 会将所有负数参数都当作 0
const substringNegative = greeting.substring(-7); // 相当于 greeting.substring(0)
console.log("substring(-7):", substringNegative); // 输出: Welcome to the future!

const substringNegative2 = greeting.substring(0, -1); // 相当于 greeting.substring(0, 0)
console.log("substring(0, -1):", substringNegative2); // 输出: "" (空字符串)
```

#### 特性2: 起始和结束位置颠倒
如果你的起始位置大于结束位置，它们俩的处理方式也不同。`substring` 会“智能”地交换它们，而 `slice` 会直接返回一个空字符串。

```javascript
const code = "CODE-12345-FINISH";

// --- substring 的表现 ---
// substring(11, 5) 会被自动纠正为 substring(5, 11)
const subSwapped = code.substring(11, 5);
console.log("substring(11, 5) [自动交换]:", subSwapped); // 输出: 12345

// --- slice 的表现 ---
// slice(11, 5) 的起始位置在结束位置之后，无法切割，所以返回空
const sliceSwapped = code.slice(11, 5);
console.log("slice(11, 5) [不交换]:", sliceSwapped); // 输出: "" (空字符串)
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个常见的陷阱是混淆这两种方法对负数参数的处理，导致得到意想不到的结果。

```javascript
const phrase = "The early bird catches the worm.";

console.log("=== 错误用法 ===");
// ❌ 目标：想获取最后4个字符 "worm"
// 错误地认为 substring 也支持负数索引
const wrongResult = phrase.substring(-5, -1);
console.log('以为 substring(-5, -1) 能获取 "worm"，结果是:', `"${wrongResult}"`);
// 解释: substring 将 -5 和 -1 都视为 0，变成了 substring(0, 0)，所以返回了空字符串。

console.log("\n=== 正确用法 ===");
// ✅ 正确做法：使用 slice 来处理负数索引
const correctResultSlice = phrase.slice(-5, -1);
console.log('使用 slice(-5, -1) 获取 "worm"，结果是:', `"${correctResultSlice}"`);
// 解释: slice(-5) 从倒数第5个字符('w')开始，slice(-1) 在倒数第1个字符('.')结束（不包含）。

// ✅ 另一种正确做法：如果必须用 substring，需要计算出正数索引
const correctResultSubstring = phrase.substring(phrase.length - 5, phrase.length - 1);
console.log('使用 substring(28, 32) 获取 "worm"，结果是:', `"${correctResultSubstring}"`);
// 解释: 通过计算长度，我们得到了正确的正数索引，但显然 slice 更方便。
```

### 🚀 Level 4: 实战应用（真实场景）

**🚀 科幻冒险：解码来自半人马座α星的信号**

我们收到了一个神秘的外星信号！信号是一长串加密数据，情报部门告诉我们，关键信息隐藏在信号的特定片段中。你的任务是编写一个解码器来提取这些信息。

```javascript
function decodeAlphaCentauriSignal(signal) {
  console.log("解码器启动... 正在分析信号:", signal);
  console.log("-------------------------------------------");

  // 任务1: 提取“来源星球”代码 (信号的前5个字符)
  // 使用 substring，因为我们明确知道是从 0 开始的
  const planetCode = signal.substring(0, 5);
  console.log(`[来源分析] 信号来源代码: ${planetCode} (解码为: 半人马座α星b)`);

  // 任务2: 提取“信息优先级” (信号的最后3个字符)
  // 这种从末尾提取的场景，slice 的负数索引是最佳选择！
  const priorityLevel = signal.slice(-3);
  console.log(`[优先级分析] 信息紧急程度: ${priorityLevel} (解码为: 最高级别)`);

  // 任务3: 提取核心信息 (从第8个字符开始，到倒数第5个字符结束)
  // 再次使用 slice，因为它能灵活地混合正负索引
  const coreMessage = signal.slice(8, -5);
  console.log(`[核心信息] 破译出的核心内容: "${coreMessage}"`);
  
  console.log("-------------------------------------------");
  console.log("解码完成！外星人说：", `${coreMessage}！`);
}

// 这是一个模拟的加密外星信号
const alienSignal = "AC-b#|GREETINGS_EARTHLINGS|#URG";

// 运行我们的解码器
decodeAlphaCentauriSignal(alienSignal);
```

### 💡 记忆要点
- **要点1**：`slice(start, end)` 和 `substring(start, end)` 都用于提取字符串片段，且不修改原字符串。
- **要点2**：`slice` 是更强大和灵活的选择，因为它支持负数索引（从字符串末尾开始计算）。
- **要点3**：当 `start > end` 时，`substring` 会自动交换两个参数，而 `slice` 会返回空字符串。

<!--
metadata:
  syntax: [const, function]
  pattern: [function-usage]
  api: [String.slice, String.substring, console.log]
  concept: [string-manipulation, indexing, immutability]
  difficulty: basic
  dependencies: [无]
  related: []
-->