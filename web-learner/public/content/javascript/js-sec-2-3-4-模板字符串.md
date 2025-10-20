好的，作为一名专业的JavaScript教育专家，我将为您生成关于“模板字符串”的教学内容。

---

## 模板字符串

### 🎯 核心概念
模板字符串解决了传统JavaScript中拼接字符串（使用 `+`）的繁琐和不支持多行字符串的问题，提供了一种更优雅、更直观的方式来创建包含动态内容的字符串。

### 📚 Level 1: 基础认知（30秒理解）
想象一下，你不再需要用笨拙的 `+` 号来连接变量和字符串了。模板字符串让你直接在字符串中“挖个坑”，把变量填进去。

```javascript
// 传统方法 vs 模板字符串

const userName = "Alex";

// 传统方法使用 '+' 拼接
const oldGreeting = "Hello, " + userName + "!";
console.log("传统方法:", oldGreeting);

// 模板字符串使用反引号 `` 和 ${}
const newGreeting = `Hello, ${userName}!`;
console.log("模板字符串:", newGreeting);
```

### 📈 Level 2: 核心特性（深入理解）
模板字符串不仅能嵌入变量，还有更多强大的功能。

#### 特性1: 嵌入任意表达式
你可以在 `${}` 中放入任何有效的JavaScript表达式，比如数学运算、函数调用、三元运算符等。

```javascript
const item = "苹果";
const price = 5;
const quantity = 3;

// 1. 进行数学运算
const message1 = `购买 ${quantity} 个${item}，总价是 ${price * quantity} 元。`;
console.log(message1);

// 2. 调用函数
function getStoreName() {
  return "奇妙水果店";
}
const message2 = `欢迎光临${getStoreName()}！`;
console.log(message2);

// 3. 使用三元运算符
const isMember = true;
const message3 = `顾客 ${isMember ? '是会员' : '不是会员'}。`;
console.log(message3);
```

#### 特性2: 支持多行字符串
在模板字符串中，换行符会直接被保留下来，创建多行文本变得极其简单，无需使用 `\n` 或字符串拼接。

```javascript
// 传统方法创建多行字符串，需要使用 \n
const oldMultiLine = "这是一个传统的多行字符串。\n第一行在这里。\n第二行在这里。";
console.log("传统多行:\n" + oldMultiLine);

console.log("\n" + "=".repeat(20) + "\n");

// 使用模板字符串，所见即所得
const newMultiLine = `这是一个模板字符串创建的多行文本。
第一行在这里。
第二行在这里。`;
console.log("模板字符串多行:\n" + newMultiLine);
```

### 🔍 Level 3: 对比学习（避免陷阱）
初学者最常犯的错误就是使用了错误的引号。模板字符串的特殊功能只在反引号（`` ` ``）中生效。

```javascript
const hero = "蜘蛛侠";
const city = "纽约";

console.log("=== 错误用法 ===");
// ❌ 错误：使用了单引号 ''
// 解释：单引号会把 ${hero} 当作普通文本，不会进行变量替换。
const wrongMessage1 = '我们的英雄是 ${hero}，他守护着 ${city}。';
console.log("使用单引号:", wrongMessage1);

// ❌ 错误：使用了双引号 ""
// 解释：双引号同样会把 ${hero} 当作普通文本。
const wrongMessage2 = "我们的英雄是 ${hero}，他守护着 ${city}。";
console.log("使用双引号:", wrongMessage2);


console.log("\n=== 正确用法 ===");
// ✅ 正确：必须使用反引号 ``
// 解释：只有在反引号中，`${...}` 语法才会被解析为表达式并嵌入到字符串中。
const correctMessage = `我们的英雄是 ${hero}，他守护着 ${city}。`;
console.log("使用反引号:", correctMessage);
```

### 🚀 Level 4: 实战应用（真实场景）
让我们进入一个游戏世界！你扮演的角色刚刚升级，我们需要生成一个酷炫的升级通知。模板字符串在这里大显身手！

**场景：🎮 角色升级系统**

我们将创建一个函数，它接收一个角色对象，然后生成一个格式化、多行的升级祝贺信息，包含角色的新状态和学会的新技能。

```javascript
// 角色升级通知生成器

function createLevelUpNotification(character) {
  const { name, level, job, stats, newSkill } = character;

  // 使用模板字符串构建一个丰富、多行的通知
  const notification = `
  ┌──────────────────────────────────┐
  │                                  │
  │   🎉🎉🎉 等级提升！🎉🎉🎉   │
  │                                  │
  ├──────────────────────────────────┤
  │                                  │
  │  英雄 ${name} (${job})            │
  │  等级提升至 Lv. ${level}！          │
  │                                  │
  │  新的属性:                       │
  │    - 生命值: ${stats.hp}         │
  │    - 攻击力: ${stats.attack}     │
  │    - 防御力: ${stats.defense}    │
  │                                  │
  │  学会新技能: 【${newSkill}】     │
  │                                  │
  └──────────────────────────────────┘
  `;
  return notification;
}

// 定义一个角色对象
const player = {
  name: "闪电之刃",
  level: 25,
  job: "剑士",
  stats: {
    hp: 1200,
    attack: 350,
    defense: 200,
  },
  newSkill: "疾风斩"
};

// 生成并打印通知
const levelUpMessage = createLevelUpNotification(player);
console.log(levelUpMessage);
```

### 💡 记忆要点
- **要点1**：模板字符串必须使用反引号（`` ` ``），而不是单引号或双引号。
- **要点2**：使用 `${}` 语法可以在字符串中嵌入任何有效的JavaScript表达式。
- **要点3**：模板字符串天然支持多行文本，无需 `\n`，回车即可换行。

<!--
metadata:
  syntax: template-literal
  pattern: string-interpolation
  api: console.log
  concept: string-concatenation, expression-interpolation
  difficulty: intermediate
  dependencies: [无]
  related: []
-->