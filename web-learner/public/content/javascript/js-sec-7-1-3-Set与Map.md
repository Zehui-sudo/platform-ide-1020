## Set与Map

### 🎯 核心概念
Set 和 Map 提供了更专业、更强大的数据结构，Set 用于存储不重复的唯一值集合，而 Map 用于存储灵活的键值对集合，解决了普通对象键必须是字符串的限制。

### 📚 Level 1: 基础认知（30秒理解）
```javascript
// === Set: 自动去重的集合 ===
// 想象一个不允许有重复贴纸的贴纸簿

const stickerBook = new Set();
stickerBook.add('🚀');
stickerBook.add('🌟');
stickerBook.add('🚀'); // 尝试添加一个重复的贴纸

console.log("我的贴纸簿里有什么?", stickerBook);
console.log("贴纸数量:", stickerBook.size); // 重复的 '🚀' 被自动忽略了

// === Map: 什么都能当钥匙的柜子 ===
// 想象一个可以用任何物品（照片、石头）当钥匙的储物柜

const magicCabinet = new Map();
const keyPhoto = { id: 1, url: 'family.jpg' }; // 这是一把“照片”钥匙
const keyStone = { type: 'granite' }; // 这是一块“石头”钥匙

magicCabinet.set(keyPhoto, '珍贵的家庭回忆');
magicCabinet.set(keyStone, '一块发光的魔法石');

console.log("用照片钥匙能打开什么?", magicCabinet.get(keyPhoto));
console.log("柜子里有多少东西?", magicCabinet.size);
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: Set - 保证成员的唯一性
Set 最核心的特性是集合中的所有成员都是唯一的。你可以使用 `add()` 添加元素，`has()` 检查元素是否存在，`delete()` 删除元素。

```javascript
// 创建一个派对邀请名单，确保每个人只被邀请一次
const partyList = new Set();

// 添加客人
partyList.add('Alice');
partyList.add('Bob');
partyList.add('Charlie');

console.log('初始名单:', partyList);

// 尝试重复邀请 Bob
console.log('尝试再次邀请 Bob...');
partyList.add('Bob'); // 这个操作不会有任何效果
console.log('名单大小依然是:', partyList.size);
console.log('最终名单:', partyList);

// 检查某人是否在名单上
console.log('Bob在名单上吗?', partyList.has('Bob')); // true
console.log('David在名单上吗?', partyList.has('David')); // false

// Charlie临时有事，从名单中移除
partyList.delete('Charlie');
console.log('Charlie还在名单上吗?', partyList.has('Charlie')); // false
console.log('更新后的名单:', partyList);
```

#### 特性2: Map - 键的多样性
与只能用字符串（或 Symbol）作键的普通对象不同，Map 的键可以是任意类型的值，包括对象、函数、数字等。这在需要将对象与元数据关联时非常有用。

```javascript
// 为不同的英雄角色（对象）储存他们的专属技能（值）
const heroSkillMap = new Map();

const heroA = { name: 'Captain Invincible' };
const heroB = { name: 'Doctor Strange' };
const heroC = { name: 'The Flash' };

// 使用英雄对象本身作为键
heroSkillMap.set(heroA, 'Super Strength');
heroSkillMap.set(heroB, 'Mystic Arts');
heroSkillMap.set(heroC, 'Super Speed');

console.log(`${heroA.name}的技能是:`, heroSkillMap.get(heroA));
console.log(`${heroB.name}的技能是:`, heroSkillMap.get(heroB));

// 键可以是函数
const specialMove = () => 'Ultimate Power!';
heroSkillMap.set(specialMove, '这是一个终极技能的描述');
console.log('函数键对应的值:', heroSkillMap.get(specialMove));

// 键可以是数字
heroSkillMap.set(404, 'Secret Not Found');
console.log('数字键404对应的值:', heroSkillMap.get(404));
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个常见的错误是试图用普通对象实现 Map 的功能，尤其是当键不是字符串时。

```javascript
const user1 = { name: 'Alice' };
const user2 = { name: 'Bob' };

console.log("=== 错误用法 ===");
// ❌ 尝试使用普通对象，将对象作为键
const userRolesObject = {};
userRolesObject[user1] = 'Admin';
userRolesObject[user2] = 'Moderator';

// 为什么是错的:
// 对象的键会被强制转换为字符串。当 user1 和 user2 被用作键时，
// 它们都会被转换为 "[object Object]"。
// 因此，第二次赋值会覆盖第一次的！
console.log("对象键被转换后的样子:", Object.keys(userRolesObject));
console.log("对象中只有一个值:", userRolesObject);
console.log("尝试获取user1的角色:", userRolesObject[user1]); // 结果是 'Moderator'，而不是 'Admin'！


console.log("\n=== 正确用法 ===");
// ✅ 使用 Map，将对象作为键
const userRolesMap = new Map();
userRolesMap.set(user1, 'Admin');
userRolesMap.set(user2, 'Moderator');

// 为什么是对的:
// Map 会保留键的原始类型和值。user1 和 user2 是两个不同的对象引用，
// 所以它们被视为两个独立的键。
console.log("Map的大小:", userRolesMap.size); // 正确地显示为 2
console.log("获取user1的角色:", userRolesMap.get(user1)); // 正确地返回 'Admin'
console.log("获取user2的角色:", userRolesMap.get(user2)); // 正确地返回 'Moderator'
```

### 🚀 Level 4: 实战应用（真实场景）
**场景: 🐾 奇幻生物图鉴 (Fantasy Creature Pokedex)**

在这个场景中，你是一位奇幻生物学家，正在探索一个充满魔法生物的世界。你需要一个系统来记录你遇到的每一种独特的生物类型，并为捕获的每一只生物实例存储详细信息（比如它的心情和喜欢的食物）。

- `Set` 非常适合用来记录你遇到的**独一无二**的生物**种类**（火系、水系等）。
- `Map` 非常适合用来存储每**一只具体生物**（对象）的**详细数据**。

```javascript
// --- 奇幻生物图鉴系统 ---

// 1. 定义我们遇到的生物实例
const fireDragon = { id: 1, name: 'Ignis' };
const waterSprite = { id: 2, name: 'Aqua' };
const anotherFireDragon = { id: 3, name: 'Fuego' }; // 这是另一只火龙

// 2. 使用 Set 记录发现的生物种类（确保不重复）
const discoveredCreatureTypes = new Set();
console.log("🌍 探险开始！图鉴种类为空:", discoveredCreatureTypes);

// 3. 使用 Map 存储每只生物的详细档案，用生物对象本身作为钥匙
const creaturePokedex = new Map();

// 4. 探险函数，模拟遇到并记录生物
function encounterCreature(creature, type, mood, favoriteFood) {
  console.log(`\n Encountered a ${type} creature named ${creature.name}!`);

  // 记录这只生物的详细信息
  creaturePokedex.set(creature, {
    type: type,
    mood: mood,
    favoriteFood: favoriteFood
  });
  console.log(`✅ ${creature.name}的档案已存入图鉴Map。`);

  // 将它的种类添加到种类Set中
  if (!discoveredCreatureTypes.has(type)) {
    console.log(`🎉 哇！发现了一个新种类: ${type}!`);
  }
  discoveredCreatureTypes.add(type);
  console.log(`📚 当前已发现的种类Set:`, discoveredCreatureTypes);
}

// 5. 开始我们的探险旅程！
encounterCreature(fireDragon, '🔥 Fire', 'Grumpy', 'Spicy Peppers');
encounterCreature(waterSprite, '💧 Water', 'Playful', 'Seaweed Candy');
encounterCreature(anotherFireDragon, '🔥 Fire', 'Excited', 'Volcanic Rocks'); // 种类是火，但这是个新个体

// 6. 查看图鉴信息
console.log("\n--- 探险结束，查看图鉴 ---");
console.log(`总共发现了 ${discoveredCreatureTypes.size} 个独特的生物种类。`);

// 检查特定生物的档案
const ignisData = creaturePokedex.get(fireDragon);
if (ignisData) {
  console.log(`查询 ${fireDragon.name} 的档案:
    - 心情: ${ignisData.mood}
    - 最爱食物: ${ignisData.favoriteFood}`);
}
```

### 💡 记忆要点
- **Set是值的集合**：所有成员都独一无二，非常适合用于数组去重或记录唯一项。
- **Map是键值对的集合**：键的类型不限，可以是任意值（包括对象），完美解决了普通对象键的限制。
- **按需选择**：当你只需要一个不重复的值列表时，选择 `Set`；当你需要将数据与特定对象（或其他非字符串键）关联时，选择 `Map`。

<!--
metadata:
  syntax: [let, const, function]
  api: [Set, Map, console.log, Set.prototype.add, Set.prototype.has, Set.prototype.delete, Set.prototype.size, Map.prototype.set, Map.prototype.get, Map.prototype.size]
  concept: [collection, uniqueness, key-value-pair, data-structure]
  difficulty: intermediate
  dependencies: [无]
  related: [js-sec-5-1-1]
-->