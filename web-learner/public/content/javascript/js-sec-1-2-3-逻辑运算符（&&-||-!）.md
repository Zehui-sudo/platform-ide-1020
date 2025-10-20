## 逻辑运算符（&&/||/!）

### 🎯 核心概念
逻辑运算符就像是代码世界里的“决策大脑”，它能将多个条件组合起来，判断最终结果是“真”还是“假”，从而让程序根据复杂的状况做出正确的选择。

### 📚 Level 1: 基础认知（30秒理解）
想象一下，你决定是否出门。
- `&&` (与): **必须同时满足**所有条件。比如：天气晴朗 **并且** 你有空。
- `||` (或): **只需满足一个**条件即可。比如：外面在下雨 **或者** 你想宅家。
- `!` (非): **颠倒是非**。比如：你 **不** 是学生。

```javascript
// Level 1: 基础认知

// && (与): 两个都为 true, 结果才是 true
const isSunny = true;
const haveTime = true;
const canGoOut = isSunny && haveTime;
console.log(`天气晴朗并且我有空吗? ${canGoOut}`); // 输出: true

// || (或): 只要有一个为 true, 结果就是 true
const isRaining = false;
const wantToStayHome = true;
const willStayHome = isRaining || wantToStayHome;
console.log(`下雨了或者我想宅家吗? ${willStayHome}`); // 输出: true

// ! (非): 取反
const isStudent = false;
const isNotStudent = !isStudent;
console.log(`我不是学生吗? ${isNotStudent}`); // 输出: true
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 短路求值 (Short-circuit Evaluation)
逻辑运算符并不会总是计算所有条件，它们很“聪明”，一旦能确定最终结果，就会立刻停止计算。

- `&&` (与): 从左到右，遇到第一个 `false` 或“假值”（如`0`, `null`, `""`）就立刻停止，并返回这个假值。如果所有都为真，则返回最后一个值。
- `||` (或): 从左到右，遇到第一个 `true` 或“真值”（任何非假值）就立刻停止，并返回这个真值。如果所有都为假，则返回最后一个值。

```javascript
// 特性1: 短路求值

console.log("--- && 短路演示 ---");
// 因为 false 是第一个操作数，JS 知道结果必为 false，
// 所以根本不会去执行后面的 console.log('我不会被打印')
const resultAnd = false && console.log('我不会被打印');
console.log("&& 的结果:", resultAnd); // 输出: false

console.log("\n--- || 短路演示 ---");
// 因为 "你好" 是一个“真值”，JS 知道结果必为 true，
// 所以它立刻返回 "你好"，后面的代码同样不会执行。
const resultOr = "你好" || console.log('我也不会被打印');
console.log("|| 的结果:", resultOr); // 输出: "你好"
```

#### 特性2: 返回值不一定是布尔值
逻辑运算符的返回值是决定整个表达式结果的那个**操作数的值**，而不一定是 `true` 或 `false`。这个特性经常被用来设置默认值。

```javascript
// 特性2: 返回值不一定是布尔值

// 场景: 用户名可能为空，如果为空，我们提供一个默认值
let userName = ""; // 用户名为空字符串，这是一个“假值”
let defaultName = "游客";
// userName 是假值，所以 || 运算会继续，并返回后面的 "游客"
let displayName = userName || defaultName;
console.log(`欢迎你, ${displayName}!`); // 输出: 欢迎你, 游客!

// 如果用户名不为空
let realUserName = "Alice"; // 这是一个“真值”
// realUserName 是真值，|| 运算发生“短路”，直接返回 "Alice"
let welcomeMessage = realUserName || defaultName;
console.log(`欢迎你, ${welcomeMessage}!`); // 输出: 欢迎你, Alice!

// && 的例子：只有当用户已登录，才显示欢迎信息
const isLoggedIn = true;
const userProfile = { name: "Bob" };
// isLoggedIn 是真值，所以 && 运算继续，并返回后面的 userProfile.name
const greeting = isLoggedIn && userProfile.name;
console.log(`问候语: ${greeting}`); // 输出: 问候语: Bob
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个非常常见的错误是试图用数学中的方式来判断一个数字是否在某个区间内。

```javascript
// Level 3: 对比学习

const score = 75;

console.log("=== 错误用法 ===");
// ❌ 错误: 这种写法在 JavaScript 中不会按预期工作
// 它会先计算 60 < score (结果是 true)，然后计算 true < 90。
// 在比较中，true会被转换为1，所以表达式变成了 1 < 90，结果是 true。
// 即使 score 是 100，60 < 100 (true)，true < 90 (true)，结果依然是 true，这显然是错的。
const isGoodScoreWrong = 60 < score < 90;
console.log(`分数 ${score} 在 60 到 90 之间吗? (错误方式): ${isGoodScoreWrong}`);
// 让我们用一个边界外的分数测试
const anotherScore = 120;
const isGoodScoreWrong2 = 60 < anotherScore < 90;
console.log(`分数 ${120} 在 60 到 90 之间吗? (错误方式): ${isGoodScoreWrong2}`); // 结果仍然是 true!

console.log("\n=== 正确用法 ===");
// ✅ 正确: 必须使用逻辑与 && 将两个独立的比较连接起来
// 检查 score > 60 AND score < 90
const isGoodScoreCorrect = score > 60 && score < 90;
console.log(`分数 ${score} 在 60 到 90 之间吗? (正确方式): ${isGoodScoreCorrect}`);
// 用边界外的分数再次测试
const anotherScoreCorrect = 120;
const isGoodScoreCorrect2 = anotherScoreCorrect > 60 && anotherScoreCorrect < 90;
console.log(`分数 ${120} 在 60 到 90 之间吗? (正确方式): ${isGoodScoreCorrect2}`); // 结果是 false，正确！
```

### 🚀 Level 4: 实战应用（真实场景）
**场景：🚀 科幻冒险：星际飞船“探索号”的超光速跳跃前置检查**

作为“探索号”的AI助手，你需要在船长下令进行超光速跳跃前，运行一个安全检查程序。只有所有关键条件都满足，或者在某些紧急情况下满足备用条件，才能安全跳跃。

```javascript
// Level 4: 飞船跳跃安全检查

function checkHyperspaceJump(engineStatus, navComputerOnline, shieldLevel, asteroidsNear, isDocked) {
  console.log("--- 开始进行超光速跳跃前置检查 ---");
  console.log(`引擎状态: ${engineStatus} | 导航系统: ${navComputerOnline ? '在线' : '离线'} | 护盾: ${shieldLevel}% | 附近有小行星: ${asteroidsNear ? '是' : '否'} | 是否已停靠: ${isDocked ? '是' : '否'}`);

  // 核心安全条件：引擎必须'stable'，并且导航电脑必须在线
  const coreSystemsOK = engineStatus === 'stable' && navComputerOnline;
  if (!coreSystemsOK) {
    console.log("❌ 跳跃取消！核心系统未就绪（引擎或导航问题）。");
    return;
  }
  
  // 危险规避条件：护盾必须是满的(100) 或者 附近没有小行星
  const hazardAvoidanceOK = shieldLevel === 100 || !asteroidsNear;
  if (!hazardAvoidanceOK) {
    console.log("❌ 跳跃取消！危险规避系统警告（护盾未满且附近有小行星）。");
    return;
  }
  
  // 最终状态检查：飞船不能处于停靠状态
  const finalStateOK = !isDocked;
  if (!finalStateOK) {
    console.log("❌ 跳跃取消！飞船仍在空间站停靠，请先脱离。");
    return;
  }
  
  // 综合所有条件进行最终判断
  if (coreSystemsOK && hazardAvoidanceOK && finalStateOK) {
    console.log("✅ 所有检查通过！引力驱动器正在充能...准备进行超光速跳跃！🚀✨");
  } else {
    // 理论上，上面的if判断已经覆盖了所有失败情况，但作为保险措施
    console.log("❌ 未知错误，跳跃程序中止。");
  }
}

// 场景1: 一切完美，准备出发！
checkHyperspaceJump('stable', true, 100, false, false);

console.log("\n========================================\n");

// 场景2: 护盾不满，但周围安全，也可以跳跃
checkHyperspaceJump('stable', true, 80, false, false);

console.log("\n========================================\n");

// 场景3: 导航系统离线，跳跃失败
checkHyperspaceJump('stable', false, 100, false, false);
```

### 💡 记忆要点
- **`&&` (与)**：一假即假。像一个严格的考官，所有科目都及格才算通过。
- **`||` (或)**：一真即真。像一个宽容的考官，只要有一门课及格就算通过。
- **短路特性**：`&&` 遇到假值停，`||` 遇到真值停，这个特性不仅能提高效率，还能用于编写简洁的代码（如设置默认值）。

<!--
metadata:
  syntax: ["let", "const", "function"]
  pattern: ["error-handling"]
  api: ["console.log"]
  concept: ["boolean-logic", "short-circuiting", "truthy-falsy"]
  difficulty: basic
  dependencies: []
  related: []
-->