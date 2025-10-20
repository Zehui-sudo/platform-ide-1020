## while/do-while 循环

### 🎯 核心概念
`while` 和 `do-while` 循环用于在**满足特定条件时，重复执行一段代码**。当你不知道具体要循环多少次，只知道循环应该在某个条件变为`false`时停止，它们就非常有用。

### 📚 Level 1: 基础认知（30秒理解）
`while` 循环就像一个警卫，每次进入代码块前都会检查“通行证”（条件）。只有条件为 `true`，才允许执行。

```javascript
// 场景：一个机器人需要充电，直到电量达到3格
let batteryLevel = 0;
console.log("🔋 机器人开始充电...");

// 当电量小于3时，继续循环
while (batteryLevel < 3) {
  batteryLevel = batteryLevel + 1; // 充一格电
  console.log("充电中... 当前电量:", batteryLevel, "格");
}

console.log("✅ 充电完成！机器人满血复活！");
```

### 📈 Level 2: 核心特性（深入理解）
`while` 和 `do-while` 的主要区别在于检查条件的时机。

#### 特性1: `while` vs `do-while` - 先判断 vs 先执行
- **`while`**: 先判断条件，再执行代码。如果条件一开始就是 `false`，循环体一次都不会执行。
- **`do-while`**: 先执行一次代码，再判断条件。无论如何，循环体至少会执行一次。

```javascript
console.log("--- 场景: 门口有保安的派对 ---");

// (1) 使用 while 循环：先检查邀请函
let hasInvitation = false; // 你没有邀请函
console.log("你走向派对门口，保安拦住了你...");

while (hasInvitation) {
  // 这个代码块永远不会执行，因为 hasInvitation 一开始就是 false
  console.log("进入派对，开始狂欢！");
}
console.log("保安：'抱歉，没有邀请函不能进入。' -> while 循环体未执行。");


// (2) 使用 do-while 循环：先进场再查票
let isInsideClub = false;
console.log("\n你走向另一个俱乐部，这里的规矩是先进场...");

do {
  // 这个代码块会先执行一次
  console.log("你溜进了俱乐部，感受了一下气氛！");
  isInsideClub = true; // 假设你进去了
} while (isInsideClub === false); // 然后保安发现你没票，条件为 false，循环结束

console.log("保安：'嘿！你没票！' -> do-while 循环体至少执行了一次。");
```

#### 特性2: `break` - 循环的紧急出口
有时候我们想在循环正常结束前提前跳出，比如找到了我们需要的东西。`break` 关键字可以立即终止循环。

```javascript
// 场景：在一堆箱子里寻找神秘宝藏
let boxesToSearch = 10;
let currentBox = 1;
const treasureBox = 5; // 宝藏在第5个箱子里

console.log("开始寻宝！一共有", boxesToSearch, "个箱子。");

while (currentBox <= boxesToSearch) {
  console.log("正在打开第", currentBox, "个箱子...");
  
  if (currentBox === treasureBox) {
    console.log("💎 找到了！宝藏就在这个箱子里！停止搜索！");
    break; // 找到宝藏，立即跳出 while 循环
  }
  
  currentBox++; // 继续检查下一个箱子
}

console.log("寻宝结束。");
```

### 🔍 Level 3: 对比学习（避免陷阱）
最常见的陷阱是“无限循环”，即循环条件永远为 `true`，导致程序卡死。

```javascript
console.log("=== 错误用法 ===");
// ❌ 错误: 忘记更新循环条件变量
// 这会导致 i 永远是 0， i < 3 永远为 true，循环永不停止。
// 为了防止你的浏览器崩溃，我们用一个“安全阀”来强制退出。
let i = 0;
let safetyCounter = 0;
while (i < 3) {
  console.log("这是一个无限循环的警告！i 的值是:", i);
  // 错误点：没有 i++ 或任何改变 i 值的代码
  
  safetyCounter++;
  if (safetyCounter > 5) {
    console.log("!!! 安全阀启动，强制退出无限循环！");
    break;
  }
}
console.log("如果没有安全阀，程序会一直卡在这里。");


console.log("\n=== 正确用法 ===");
// ✅ 正确: 在循环体内确保更新条件变量
let j = 0;
while (j < 3) {
  console.log("循环正常进行中, j 的值是:", j);
  j++; // 关键步骤：每次循环都让 j 增加，确保循环最终会结束
}
console.log("循环正常结束。j 的最终值是:", j);
```

### 🚀 Level 4: 实战应用（真实场景）

🎮 **游戏场景**: 迷你回合制战斗

让我们用 `do-while` 循环来模拟一个简单的打怪兽游戏。战斗至少会进行一回合，直到你或怪兽的生命值降到0或以下。

```javascript
// 场景：你是一位勇敢的冒险者，遇到了一只史莱姆！
console.log("⚔️ 一场战斗开始！你遇到了一只黏糊糊的史莱姆！");

// 1. 初始化角色和怪物状态
let heroHP = 100;
let slimeHP = 50;
let round = 0;

// 2. 使用 do-while 保证战斗至少进行一回合
do {
  round++;
  console.log(`\n--- 第 ${round} 回合 ---`);

  // 英雄攻击
  const heroAttack = Math.floor(Math.random() * 20) + 10; // 造成 10-29 点伤害
  slimeHP -= heroAttack;
  console.log(`你对史莱姆造成了 ${heroAttack} 点伤害！史莱姆剩余 HP: ${Math.max(0, slimeHP)}`);

  // 检查史莱姆是否存活
  if (slimeHP <= 0) {
    console.log("史莱姆被击败了！");
    break; // 怪物死亡，跳出循环
  }

  // 史莱姆攻击
  const slimeAttack = Math.floor(Math.random() * 15) + 5; // 造成 5-19 点伤害
  heroHP -= slimeAttack;
  console.log(`史莱姆反击，对你造成了 ${slimeAttack} 点伤害！你的剩余 HP: ${Math.max(0, heroHP)}`);
  
  // 检查英雄是否存活
  if (heroHP <= 0) {
    console.log("你被史莱姆击败了...");
    break; // 英雄死亡，跳出循环
  }

// 3. 循环条件：只要双方都还活着，战斗就继续
} while (heroHP > 0 && slimeHP > 0);

console.log("\n--- 战斗结束 ---");
if (heroHP > 0) {
  console.log("🏆 胜利！你获得了战斗的胜利！");
} else {
  console.log("☠️ 失败... 请再接再厉。");
}
```

### 💡 记忆要点
- **`while`**：先检查，后执行。像个谨慎的守卫，条件不符门都不开。
- **`do-while`**：先执行，后检查。像个热情的店主，先进来看看再说，保证你至少能“体验”一次。
- **无限循环**：务必在循环体内更新条件变量，给循环一个明确的“出口”，否则它将永不停止。

<!--
metadata:
  syntax: ["while", "do-while", "break"]
  pattern: ["loop"]
  api: ["console.log", "Math.random", "Math.floor", "Math.max"]
  concept: ["loop", "condition", "infinite-loop", "boolean"]
  difficulty: basic
  dependencies: []
  related: []
-->