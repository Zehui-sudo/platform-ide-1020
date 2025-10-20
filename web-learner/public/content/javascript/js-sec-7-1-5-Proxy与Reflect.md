## Proxy与Reflect

### 🎯 核心概念
Proxy与Reflect是JavaScript提供的元编程（metaprogramming）能力，它允许我们拦截并自定义对象的基本操作（如属性查找、赋值、函数调用等），相当于在目标对象前架设一个“代理”，所有对该对象的操作都需经过这层代理，从而实现验证、监控、格式化等高级功能。

### 📚 Level 1: 基础认知（30秒理解）
最简单的Proxy就像一个看门人，每当有人访问对象属性时，它都会记录下来。

```javascript
// 目标对象：一个普通的书本信息
const book = {
  title: "The Lord of the Rings",
  author: "J.R.R. Tolkien"
};

// 创建一个代理处理器
const handler = {
  // 'get' 是一个“陷阱”，用于拦截属性读取操作
  get: function(target, property) {
    console.log(`正在访问属性: ${property}`);
    // 使用 Reflect.get 来安全地获取原始对象的属性值
    return Reflect.get(target, property);
  }
};

// 创建 book 对象的代理
const proxyBook = new Proxy(book, handler);

// 通过代理访问属性
console.log(proxyBook.title); 
// 输出: 正在访问属性: title
// 输出: The Lord of the Rings

console.log(proxyBook.author);
// 输出: 正在访问属性: author
// 输出: J.R.R. Tolkien
```

### 📈 Level 2: 核心特性（深入理解）
Proxy不仅仅能监视，还能修改和控制对象的行为。

#### 特性1: `get` 陷阱 - 提供默认值
当访问一个不存在的属性时，我们可以使用`get`陷阱返回一个默认值，而不是`undefined`，让代码更健壮。

```javascript
// 一个存储用户配置的对象
const userConfig = {
  theme: 'dark',
  fontSize: 14
};

// 代理处理器，为不存在的配置提供默认值
const configHandler = {
  get: function(target, property) {
    console.log(`尝试获取配置: '${property}'`);
    if (property in target) {
      return Reflect.get(target, property);
    } else {
      // 如果属性不存在，返回一个友好的默认提示
      console.log(`'${property}' 配置项不存在，返回默认值 'default'`);
      return 'default';
    }
  }
};

const proxyConfig = new Proxy(userConfig, configHandler);

// 访问存在的属性
console.log(`主题: ${proxyConfig.theme}`);
// 输出: 尝试获取配置: 'theme'
// 输出: 主题: dark

// 访问不存在的属性
console.log(`语言: ${proxyConfig.language}`);
// 输出: 尝试获取配置: 'language'
// 输出: 'language' 配置项不存在，返回默认值 'default'
// 输出: 语言: default
```

#### 特性2: `set` 陷阱 - 数据验证
`set`陷阱可以拦截属性赋值操作，是实现数据验证的完美工具。例如，确保年龄必须是数字且在合理范围内。

```javascript
// 目标用户对象
const user = {
  name: "Alice",
  age: 30
};

// 代理处理器，用于验证年龄
const validationHandler = {
  set: function(target, property, value) {
    if (property === 'age') {
      if (typeof value !== 'number' || value <= 0) {
        // 如果值无效，抛出错误，阻止赋值
        console.error("错误：年龄必须是一个正数！");
        return false; // 表示赋值失败
      }
    }
    // 对于有效值或其他属性，使用 Reflect.set 完成赋值
    console.log(`设置属性 ${property} 为 ${value}`);
    return Reflect.set(target, property, value);
  }
};

const proxyUser = new Proxy(user, validationHandler);

// 尝试进行一次有效的赋值
proxyUser.age = 31;
console.log("用户的新年龄:", user.age);
// 输出: 设置属性 age 为 31
// 输出: 用户的新年龄: 31

// 尝试进行一次无效的赋值
proxyUser.age = -5;
console.log("尝试无效赋值后，用户的年龄:", user.age);
// 输出: 错误：年龄必须是一个正数！
// 输出: 尝试无效赋值后，用户的年龄: 31 (年龄没有被改变)
```

### 🔍 Level 3: 对比学习（避免陷阱）
在`set`陷阱中，直接操作`target`可能导致问题，推荐始终使用`Reflect`。

```javascript
// 准备一个带有 setter 的目标对象
const userWithSetter = {
  _name: "Guest",
  get name() {
    return this._name;
  },
  set name(value) {
    console.log("内置的 setter 被调用了！");
    this._name = `User: ${value}`;
  }
};


console.log("=== 错误用法 (可能破坏 this 指向和 setter) ===");
// ❌ 错误做法：在 handler 中直接操作 target
const wrongHandler = {
  set: function(target, property, value) {
    console.log("Proxy 'set' 拦截: 直接修改 target");
    // 直接赋值会调用 setter，但如果 setter 内部依赖 this，
    // 且 this 被期望为代理对象时，这里会出问题。
    // 在这个简单例子中能工作，但在更复杂场景（如继承）下会失败。
    target[property] = value; 
    return true;
  }
};
const wrongProxy = new Proxy(userWithSetter, wrongHandler);
wrongProxy.name = "Alice";
console.log("错误用法后的名字:", wrongProxy.name);
// 解释：直接使用 `target[property] = value` 绕过了Proxy的上下文（receiver），
// 在处理带有 getter/setter 或继承的原型链时，可能导致 `this` 指向不正确，从而引发错误。


console.log("\n=== 正确用法 (使用 Reflect) ===");
// ✅ 正确做法：使用 Reflect.set 保证操作的正确性
const correctHandler = {
  set: function(target, property, value, receiver) {
    console.log("Proxy 'set' 拦截: 使用 Reflect.set");
    // Reflect.set 会正确地处理 this 指向（传入 receiver），并返回操作是否成功的布尔值。
    // 这是在 Proxy 陷阱中执行默认操作的标准方式。
    return Reflect.set(target, property, value, receiver);
  }
};
const correctProxy = new Proxy(userWithSetter, correctHandler);
correctProxy.name = "Bob";
console.log("正确用法后的名字:", correctProxy.name);
// 解释：`Reflect.set` 就像是内部 `[[Set]]` 操作的函数版本。它不仅完成了赋值，
// 还正确地将 `receiver` (通常是代理对象本身) 作为 `this` 的上下文传递给目标对象的 setter，
// 确保了操作的完整性和安全性。
```

### 🚀 Level 4: 实战应用（真实场景）
**场景：🐾 虚拟宠物互动**

让我们创建一个虚拟电子宠物！通过Proxy，我们可以让宠物对我们的操作（如喂食、玩耍）做出有趣的反应，而不需要在宠物对象上写一堆if-else判断。

```javascript
// 我们的虚拟宠物的基础属性
const myPet = {
  name: "皮卡丘",
  hunger: 50, // 饥饿度 (0-100)
  happiness: 50, // 快乐度 (0-100)
};

// 宠物心情处理器
const petHandler = {
  get(target, prop) {
    if (prop === 'mood') {
      // 'mood' 是一个虚拟属性，根据饥饿和快乐度动态计算
      if (target.hunger > 70 && target.happiness < 30) {
        return "😭 饿得快哭了，也不开心...";
      } else if (target.hunger > 70) {
        return "😫 好饿啊，快给我吃的！";
      } else if (target.happiness < 30) {
        return "😞 有点不开心，求关注。";
      }
      return "😊 心情不错！";
    }
    
    // 对于不存在的属性，给一个有趣的反馈
    if (!(prop in target)) {
      return `🤔 ${target.name}歪了歪头，不明白 '${prop}' 是什么意思。`;
    }

    return Reflect.get(target, prop);
  },

  set(target, prop, value) {
    // 拦截对饥饿度的修改
    if (prop === 'hunger') {
      if (value < target.hunger) {
        console.log(`🍴 给 ${target.name} 喂食... 饥饿度降低！`);
      } else {
        console.log(`🏃 ${target.name} 玩耍了一会儿，更饿了...`);
      }
      target.hunger = Math.max(0, Math.min(100, value)); // 确保值在0-100之间
      return true;
    }

    // 拦截对快乐度的修改
    if (prop === 'happiness') {
       if (value > target.happiness) {
        console.log(`💖 和 ${target.name} 玩耍... 快乐度提升！`);
      } else {
        console.log(`😢 ${target.name} 感到被冷落了...`);
      }
      target.happiness = Math.max(0, Math.min(100, value)); // 确保值在0-100之间
      return true;
    }
    
    return Reflect.set(target, prop, value);
  }
};

// 创建我们的智能宠物代理
const smartPet = new Proxy(myPet, petHandler);

console.log(`你好，我的名字是 ${smartPet.name}`);
console.log(`当前心情: ${smartPet.mood}`); // 访问虚拟属性

console.log("\n--- 开始互动 ---");

smartPet.hunger -= 30; // 喂食
smartPet.happiness += 20; // 玩耍

console.log(`\n互动后，${smartPet.name} 的饥饿度: ${smartPet.hunger}`);
console.log(`互动后，${smartPet.name} 的快乐度: ${smartPet.happiness}`);
console.log(`现在的心情: ${smartPet.mood}`);

console.log("\n--- 尝试奇怪的操作 ---");
console.log(smartPet.color); // 访问不存在的属性
```

### 💡 记忆要点
- **要点1**：Proxy是在目标对象外层包裹的一层“拦截网”，用于拦截并自定义对该对象的基本操作。
- **要点2**：Proxy的处理器（handler）对象包含多个“陷阱”（traps）方法，如 `get`、`set`，分别对应不同的操作。
- **要点3**：Reflect是一个内置对象，它提供与Proxy陷阱同名的方法，是在陷阱内部执行原始操作的“标准姿势”，能确保行为正确。

<!--
metadata:
  syntax: function, const, let, class, get, set
  pattern: proxy-pattern
  api: Proxy, Reflect, Reflect.get, Reflect.set, console.log
  concept: metaprogramming, proxy, reflection, traps, handler, target, receiver
  difficulty: advanced
  dependencies: [无]
  related: [js-sec-7-1-4]
-->