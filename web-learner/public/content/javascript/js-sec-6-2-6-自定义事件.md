## 自定义事件

### 🎯 核心概念
自定义事件允许我们创建和派发自己的事件，实现代码模块间的解耦通信，当一个模块的状态发生变化时，可以通知其他不相关的模块，而无需直接调用它们。

### 📚 Level 1: 基础认知（30秒理解）
我们可以像创建点击（click）或按键（keydown）事件一样，创建属于我们自己的事件。首先监听一个自定义事件，然后创建并“派发”（dispatch）它，监听器就会被触发。

```javascript
// Level 1: 最简单的自定义事件

// 1. 选择一个元素作为事件目标
const eventTarget = document.body;

// 2. 在目标上监听我们自定义的事件 'partyTime'
eventTarget.addEventListener('partyTime', () => {
  console.log('🎉 Party Time! Let\'s celebrate!');
});

// 3. 创建一个新的自定义事件实例
const myEvent = new CustomEvent('partyTime');

// 4. 在目标上派发（触发）这个事件
eventTarget.dispatchEvent(myEvent);

// 控制台输出:
// 🎉 Party Time! Let's celebrate!
```

### 📈 Level 2: 核心特性（深入理解）
自定义事件不仅能被触发，还能携带数据，并像原生DOM事件一样冒泡。

#### 特性1: 使用 `detail` 属性传递数据
创建事件时，我们可以通过 `detail` 属性附加任何我们想要传递的数据（对象、数组、字符串等）。

```javascript
// Level 2, Feature 1: 传递数据

const gameConsole = document.body;

// 监听 'newAchievement' 事件，并准备接收数据
gameConsole.addEventListener('newAchievement', (event) => {
  // 通过 event.detail 访问传递过来的数据
  const achievementData = event.detail;
  console.log(`🏆 新成就解锁!`);
  console.log(`   名称: ${achievementData.name}`);
  console.log(`   分数: ${achievementData.score}点`);
  console.log(`   稀有度: ${achievementData.rarity}`);
});

// 创建事件时，通过 detail 属性传入一个对象
const achievementEvent = new CustomEvent('newAchievement', {
  detail: {
    name: '代码魔法师',
    score: 100,
    rarity: '史诗'
  }
});

// 派发事件
gameConsole.dispatchEvent(achievementEvent);

// 控制台输出:
// 🏆 新成就解锁!
//    名称: 代码魔法师
//    分数: 100点
//    稀有度: 史诗
```

#### 特性2: 事件冒泡 (`bubbles`)
通过设置 `bubbles: true`，自定义事件可以像点击事件一样，从触发元素逐级向上传播到父元素，直到文档根节点。

```javascript
// Level 2, Feature 2: 事件冒泡

// 为了在Node.js环境或浏览器无DOM环境下模拟，我们使用EventTarget
// 在浏览器中，你可以直接使用 document.createElement('div')
class MockElement extends EventTarget {
    constructor(name, parent = null) {
        super();
        this.name = name;
        this.parent = parent;
    }
    // 重写 dispatchEvent 以模拟冒泡
    dispatchEvent(event) {
        let target = this;
        // 调用自身的监听器
        super.dispatchEvent(event);
        // 如果 bubbles 为 true 且有父元素，则在父元素上继续派发
        if (event.bubbles && target.parent) {
            target.parent.dispatchEvent(event);
        }
    }
}

const parentBox = new MockElement('parentBox');
const childBox = new MockElement('childBox', parentBox);

// 在父元素上监听
parentBox.addEventListener('customBubble', (event) => {
  console.log(`[父元素] 捕获到了来自 ${event.target.name} 的冒泡事件！`);
});

// 在子元素上监听
childBox.addEventListener('customBubble', (event) => {
  console.log(`[子元素] 事件从我这里开始！`);
});

// 创建一个可冒泡的事件
const bubbleEvent = new CustomEvent('customBubble', { bubbles: true });

console.log('派发事件...');
// 从子元素开始派发
childBox.dispatchEvent(bubbleEvent);

// 控制台输出:
// 派发事件...
// [子元素] 事件从我这里开始！
// [父元素] 捕获到了来自 childBox 的冒泡事件！
```

### 🔍 Level 3: 对比学习（避免陷阱）
自定义事件的主要优势在于解耦。当两个模块需要通信时，直接调用对方的函数会导致紧耦合，难以维护和测试。

```javascript
// 假设我们有一个玩家(Player)和一个UI管理器(UIManager)
// 它们都需要在分数变化时做出反应

console.log("=== 错误用法: 紧耦合 ===");
// ❌ 玩家对象直接依赖并调用UI管理器的方法
const UIManager_Bad = {
  updateScoreboard: (score) => {
    console.log(`[UI] 分数已更新: ${score}`);
  }
};

const Player_Bad = {
  score: 0,
  addScore: function(points) {
    this.score += points;
    console.log(`[玩家] 获得了 ${points} 分！`);
    // 直接调用，Player必须知道UIManager_Bad的存在和它的方法名
    UIManager_Bad.updateScoreboard(this.score);
  }
};
Player_Bad.addScore(10);
// 这种方式的问题是：如果UI管理器的名字或方法改变，玩家代码也必须修改。
// 如果想添加另一个模块（如音效模块）来响应分数变化，还得修改Player的代码。


console.log("\n=== 正确用法: 使用自定义事件解耦 ===");
// ✅ 玩家只需派发事件，不关心谁在监听
const eventBus = new EventTarget(); // 使用一个共享的事件中心

const UIManager_Good = {
  init: function() {
    eventBus.addEventListener('scoreChanged', (event) => {
      this.updateScoreboard(event.detail.newScore);
    });
  },
  updateScoreboard: (score) => {
    console.log(`[UI] 分数已更新: ${score}`);
  }
};

const SoundManager_Good = {
    init: function() {
        eventBus.addEventListener('scoreChanged', (event) => {
            if (event.detail.points > 0) {
                this.playSound('score-up');
            }
        });
    },
    playSound: (soundName) => {
        console.log(`[音效] 播放声音: ${soundName}.mp3`);
    }
};

const Player_Good = {
  score: 0,
  addScore: function(points) {
    this.score += points;
    console.log(`[玩家] 获得了 ${points} 分！`);
    // 派发事件，将新分数和增加的分数作为数据传递
    const scoreEvent = new CustomEvent('scoreChanged', {
      detail: { newScore: this.score, points: points }
    });
    eventBus.dispatchEvent(scoreEvent);
  }
};

// 初始化监听模块
UIManager_Good.init();
SoundManager_Good.init();

// 玩家得分
Player_Good.addScore(50);
// 现在，玩家模块完全不知道UI或音效模块的存在。
// 我们可以轻松添加或删除任意数量的监听器，而无需修改玩家代码。

// 控制台输出:
// === 错误用法: 紧耦合 ===
// [玩家] 获得了 10 分！
// [UI] 分数已更新: 10
//
// === 正确用法: 使用自定义事件解耦 ===
// [玩家] 获得了 50 分！
// [UI] 分数已更新: 50
// [音效] 播放声音: score-up.mp3
```

### 🚀 Level 4: 实战应用（真实场景）
**场景：🐾 虚拟宠物互动系统**

我们来创建一个虚拟电子宠物。这个宠物有自己的“生命周期”，它的心情和饥饿度会随时间变化。当它的状态达到某个临界点时（例如太饿或太开心），它会派发一个自定义事件。一个独立的“宠物护理系统”会监听这些事件，并向我们（主人）报告宠物的状态。

```javascript
// 场景: 虚拟宠物互动系统

// 创建一个全局的事件中心，让宠物和护理系统通过它来通信
const petEventBus = new EventTarget();

// 宠物护理系统，它只关心事件
const petCareSystem = {
  init: function() {
    console.log("宠物护理系统已启动，正在监听宠物状态...");
    petEventBus.addEventListener('petStateChange', this.handleStateChange);
  },
  handleStateChange: (event) => {
    const { petName, mood, message, hunger, happiness } = event.detail;
    console.log(`\n======= 宠物状态警报! =======`);
    console.log(`宠物: ${petName}`);
    console.log(`心情: ${mood}`);
    console.log(`留言: "${message}"`);
    console.log(`(当前饥饿度: ${hunger}, 快乐度: ${happiness})`);
    console.log(`==============================\n`);
  }
};

// 虚拟宠物对象
const myVirtualPet = {
  name: '皮卡丘',
  hunger: 50,
  happiness: 50,

  live: function() {
    console.log(`${this.name} 开始了新的一天! (饥饿度: ${this.hunger}, 快乐度: ${this.happiness})`);
    setInterval(() => {
      // 模拟时间和状态变化
      this.hunger += 5;
      this.happiness -= 3;
      
      console.log(`...时间流逝... (饿: ${this.hunger}, 乐: ${this.happiness})`);

      // 检查状态并派发事件
      if (this.hunger > 80) {
        this.emitStateChangeEvent('饿坏了', 'Pika Pika! 我要吃东西！');
        this.hunger = 80; // 防止重复触发
      }
      if (this.happiness < 20) {
        this.emitStateChangeEvent('不开心', 'Pika... 我想玩...');
        this.happiness = 20; // 防止重复触发
      }
    }, 2000); // 每2秒更新一次状态
  },

  feed: function() {
    console.log(`你喂了 ${this.name} 一些食物.`);
    this.hunger -= 30;
    this.happiness += 10;
    if (this.hunger < 0) this.hunger = 0;
    this.emitStateChangeEvent('满足', 'Pikaaa-chuuuu! 好吃!');
  },

  play: function() {
    console.log(`你和 ${this.name} 玩了游戏.`);
    this.happiness += 30;
    this.hunger += 10;
    if (this.happiness > 100) this.happiness = 100;
    this.emitStateChangeEvent('超开心', 'PI-KA-CHU!!!');
  },

  emitStateChangeEvent: function(mood, message) {
    const stateEvent = new CustomEvent('petStateChange', {
      detail: {
        petName: this.name,
        mood: mood,
        message: message,
        hunger: this.hunger,
        happiness: this.happiness
      }
    });
    petEventBus.dispatchEvent(stateEvent);
  }
};

// --- 启动模拟 ---
petCareSystem.init();
myVirtualPet.live();

// 模拟用户与宠物互动 (在几秒后执行)
setTimeout(() => {
  myVirtualPet.play();
}, 3000);

setTimeout(() => {
  myVirtualPet.feed();
}, 9000);

// 你可以观察控制台输出，看到宠物状态随时间变化，
// 并在特定条件下自动触发事件，护理系统会作出响应。
// 用户的互动也会触发事件。
```

### 💡 记忆要点
- **创建**: 使用 `new CustomEvent('eventName', { detail: data, bubbles: true })` 创建事件，`detail` 用于携带数据。
- **派发**: 使用 `element.dispatchEvent(myEvent)` 在一个DOM元素或`EventTarget`上触发事件。
- **监听**: 使用 `element.addEventListener('eventName', (event) => { ... })` 监听事件，并通过 `event.detail` 获取数据。

<!--
metadata:
  syntax: [class, const, function]
  pattern: [event-driven-programming, decoupling]
  api: [CustomEvent, dispatchEvent, addEventListener, EventTarget]
  concept: [custom-events, event-bubbling, decoupling]
  difficulty: advanced
  dependencies: [无]
  related: [js-sec-6-2-1]
-->