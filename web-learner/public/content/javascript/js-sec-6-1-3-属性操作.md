好的，作为一名专业的JavaScript教育专家，我将为您生成关于“属性操作”的学习内容。内容将严格遵循您的要求，结构清晰，代码示例完整且有趣。

---

## 属性操作

### 🎯 核心概念
属性操作允许我们动态地读取、添加、修改或删除HTML元素的属性，这是让网页从静态变得动态和可交互的基础。

### 📚 Level 1: 基础认知（30秒理解）
想象一下给一个机器人贴上名牌。我们可以使用 `setAttribute` 来贴上（设置）名牌，用 `getAttribute` 来读取名牌上的名字。

```javascript
// 注意: 以下代码需要在浏览器环境中运行，可以复制到浏览器开发者工具的Console中执行。

// 1. 创建一个虚拟的元素，就像创造一个机器人
const robot = document.createElement('div');

// 2. 给机器人贴上一个名为 "id" 的名牌，值为 "R2-D2"
robot.setAttribute('id', 'R2-D2');

// 3. 读取这个机器人 "id" 名牌上的值
const robotId = robot.getAttribute('id');

console.log(`成功创建机器人，它的ID是: ${robotId}`); // 输出: 成功创建机器人，它的ID是: R2-D2

// 4. 你可以检查这个虚拟元素，它现在看起来像 <div id="R2-D2"></div>
console.log(robot.outerHTML);
```

### 📈 Level 2: 核心特性（深入理解）
深入了解属性操作的两个关键特性。

#### 特性1: 设置和移除多种属性
一个元素可以有多个属性，比如 `class` 用于样式，`disabled` 用于禁用按钮等。我们可以随时添加或移除它们。

```javascript
// 注意: 以下代码需要在浏览器环境中运行。

// 创建一个按钮元素
const actionButton = document.createElement('button');
actionButton.textContent = '发射激光';

// 使用 setAttribute 添加 class 和 id
actionButton.setAttribute('class', 'laser-button primary');
actionButton.setAttribute('id', 'main-laser-btn');

console.log('按钮初始状态:', actionButton.outerHTML);
// 输出: 按钮初始状态: <button class="laser-button primary" id="main-laser-btn">发射激光</button>

// 模拟能量耗尽，禁用按钮
actionButton.setAttribute('disabled', 'true');
console.log('能量耗尽后:', actionButton.outerHTML);
// 输出: 能量耗尽后: <button class="laser-button primary" id="main-laser-btn" disabled="true">发射激光</button>

// 能量恢复，移除 disabled 属性，让按钮恢复可用
actionButton.removeAttribute('disabled');
console.log('能量恢复后:', actionButton.outerHTML);
// 输出: 能量恢复后: <button class="laser-button primary" id="main-laser-btn">发射激光</button>
```

#### 特性2: 使用 `data-*` 自定义数据属性
有时我们需要在元素上存储一些自定义的数据，比如玩家分数、物品ID等。HTML5提供了 `data-*` 属性，这是一种安全、标准的做法。

```javascript
// 注意: 以下代码需要在浏览器环境中运行。

// 创建一个代表游戏角色的元素
const player = document.createElement('div');

// 使用 data-* 属性存储角色信息
player.setAttribute('data-player-name', 'Zelda');
player.setAttribute('data-level', '5');
player.setAttribute('data-score', '12500');

// 读取这些自定义数据
const playerName = player.getAttribute('data-player-name');
const playerScore = player.getAttribute('data-score');

console.log(`${playerName} 的当前分数是: ${playerScore}`);
// 输出: Zelda 的当前分数是: 12500

// 角色升级
const currentLevel = parseInt(player.getAttribute('data-level'), 10);
const newLevel = currentLevel + 1;
player.setAttribute('data-level', newLevel);

console.log(`${playerName} 升级了! 当前等级: ${player.getAttribute('data-level')}`);
// 输出: Zelda 升级了! 当前等级: 6
```

### 🔍 Level 3: 对比学习（避免陷阱）
直接用点 `.` 操作属性和使用 `setAttribute` 有什么区别？对于自定义属性，区别很大！

```javascript
// 注意: 以下代码需要在浏览器环境中运行。

const myBox = document.createElement('div');

console.log("=== 错误用法 ===");
// ❌ 尝试用点(.)操作符创建一个非标准属性
myBox.myCustomData = '秘密信息';
console.log('通过点操作符设置后，JS对象上确实有该属性:', myBox.myCustomData);
// 但是，这并没有在HTML上创建对应的属性！
console.log('检查HTML属性 (getAttribute):', myBox.getAttribute('myCustomData')); // 输出: null
console.log('检查HTML结构:', myBox.outerHTML); // 输出: <div></div> (属性没有出现)
// 解释: 点操作符操作的是JavaScript对象的属性，而不是HTML标签的属性。这对于存储临时状态很有用，但它不会反映在HTML结构上，CSS选择器（如[myCustomData="..."]）也无法选中它。

console.log("\n=== 正确用法 ===");
// ✅ 使用 setAttribute 创建自定义属性
myBox.setAttribute('my-custom-data', '公开情报');
console.log('通过setAttribute设置后，JS对象上没有直接的同名属性:', myBox.myCustomData); // 仍然是'秘密信息'
// 但是，HTML属性被正确创建了
console.log('检查HTML属性 (getAttribute):', myBox.getAttribute('my-custom-data')); // 输出: 公开情报
console.log('检查HTML结构:', myBox.outerHTML); // 输出: <div my-custom-data="公开情报"></div>
// 解释: setAttribute 直接操作HTML标签的属性。这是创建和修改HTML属性（特别是自定义属性和data-*属性）的标准和推荐方法。
```

### 🚀 Level 4: 实战应用（真实场景）
**场景: 🎮 角色升级系统**

让我们为一个简单的文字冒险游戏创建一个角色卡。我们将使用 `data-*` 属性来存储角色的所有状态，并通过一个函数来模拟升级过程，看看属性是如何动态变化的。

```javascript
// 注意: 以下代码需要在浏览器环境中运行。

// 创建一个代表我们英雄的虚拟元素
const heroCard = document.createElement('div');
heroCard.setAttribute('id', 'hero-gimli');
heroCard.setAttribute('data-name', 'Gimli');
heroCard.setAttribute('data-class', '矮人战士');
heroCard.setAttribute('data-level', '1');
heroCard.setAttribute('data-hp', '20');
heroCard.setAttribute('data-strength', '15');
heroCard.setAttribute('data-weapon', '战斧');

/**
 * 打印角色状态信息
 * @param {HTMLElement} character - 代表角色的元素
 */
function displayStats(character) {
  const name = character.getAttribute('data-name');
  const level = character.getAttribute('data-level');
  const hp = character.getAttribute('data-hp');
  const strength = character.getAttribute('data-strength');
  const weapon = character.getAttribute('data-weapon');

  console.log(`
    --- 角色状态卡 ---
    姓名: ${name} (Lv. ${level})
    职业: ${character.getAttribute('data-class')}
    生命值: ${hp}
    力量: ${strength}
    武器: ${weapon}
    --------------------
  `);
}

/**
 * 角色升级函数
 * @param {HTMLElement} character - 代表角色的元素
 */
function levelUp(character) {
  const name = character.getAttribute('data-name');
  console.log(`🎉 恭喜！ ${name} 升级了！ 🎉`);

  // 1. 读取当前等级并 +1
  let currentLevel = parseInt(character.getAttribute('data-level'), 10);
  character.setAttribute('data-level', ++currentLevel);

  // 2. 增加生命值和力量
  let currentHp = parseInt(character.getAttribute('data-hp'), 10);
  let currentStrength = parseInt(character.getAttribute('data-strength'), 10);
  character.setAttribute('data-hp', currentHp + 10);
  character.setAttribute('data-strength', currentStrength + 5);

  // 3. 等级达到3级时，获得新武器！
  if (currentLevel === 3) {
    console.log(`✨ ${name} 获得了新的武器：风暴战锤！`);
    character.setAttribute('data-weapon', '风暴战锤');
  }
}

// 游戏开始，显示初始状态
console.log("游戏开始，英雄登场！");
displayStats(heroCard);

// 英雄经历了一场战斗，升级了！
levelUp(heroCard);
displayStats(heroCard);

// 再次升级！
levelUp(heroCard);
displayStats(heroCard);

// 第三次升级，看看会不会有惊喜！
levelUp(heroCard);
displayStats(heroCard);
```

### 💡 记忆要点
- **`setAttribute(name, value)`**: 设置或修改一个HTML属性，是创建自定义属性的标准方式。
- **`getAttribute(name)`**: 读取HTML属性的值，返回的是字符串。
- **`data-*`**: 使用 `data-` 前缀来创建自定义属性，用于在元素上安全地存储程序所需的数据。

<!--
metadata:
  syntax: [const, function, let]
  pattern: [dom-manipulation]
  api: [setAttribute, getAttribute, removeAttribute, console.log, document.createElement, parseInt]
  concept: [dom-attributes, data-attributes]
  difficulty: basic
  dependencies: [无]
  related: []
-->