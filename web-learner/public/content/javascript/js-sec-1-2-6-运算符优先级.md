好的，作为一名专业的JavaScript教育专家，我将为你生成关于“运算符优先级”的教学内容。

---

## 运算符优先级

### 🎯 核心概念
运算符优先级决定了在包含多个运算符的表达式中，哪个运算符先被执行。就像数学中的“先乘除后加减”一样，它是确保代码按照预期逻辑计算的规则。

### 📚 Level 1: 基础认知（30秒理解）
在没有括号的情况下，JavaScript会优先计算乘法，然后才是加法。

```javascript
// 声明两个变量
let a = 10;
let b = 5;

// 猜猜结果是多少？
// JavaScript会先计算 3 * b (3 * 5 = 15)
// 然后再计算 a + 15 (10 + 15 = 25)
let result = a + 3 * b;

console.log(`计算 10 + 3 * 5 的结果是: ${result}`); // 输出: 25
```

### 📈 Level 2: 核心特性（深入理解）
理解了基础的“先乘除后加减”，我们来看看更复杂的规则。

#### 特性1: 相同优先级的运算符，从左到右执行
当一个表达式中有多个相同优先级的运算符（如 `*` 和 `/`，或 `+` 和 `-`），计算会从左到右依次进行。

```javascript
// 定义一些数字
let initialValue = 100;
let divisor = 10;
let multiplier = 2;

// 1. 先从左到右计算 100 / 10，得到 10
// 2. 然后计算 10 * 2，得到 20
let result = initialValue / divisor * multiplier;

console.log(`100 / 10 * 2 的计算顺序是从左到右，结果是: ${result}`); // 输出: 20
```

#### 特性2: 使用括号 `()` 拥有最高优先级
括号是改变运算顺序的“法宝”。无论优先级多低，被括号括起来的表达式总会最先被计算。

```javascript
// 同样的数字，不同的结果
let apples = 5;
let oranges = 10;
let friends = 2;

// 不使用括号，会先算 oranges * friends
let wrongCalculation = apples + oranges * friends;
console.log(`不加括号：5 + 10 * 2 = ${wrongCalculation}`); // 输出: 25

// 使用括号，会先算 apples + oranges
let correctCalculation = (apples + oranges) * friends;
console.log(`加了括号：(5 + 10) * 2 = ${correctCalculation}`); // 输出: 30
console.log("场景：你想计算苹果和橘子的总数，然后分给2个朋友，每人一份。显然，30才是正确答案。");
```

### 🔍 Level 3: 对比学习（避免陷阱）
在实际编码中，不注意优先级常常会导致难以发现的逻辑错误。

```javascript
// 场景：计算三个科目的平均分
let mathScore = 90;
let englishScore = 85;
let scienceScore = 92;

console.log("=== 错误用法 ===");
// ❌ 错误：由于 / 的优先级高于 +，这里实际上是计算 90 + 85 + (92 / 3)
let wrongAverage = mathScore + englishScore + scienceScore / 3;
console.log(`错误的平均分计算: ${wrongAverage.toFixed(2)}`);
console.log("解释：这相当于只给科学打了折扣，而不是求三科的平均分。");


console.log("\n=== 正确用法 ===");
// ✅ 正确：使用括号先计算总分，再除以科目数量
let correctAverage = (mathScore + englishScore + scienceScore) / 3;
console.log(`正确的平均分计算: ${correctAverage.toFixed(2)}`);
console.log("解释：括号确保了先求和，再求平均，这才是我们想要的逻辑。");
```

### 🚀 Level 4: 实战应用（真实场景）

**🎮 游戏场景：计算角色的最终攻击力**

在一个奇幻RPG游戏中，英雄的最终攻击力由多个因素决定：基础攻击力、装备加成（百分比）和临时药水效果（固定值）。错误的计算顺序会让你的英雄变得不堪一击！

**公式：`最终攻击力 = (基础攻击力 + 药水提升) * 装备加成`**

```javascript
// 角色属性设定
const characterName = "屠龙者·阿尔法";
let baseAttack = 100; // 基础攻击力
let weaponBonus = 1.5; // 史诗长剑提供50%的攻击力加成 (1 + 0.5)
let potionEffect = 20; // 喝下了一瓶力量药水，临时增加20点攻击力

console.log(`💥 英雄【${characterName}】准备战斗！`);
console.log(`基础攻击: ${baseAttack}, 武器加成: ${weaponBonus}, 药水效果: +${potionEffect}`);
console.log("-------------------------------------");

// 错误的计算方式：没有使用括号
// 运算顺序：potionEffect * weaponBonus 先被计算 (20 * 1.5 = 30)，然后再加上 baseAttack (100 + 30 = 130)
let wrongFinalAttack = baseAttack + potionEffect * weaponBonus;
console.log(`❌ 计算失误！最终攻击力: ${wrongFinalAttack}`);
console.log("😱 “糟糕！我的力量药水好像没起作用！” 阿尔法大喊。这点伤害连史莱姆的皮都破不了！");

console.log("-------------------------------------");

// 正确的计算方式：使用括号确保逻辑正确
// 运算顺序：(baseAttack + potionEffect) 先被计算 (100 + 20 = 120)，然后再乘以 weaponBonus (120 * 1.5 = 180)
let correctFinalAttack = (baseAttack + potionEffect) * weaponBonus;
console.log(`✅ 正确计算！最终攻击力: ${correctFinalAttack}`);
console.log(`🐲 “感受我的愤怒吧！” 阿尔法一剑挥出，对巨龙造成了 ${correctFinalAttack} 点毁灭性伤害！`);
```

### 💡 记忆要点
- **要点1**：乘法 `*`、除法 `/`、取模 `%` 的优先级高于加法 `+` 和减法 `-`。
- **要点2**：括号 `()` 的优先级最高，可以强制改变运算顺序。
- **要点3**：当不确定优先级时，主动使用括号。这不仅能保证计算正确，还能让代码意图更清晰，更易于阅读和维护。

<!--
metadata:
  syntax: let, const
  pattern: expression-evaluation
  api: console.log
  concept: operator-precedence
  difficulty: intermediate
  dependencies: [无]
  related: [js-sec-1-2-1]
-->