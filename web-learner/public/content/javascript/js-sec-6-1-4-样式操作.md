## 样式操作

### 🎯 核心概念
JavaScript样式操作允许我们动态地改变网页上元素的CSS样式，从而实现动画、用户交互反馈、主题切换等丰富的视觉效果，让静态的页面“动”起来。

### 📚 Level 1: 基础认知（30秒理解）
通过 `element.style` 属性，我们可以像操作一个普通对象一样，直接读取和修改元素的内联样式。

```javascript
// 在纯JavaScript环境中，我们用一个对象来模拟一个HTML元素
const myElement = {
  id: 'greeting-text',
  textContent: 'Hello, Coder!',
  style: {} // 元素的style属性初始是一个空对象
};

console.log('修改前元素的样式:', myElement.style);

// 使用点（.）语法来设置CSS属性
myElement.style.color = 'blue';
myElement.style.fontSize = '24px'; // 注意属性名的变化

console.log('修改后元素的样式:', myElement.style);
console.log(`现在，ID为 '${myElement.id}' 的元素文本 "${myElement.textContent}" 将会以蓝色、24px的大小显示。`);
```

### 📈 Level 2: 核心特性（深入理解）
掌握样式操作的两个主要方式：直接修改`style`对象和通过操作`class`来批量应用样式。

#### 特性1: CSS属性的驼峰命名法转换
在JavaScript中，CSS属性名如果包含连字符（`-`），需要转换成驼峰命名法（camelCase）。例如，`background-color` 变为 `backgroundColor`。

```javascript
// 模拟一个按钮元素
const actionButton = {
  id: 'submit-btn',
  style: {
    padding: '10px',
    border: '1px solid black'
  }
};

console.log('按钮初始样式:', actionButton.style);

// 使用驼峰命名法修改CSS属性
actionButton.style.backgroundColor = '#28a745'; // CSS: background-color
actionButton.style.borderRadius = '5px';      // CSS: border-radius
actionButton.style.borderBottomWidth = '4px'; // CSS: border-bottom-width

console.log('按钮修改后样式:', actionButton.style);
console.log('注意: background-color 和 border-radius 都被转换为了驼峰命名法。');
```

#### 特性2: 使用 `classList` 管理类名
直接修改单个样式很方便，但更推荐的做法是通过添加或移除CSS类来批量管理样式。`element.classList` 提供了一套简单好用的API (`add`, `remove`, `toggle`)。

```javascript
// 模拟一个带有classList API的卡片元素
const userCard = {
  className: 'card', // 初始类名
  // 模拟一个简单的classList对象
  classList: {
    _classes: ['card'],
    add: function(className) { if(!this._classes.includes(className)) this._classes.push(className); this._updateHost(); },
    remove: function(className) { this._classes = this._classes.filter(c => c !== className); this._updateHost(); },
    toggle: function(className) { this.contains(className) ? this.remove(className) : this.add(className); },
    contains: function(className) { return this._classes.includes(className); },
    _updateHost: function() { userCard.className = this._classes.join(' '); }
  }
};

console.log('初始类名:', userCard.className);

// 添加一个 'active' 类
userCard.classList.add('active');
console.log("添加 'active' 后:", userCard.className);

// 添加一个 'dark-theme' 类
userCard.classList.add('dark-theme');
console.log("添加 'dark-theme' 后:", userCard.className);

// 移除 'active' 类
userCard.classList.remove('active');
console.log("移除 'active' 后:", userCard.className);

// 切换 'dark-theme' 类 (它现在存在，所以会被移除)
userCard.classList.toggle('dark-theme');
console.log("切换 'dark-theme' (第一次) 后:", userCard.className);
```

### 🔍 Level 3: 对比学习（避免陷阱）
直接操作 `className` 和使用 `classList` 有着天壤之别，前者是覆盖，后者是管理。

```javascript
// 模拟一个需要添加状态类的元素
const playerAvatar = {
  className: 'avatar rounded',
  // 模拟 classList
  classList: {
    _classes: ['avatar', 'rounded'],
    add: function(cls) { if (!this._classes.includes(cls)) { this._classes.push(cls); } playerAvatar.className = this._classes.join(' '); },
  }
};

console.log("=== 错误用法 ===");
// ❌ 错误：直接用 `className` 字符串拼接来添加新类
console.log("操作前:", playerAvatar.className);
playerAvatar.className += ' is-online'; // 注意前面需要加空格，容易出错
console.log("错误操作后:", playerAvatar.className);
console.log("问题：这种方式繁琐且容易出错，比如忘记加空格会导致类名变成 'avatar roundedis-online'。如果想移除一个类，字符串操作会更复杂。");


// 重置状态
playerAvatar.className = 'avatar rounded';
playerAvatar.classList._classes = ['avatar', 'rounded'];


console.log("\n=== 正确用法 ===");
// ✅ 正确：使用 `classList.add()` 来添加新类
console.log("操作前:", playerAvatar.className);
playerAvatar.classList.add('is-online');
console.log("正确操作后:", playerAvatar.className);
console.log("优点：`classList.add` 方法清晰、安全，无需关心空格或重复添加的问题，是管理类名的最佳实践。");
```

### 🚀 Level 4: 实战应用（真实场景）
**🐾 场景：虚拟宠物心情反应系统**

我们的虚拟宠物 "代码猫" (CodeCat) 会根据我们的互动改变心情，并通过改变样式来直观地展示它的情绪！

```javascript
// 模拟一个代表宠物的HTML元素
const petElement = {
  // style 对象用于存储CSS样式
  style: {
    border: '2px solid black',
    padding: '15px',
    display: 'inline-block',
    fontFamily: 'monospace',
    lineHeight: '1.2',
    transition: 'all 0.3s' // 想象一下平滑的过渡效果
  },
  // innerHTML 用于显示宠物的ASCII艺术形象
  innerHTML: ''
};

// 定义不同心情对应的样式和形象
const moods = {
  happy: {
    borderColor: 'hsl(120, 70%, 50%)', // 鲜绿色
    backgroundColor: 'hsl(120, 70%, 95%)',
    icon: `
  /\\_/\\
 ( ^.^ )
 (> . <)`
  },
  sad: {
    borderColor: 'hsl(210, 30%, 50%)', // 忧郁蓝
    backgroundColor: 'hsl(210, 30%, 95%)',
    icon: `
  /\\_/\\
 ( ._. )
 (  v  )`
  },
  curious: {
    borderColor: 'hsl(45, 100%, 50%)', // 好奇黄
    backgroundColor: 'hsl(45, 100%, 95%)',
    icon: `
  /\\_/\\
 ( o.O )
 (  ?  )`
  }
};

// 更新宠物外观的函数
function setPetMood(mood) {
  console.log(`\n===== 代码猫的心情变成了: ${mood.toUpperCase()}! =====`);

  const newLook = moods[mood];
  if (!newLook) {
    console.log('未知的心情，代码猫表示很困惑...');
    return;
  }

  // 1. 使用JS动态修改 style 属性
  petElement.style.borderColor = newLook.borderColor;
  petElement.style.backgroundColor = newLook.backgroundColor;

  // 2. 更新宠物的ASCII形象
  petElement.innerHTML = newLook.icon;

  // 3. 打印出宠物的当前状态
  console.log('代码猫现在的样子:');
  console.log(petElement.innerHTML);
  console.log('它的"窝"的样式:', petElement.style);
}

// 让我们来改变代码猫的心情！
setPetMood('happy');   // 代码猫很高兴，因为你开始学习JS了
setPetMood('sad');     // 代码猫很难过，因为它发现了一个bug
setPetMood('curious'); // 代码猫很好奇，想知道你接下来要学什么
```

### 💡 记忆要点
- **要点1**: 使用 `element.style.property` 来直接修改元素的内联样式，非常适合动态、个别的样式调整。
- **要点2**: CSS属性中带连字符的（如 `background-color`）在JavaScript中需要转换为驼峰命名法（`backgroundColor`）。
- **要点3**: 优先使用 `element.classList`（`.add()`, `.remove()`, `.toggle()`）来管理CSS类，因为它更安全、功能更强大，不会意外覆盖现有类。

<!--
metadata:
  syntax: [variable-declaration, const, function, object-literal]
  pattern: [object-literal]
  api: [style, classList, console.log]
  concept: [dom-manipulation, style-binding]
  difficulty: basic
  dependencies: [无]
  related: [js-sec-6-1-3]
-->