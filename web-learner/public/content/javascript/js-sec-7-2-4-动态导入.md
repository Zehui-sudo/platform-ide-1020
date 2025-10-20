## 动态导入

### 🎯 核心概念
动态导入（Dynamic Import）允许你在代码运行时，根据需要（如用户操作或特定条件）才去加载和执行JavaScript模块，而不是在页面初始加载时就加载所有模块。这极大地优化了应用的初始加载速度和内存占用。

### 📚 Level 1: 基础认知（30秒理解）
静态`import`语句必须在文件的顶层使用，而动态`import()`可以在代码的任何地方像函数一样调用。它返回一个Promise，解析后会得到一个包含模块所有导出的对象。

为了让示例可独立运行，我们使用`Blob`和`URL.createObjectURL`在浏览器内存中模拟一个JS模块文件。

```javascript
// 模拟一个名为 'math.js' 的模块
const mathModuleCode = `
  export const add = (a, b) => a + b;
  export default function multiply(a, b) { return a * b; }
`;
const blob = new Blob([mathModuleCode], { type: 'application/javascript' });
const moduleUrl = URL.createObjectURL(blob);

// 使用动态导入加载这个模拟的模块
import(moduleUrl)
  .then(mathModule => {
    console.log("模块加载成功!");
    
    // 使用命名导出 (named export)
    const sum = mathModule.add(5, 3);
    console.log("调用命名导出 add(5, 3):", sum);

    // 使用默认导出 (default export)
    const product = mathModule.default(5, 3);
    console.log("调用默认导出 multiply(5, 3):", product);
  })
  .catch(err => {
    console.error("模块加载失败:", err);
  })
  .finally(() => {
    // 清理创建的URL对象
    URL.revokeObjectURL(moduleUrl);
  });
```

### 📈 Level 2: 核心特性（深入理解）
动态导入的核心优势在于其灵活性和与现代异步语法的结合。

#### 特性1: 结合 `async/await` 语法
使用 `async/await` 可以让异步的导入操作看起来像同步代码一样直观和简洁，是处理动态导入的首选方式。

```javascript
// 模拟一个名为 'userProfile.js' 的模块
const userProfileCode = `
  export function getGreeting(name) {
    return \`Hello, \${name}! Welcome back.\`;
  }
`;
const blob = new Blob([userProfileCode], { type: 'application/javascript' });
const moduleUrl = URL.createObjectURL(blob);

async function showGreeting(username) {
  try {
    console.log("准备动态加载用户问候模块...");
    const userProfileModule = await import(moduleUrl);
    const message = userProfileModule.getGreeting(username);
    console.log(message);
  } catch (error) {
    console.error("加载模块时出错:", error);
  } finally {
    URL.revokeObjectURL(moduleUrl);
  }
}

showGreeting("Explorer");
```

#### 特性2: 条件加载
这是动态导入最强大的功能之一。你可以根据特定条件（如用户权限、设备类型、功能开关等）来决定是否加载某个模块，避免不必要的代码加载。

```javascript
// 模拟两个不同的模块：一个用于管理员，一个用于普通用户
const adminModuleCode = `export default () => '欢迎进入管理员控制台！';`;
const guestModuleCode = `export default () => '你好，访客！请先登录。';`;

const adminBlob = new Blob([adminModuleCode], { type: 'application/javascript' });
const guestBlob = new Blob([guestModuleCode], { type: 'application/javascript' });

const adminModuleUrl = URL.createObjectURL(adminBlob);
const guestModuleUrl = URL.createObjectURL(guestBlob);

async function loadDashboard(userRole) {
  console.log(`用户角色: ${userRole}，正在加载对应模块...`);
  let messageFunction;
  
  if (userRole === 'admin') {
    const { default: getAdminMessage } = await import(adminModuleUrl);
    messageFunction = getAdminMessage;
  } else {
    const { default: getGuestMessage } = await import(guestModuleUrl);
    messageFunction = getGuestMessage;
  }
  
  console.log(messageFunction());
  
  // 清理
  URL.revokeObjectURL(adminModuleUrl);
  URL.revokeObjectURL(guestModuleUrl);
}

// 模拟不同用户登录
loadDashboard('admin');
setTimeout(() => loadDashboard('guest'), 100); // 延迟一点以看清两次输出
```

### 🔍 Level 3: 对比学习（避免陷阱）
动态导入返回的是一个Promise，这意味着你不能像同步代码那样立即使用它的结果。

```javascript
// 模拟一个模块
const utilityModuleCode = `export const magicNumber = 42;`;
const blob = new Blob([utilityModuleCode], { type: 'application/javascript' });
const moduleUrl = URL.createObjectURL(blob);

console.log("=== 错误用法 ===");
// ❌ 错误：直接尝试访问模块内容
// 解释：`import()` 立即返回一个Promise，而不是模块本身。
// 在Promise完成（resolved）之前，模块内容是不可用的。
try {
  const utilityModule = import(moduleUrl);
  // 下面这行会抛出错误，因为 utilityModule 是一个Promise，没有 magicNumber 属性
  console.log(utilityModule.magicNumber); 
} catch(e) {
  console.error("出错了！错误信息:", e.message);
  console.log("👆 看到 'undefined' 或错误是正常的，因为我们在一个Promise上访问属性。");
}


console.log("\n=== 正确用法 ===");
// ✅ 正确：使用 async/await 等待Promise完成
// 解释：我们创建了一个异步函数，并使用 `await` 关键字暂停执行，
// 直到 `import()` Promise 解析出模块对象，然后才能安全地访问其属性。
async function correctlyLoadModule() {
  try {
    const utilityModule = await import(moduleUrl);
    console.log("成功获取模块内容:", utilityModule.magicNumber);
  } catch(e) {
    console.error("加载失败:", e);
  } finally {
    URL.revokeObjectURL(moduleUrl);
  }
}
correctlyLoadModule();
```

### 🚀 Level 4: 实战应用（真实场景）
**🚀 科幻冒险场景：星际通讯翻译器**

你是一名星际探险家，降落在一个未知星球。你的飞船AI会根据你遇到的不同外星生物，动态加载相应的翻译模块来帮助你沟通。

```javascript
// 模拟外星语言翻译模块
// 模块1: Glooporian (黏液族) - 它们的语言是冒泡声
const gloopTranslatorCode = `
  export default function translate(message) {
    const translation = message.split('').map(char => 'gloop-').join('');
    return \`[黏液族语破译]: ${translation} (听起来像友好的冒泡声)\`;
  }
`;
// 模块2: Siliconoid (硅基生命) - 它们通过晶体振动沟通
const siliconTranslatorCode = `
  export default function translate(message) {
    const translation = message.split('').reverse().join('');
    return \`[硅基体频率分析]: ${translation} (一种高频水晶谐振)\`;
  }
`;

// 创建模块的内存URL
const gloopBlob = new Blob([gloopTranslatorCode], { type: 'application/javascript' });
const siliconBlob = new Blob([siliconTranslatorCode], { type: 'application/javascript' });
const gloopModuleUrl = URL.createObjectURL(gloopBlob);
const siliconModuleUrl = URL.createObjectURL(siliconBlob);

const alienEncounters = [
  { type: 'Glooporian', message: 'Hello' },
  { type: 'Siliconoid', message: 'Danger' },
  { type: 'Unknown', message: '???' }
];

async function communicateWithAlien(encounter) {
  console.log(`\n--- 遭遇新生物: ${encounter.type} ---`);
  console.log(`原始信息: "${encounter.message}"`);
  
  let translatorUrl;
  if (encounter.type === 'Glooporian') {
    translatorUrl = gloopModuleUrl;
  } else if (encounter.type === 'Siliconoid') {
    translatorUrl = siliconModuleUrl;
  } else {
    console.log("[AI提示]: 未知生物类型，无法加载翻译模块。请保持警惕！");
    return;
  }
  
  try {
    console.log(`[AI]: 正在为 ${encounter.type} 加载专用翻译模块...`);
    const { default: translate } = await import(translatorUrl);
    const translatedMessage = translate(encounter.message);
    console.log(translatedMessage);
  } catch (error) {
    console.error("[AI警告]: 翻译模块加载失败！通讯中断。", error);
  }
}

async function startAdventure() {
  console.log("🚀 开始星球探索...");
  for (const encounter of alienEncounters) {
    await communicateWithAlien(encounter);
  }
  console.log("\n--- 探索结束 ---");
  
  // 清理内存中的模块URL
  URL.revokeObjectURL(gloopModuleUrl);
  URL.revokeObjectURL(siliconModuleUrl);
}

startAdventure();
```

### 💡 记忆要点
- **返回Promise**: 动态 `import(path)` 返回一个Promise，而不是模块本身，必须用 `.then()` 或 `async/await` 来处理。
- **按需加载**: 它是实现代码分割（Code Splitting）的核心技术，只在需要时加载代码，优化性能。
- **位置灵活**: 与只能在顶层使用的静态`import`不同，动态`import()`可以写在函数、条件语句等任何代码块中。

<!--
metadata:
  syntax: ["import", "async", "await"]
  pattern: ["dynamic-import", "async-await"]
  api: ["Promise", "Blob", "URL.createObjectURL", "URL.revokeObjectURL"]
  concept: ["modules", "asynchronous-programming", "code-splitting"]
  difficulty: advanced
  dependencies: ["无"]
  related: ["js-sec-7-2-1", "js-sec-6-1-1"]
-->