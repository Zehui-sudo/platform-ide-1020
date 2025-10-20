好的，作为一名专业的JavaScript教育专家，我将为你生成关于“默认参数与剩余参数”的学习内容。

---

## 默认参数与剩余参数

### 🎯 核心概念
默认参数与剩余参数增强了JavaScript函数的灵活性，它们允许我们为函数参数设置备用值（默认参数），以及将不确定数量的参数收集到一个数组中进行处理（剩余参数），让函数定义更清晰、调用更方便。

### 📚 Level 1: 基础认知（30秒理解）
```javascript
// === 默认参数 (Default Parameters) ===
// 当调用函数时没有提供某个参数，它会使用默认值
function greet(name = '神秘的朋友') {
  console.log(`你好, ${name}!`);
}

greet('爱丽丝'); // 输出: 你好, 爱丽丝!
greet();       // 输出: 你好, 神秘的朋友!


// === 剩余参数 (Rest Parameters) ===
// 使用 ... 将多个独立的参数“打包”成一个数组
function sumAll(...numbers) {
  // `numbers` 是一个真正的数组，可以使用数组方法
  let total = numbers.reduce((acc, current) => acc + current, 0);
  console.log(`传入的数字是: [${numbers}]`);
  console.log(`它们的总和是: ${total}`);
}

sumAll(1, 2, 3);       // 输出: 传入的数字是: [1,2,3]  它们的总和是: 6
sumAll(10, 20, 30, 40); // 输出: 传入的数字是: [10,20,30,40]  它们的总和是: 100
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 默认参数可以是表达式或函数调用
默认值不是在函数定义时计算的，而是在函数被调用且参数未提供时才实时计算。

```javascript
// 一个简单的函数，用来返回当前时间戳
function getDefaultTimestamp() {
  console.log('正在获取默认时间...');
  return Date.now();
}

// `createdAt` 的默认值是一个函数调用
function createLogEntry(message, createdAt = getDefaultTimestamp()) {
  console.log(`日志: "${message}" 创建于 ${createdAt}`);
}

// 第一次调用，提供了第二个参数，所以默认函数不会执行
createLogEntry('用户登录成功', 1678886400000);
// -> 日志: "用户登录成功" 创建于 1678886400000

console.log('--- 分割线 ---');

// 第二次调用，未提供第二个参数，默认函数被执行
// 为了看到效果，我们等一秒再调用
setTimeout(() => {
  createLogEntry('用户上传了文件');
  // -> 正在获取默认时间...
  // -> 日志: "用户上传了文件" 创建于 [当前的时间戳]
}, 1000);
```

#### 特性2: 剩余参数必须是最后一个参数
剩余参数 (`...`) 用于收集所有“剩下”的参数，因此它在逻辑上和语法上都必须是函数参数列表的最后一位。

```javascript
// 正确用法：...players 是最后一个参数
function createTeam(captain, coach, ...players) {
  console.log(`队长: ${captain}`);
  console.log(`教练: ${coach}`);
  console.log(`队员名单: ${players.join(', ')}`);
  console.log(`队员人数: ${players.length}`);
}

createTeam('梅西', '斯卡洛尼', '马丁内斯', '迪马利亚', '阿尔瓦雷斯');
// 输出:
// 队长: 梅西
// 教练: 斯卡洛尼
// 队员名单: 马丁内斯, 迪马利亚, 阿尔瓦雷斯
// 队员人数: 3

// 如果尝试将剩余参数放在前面，会直接导致语法错误 (SyntaxError)。
// 下面的代码无法运行，仅作展示：
// function createTeamWrong(...players, captain, coach) {
//   // Uncaught SyntaxError: Rest parameter must be last formal parameter
// }
```

### 🔍 Level 3: 对比学习（避免陷阱）
在ES6之前，我们常用 `||` 操作符来模拟默认参数，但这存在一个陷阱：它会错误地处理所有“假值”（falsy values），如 `0`, `''`, `false`。

```javascript
// 假设我们要为一个游戏角色设置音量
// 音量可以是 0 到 100 之间的数字

console.log("=== 错误用法 (使用 ||) ===");
// ❌ 这种老方法会把有效的“假值”当作未提供
function setVolumeOld(level) {
  const finalLevel = level || 50; // 如果 level 是 0, '' or false, 就会变成 50
  console.log(`[旧方法] 当前音量: ${finalLevel}`);
}

setVolumeOld(80); // 正常工作 -> [旧方法] 当前音量: 80
setVolumeOld();   // 正常工作 -> [旧方法] 当前音量: 50
setVolumeOld(0);  // ❌ 错误！我们想设置音量为0，但它变成了50！
setVolumeOld(''); // ❌ 错误！空字符串也被当成了50！


console.log("\n=== 正确用法 (使用 ES6 默认参数) ===");
// ✅ ES6 默认参数只在参数值为 `undefined` 时生效
function setVolumeNew(level = 50) {
  console.log(`[新方法] 当前音量: ${level}`);
}

setVolumeNew(80); // 正常工作 -> [新方法] 当前音量: 80
setVolumeNew();   // 正常工作 -> [新方法] 当前音量: 50
setVolumeNew(0);  // ✅ 正确！音量被成功设置为 0
setVolumeNew(''); // ✅ 正确！音量被成功设置为空字符串
```

### 🚀 Level 4: 实战应用（真实场景）

**场景：🎨 创意互动 - 表情符号生成器**

让我们创建一个有趣的函数，它可以根据你提供的一系列“零件”来组装一个独一无二的表情符号。这个场景非常适合默认参数（提供默认的五官）和剩余参数（添加任意数量的装饰品）。

```javascript
/**
 * 表情符号生成器
 * @param {string} eyes - 眼睛样式，默认为 'o o'
 * @param {string} mouth - 嘴巴样式，默认为 '-'
 * @param {...string} decorations - 任意数量的装饰品，如帽子、胡子等
 */
function createEmoji(eyes = 'o o', mouth = '-', ...decorations) {
  console.log(`🎨 开始制作表情...`);
  console.log(`眼睛: ${eyes}, 嘴巴: ${mouth}`);

  // 检查是否有装饰品
  if (decorations.length === 0) {
    console.log('没有添加任何装饰品。');
  } else {
    console.log(`收到了 ${decorations.length} 个装饰品: ${decorations.join(', ')}`);
  }

  // 组装最终的表情符号
  // 将所有装饰品放在表情的上方和下方
  const topDecorations = decorations.slice(0, Math.ceil(decorations.length / 2)).join(' ');
  const bottomDecorations = decorations.slice(Math.ceil(decorations.length / 2)).join(' ');

  const emoji = `
    ${topDecorations}
   ( ${eyes} )
      ${mouth}
    ${bottomDecorations}
  `;

  console.log('✨ 你的专属表情符号诞生了！✨');
  console.log(emoji);
  return emoji;
}

// 1. 使用所有默认参数
console.log('--- 案例1: 基础款 ---');
createEmoji();

// 2. 自定义眼睛和嘴巴，不加装饰
console.log('\n--- 案例2: 开心款 ---');
createEmoji('^ ^', 'U');

// 3. 使用默认五官，但加上一堆装饰品
console.log('\n--- 案例3: 派对款 ---');
createEmoji(undefined, undefined, '🎉', '🎩', '🥳', '✨'); // 使用 undefined 来跳过并使用默认值

// 4. 完全自定义
console.log('\n--- 案例4: 海盗款 ---');
createEmoji('@ o', 'J', '🏴‍☠️', '⚔️');
```

### 💡 记忆要点
- **要点1**：默认参数 `(param = defaultValue)` 仅在传入的参数是 `undefined` 时生效，对 `null`, `0`, `''` 等假值无效。
- **要点2**：剩余参数 `(...args)` 将函数调用时末尾的所有参数收集到一个真正的数组中，方便使用 `map`, `filter` 等数组方法。
- **要点3**：剩余参数必须是函数参数列表中的最后一个，一个函数最多只能有一个剩余参数。

<!--
metadata:
  syntax: [function, arrow-function]
  pattern: []
  api: [console.log, Array.reduce, Array.join, Array.slice]
  concept: [default-parameters, rest-parameters, arguments-object, falsy-values]
  difficulty: intermediate
  dependencies: [无]
  related: []
-->