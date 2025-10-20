好的，作为一名专业的JavaScript教育专家，我将为你生成关于"Cookie"的教学内容。内容将严格按照你要求的格式和风格，确保清晰、实用且富有吸引力。

---

## Cookie

### 🎯 核心概念
Cookie 解决了 **“让网站记住你”** 的问题。由于HTTP协议是无状态的，服务器无法知道两次请求是否来自同一个用户。Cookie就像是网站发给你的一个临时身份证，存储在你的浏览器里，当你再次访问该网站时，浏览器会带上这个身份证，网站就能认出你，从而提供个性化的服务，比如保持登录状态、记住购物车商品等。

### 📚 Level 1: 基础认知（30秒理解）
在浏览器中，你可以通过 `document.cookie` 来设置一个小小的文本信息。这就像给网站贴一张便利贴，告诉它一些事情。

> **注意**：以下所有代码都需要在浏览器的开发者工具（Console）中运行，因为 `document.cookie` 是浏览器环境特有的API。

```javascript
// 在浏览器的Console中运行此代码

// 设置一个最简单的cookie
// 格式是 "key=value"
document.cookie = "username=CodeMaster";

// 读取cookie
// document.cookie会返回当前网站所有可访问的cookie，以分号分隔的字符串
console.log("当前网站的Cookie是:", document.cookie);

// 清理我们设置的cookie，以便下次演示
// 将过期时间设置为一个过去的时间点即可删除
document.cookie = "username=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
console.log("清理后的Cookie是:", document.cookie);
```

### 📈 Level 2: 核心特性（深入理解）
Cookie 不仅仅是简单的键值对，它还有一些重要的属性来控制其生命周期和作用域。

#### 特性1: 过期时间（`expires` 和 `max-age`）
默认情况下，Cookie是“会话Cookie”，关闭浏览器后就会消失。我们可以设置一个过期时间，让它在用户的硬盘上存活更久。

```javascript
// 在浏览器的Console中运行此代码

// --- 使用 expires 设置过期时间 ---
// 创建一个表示一天后的日期对象
const d = new Date();
d.setTime(d.getTime() + (24 * 60 * 60 * 1000)); // 24小时
const expires = "expires=" + d.toUTCString();

// 设置一个将在24小时后过期的cookie
document.cookie = "user_preference=dark_mode; " + expires;
console.log("设置了带 expires 的Cookie:", document.cookie);


// --- 使用 max-age 设置有效期（单位：秒） ---
// 设置一个将在1小时（3600秒）后过期的cookie
// max-age比expires更现代，优先级也更高
document.cookie = "session_id=xyz123; max-age=3600";
console.log("设置了带 max-age 的Cookie:", document.cookie);

// 你可以在浏览器的 Application -> Cookies 面板中看到它们的过期时间
```

#### 特性2: 读取与解析
`document.cookie` 返回的是一个包含所有Cookie的字符串，我们需要自己动手解析它，才能拿到特定键的值。

```javascript
// 在浏览器的Console中运行此代码

// 先设置几个不同的cookie，模拟真实环境
document.cookie = "username=HeroCoder";
document.cookie = "level=99";
document.cookie = "theme=space";

function getCookie(name) {
  // 1. 获取所有cookie字符串
  const allCookies = document.cookie;
  console.log("获取到的完整Cookie字符串:", allCookies);

  // 2. 按分号和空格分割成数组
  const cookiePairs = allCookies.split('; ');

  // 3. 遍历数组寻找目标cookie
  for (let i = 0; i < cookiePairs.length; i++) {
    const pair = cookiePairs[i].split('=');
    const key = pair[0];
    const value = pair[1];
    if (key === name) {
      // 找到了！返回解码后的值
      return decodeURIComponent(value);
    }
  }
  // 没找到
  return null;
}

// 测试我们的函数
const user = getCookie("username");
const userLevel = getCookie("level");

console.log(`欢迎回来, ${user}! 你的等级是 ${userLevel}。`);

// 清理本次演示设置的cookies
document.cookie = "username=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
document.cookie = "level=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
document.cookie = "theme=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
```

### 🔍 Level 3: 对比学习（避免陷阱）
在设置Cookie值时，如果值包含特殊字符（如 `;`、`=`、空格），会破坏Cookie的结构，导致解析错误。

```javascript
// 在浏览器的Console中运行此代码

// 准备一个包含特殊字符的数据
const userProfile = {
  name: "Dr. Evil; Jr.",
  city: "New York"
};
const profileString = JSON.stringify(userProfile);

console.log("=== 错误用法 ===");
// ❌ 直接将包含特殊字符的字符串作为cookie值
document.cookie = `profile=${profileString}`;

// 读取时，因为分号的存在，cookie字符串被意外截断
console.log("直接存储后读取的Cookie字符串:", document.cookie);
// 尝试解析，很可能会失败或得到不完整的数据
const brokenValue = document.cookie.split('=')[1];
console.log("解析出的错误值:", brokenValue); // 输出 "{"name":"Dr. Evil"
console.error("❌ 错误：值被分号截断了！");


console.log("\n=== 正确用法 ===");
// ✅ 使用 encodeURIComponent 对值进行编码
const encodedProfileString = encodeURIComponent(profileString);
document.cookie = `profile=${encodedProfileString}`;

console.log("编码后存储的Cookie字符串:", document.cookie);

// 读取时，先获取到完整编码后的值，再用 decodeURIComponent 解码
function getEncodedCookie(name) {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  if (match) {
    return decodeURIComponent(match[2]);
  }
  return null;
}
const correctValue = getEncodedCookie("profile");
console.log("正确解码后的值:", correctValue);
const parsedProfile = JSON.parse(correctValue);
console.log(`✅ 正确：成功获取到用户 ${parsedProfile.name} 的信息，他来自 ${parsedProfile.city}`);

// 清理cookie
document.cookie = "profile=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
```

### 🚀 Level 4: 实战应用（真实场景）
**场景：🐾 虚拟宠物互动养成游戏**

我们来创建一个简单的虚拟宠物。它的名字、饥饿度和快乐值将保存在Cookie中。这样即使用户刷新了页面，宠物的状态也能被记住。

```javascript
// 在浏览器的Console中运行此代码

// --- 宠物状态管理工具 ---
const petManager = {
  // 从Cookie加载宠物状态
  loadStatus: function() {
    const petCookie = this.getCookie('virtualPet');
    if (petCookie) {
      console.log("找到了之前的宠物记录！正在唤醒它...");
      return JSON.parse(petCookie);
    } else {
      console.log("你好，新主人！请为你的宠物取个名字吧。");
      return { name: '蛋仔', hunger: 50, happiness: 50 };
    }
  },
  // 将宠物状态保存到Cookie，有效期为7天
  saveStatus: function(pet) {
    const petString = JSON.stringify(pet);
    const expires = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toUTCString();
    document.cookie = `virtualPet=${encodeURIComponent(petString)}; expires=${expires}; path=/`;
    console.log(`[系统消息] ${pet.name} 的状态已保存到Cookie。`);
  },
  // 读取特定cookie的辅助函数
  getCookie: function(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return decodeURIComponent(parts.pop().split(';').shift());
  }
};

// --- 宠物互动函数 ---
function feed(pet) {
  console.log(`你喂了 ${pet.name} 一块美味的饼干！🍪`);
  pet.hunger = Math.max(0, pet.hunger - 15);
  pet.happiness += 5;
  displayStatus(pet);
  petManager.saveStatus(pet);
}

function play(pet) {
  console.log(`你和 ${pet.name} 玩了抛球游戏！🎾`);
  pet.hunger += 10;
  pet.happiness = Math.min(100, pet.happiness + 15);
  displayStatus(pet);
  petManager.saveStatus(pet);
}

function displayStatus(pet) {
  console.log(`--- ${pet.name}的当前状态 ---`);
  console.log(`❤️ 快乐值: ${pet.happiness}/100`);
  console.log(`🍔 饥饿度: ${pet.hunger}/100`);
  if (pet.happiness > 80) console.log(`${pet.name} 看上去非常开心！😄`);
  if (pet.hunger > 70) console.log(`${pet.name} 的肚子在咕咕叫，它好像饿了...😟`);
}

// --- 游戏开始 ---
console.log("--- 欢迎来到虚拟宠物世界！ ---");
let myPet = petManager.loadStatus();
displayStatus(myPet);

console.log("\n--- 让我们和宠物互动一下 ---");
// 模拟互动
feed(myPet);
play(myPet);

console.log("\n💡 提示：现在刷新页面，然后重新运行这段代码，你会发现宠物的状态被记住了！");
```

### 💡 记忆要点
- **要点1**：Cookie是存储在浏览器端的小段文本，用于在多次HTTP请求间维持状态。
- **要点2**：操作Cookie使用 `document.cookie`，但它返回一个需要手动解析的字符串，并非一个方便的对象。
- **要点3**：存储在Cookie中的值，如果可能包含特殊字符，务必使用 `encodeURIComponent` 编码和 `decodeURIComponent` 解码，以保证数据完整性。

<!--
metadata:
  syntax: [variable-declaration, function]
  pattern: [string-manipulation]
  api: [document.cookie, console.log, encodeURIComponent, decodeURIComponent, Date, JSON.stringify, JSON.parse]
  concept: [client-side-storage, persistence, state-management]
  difficulty: intermediate
  dependencies: [无]
  related: [js-sec-8-2-2, js-sec-8-2-3]
-->