好的，作为一名专业的JavaScript教育专家，我将为你生成关于“请求拦截”的教学内容。

---

## 请求拦截

### 🎯 核心概念
请求拦截是一种编程模式，允许我们在网络请求被**发送前**或响应被**接收后**，对其进行全局的、统一的检查、修改或处理。它就像是在客户端和服务器之间设立了一个“检查站”，所有进出的“包裹”（请求和响应）都要经过这里，从而实现如自动添加认证信息、统一错误处理、请求日志记录等功能，避免在每个请求点重复编写代码。

### 📚 Level 1: 基础认知（30秒理解）
想象一下，我们有一个自定义的`fetch`函数。请求拦截最基础的形式，就是在真正发起请求前，先执行一个我们定义的“拦截”函数，比如打印一条日志。

```javascript
// 模拟一个网络请求函数
function fakeApiCall(url, options) {
  console.log(`[API] 正在向 ${url} 发送请求...`);
  return Promise.resolve({ success: true, data: `来自 ${url} 的数据` });
}

// 创建一个带有请求拦截功能的 fetch 包装器
function createFetchWithInterceptor(apiCall) {
  const interceptor = (url, options) => {
    // 这是我们的拦截器：在请求发送前，打印日志
    console.log(`[拦截器] 准备发送请求到: ${url}`);
    // 拦截器处理完后，调用原始的 API 函数
    return apiCall(url, options);
  };
  return interceptor;
}

const myFetch = createFetchWithInterceptor(fakeApiCall);

// 使用我们带有拦截功能的 fetch
myFetch('https://api.example.com/data', { method: 'GET' })
  .then(response => {
    console.log('[客户端] 收到响应:', response);
  });
```

### 📈 Level 2: 核心特性（深入理解）
拦截器不仅能“看”，还能“改”。它们可以修改请求配置，也可以处理响应数据。

#### 特性1: 修改请求 (Request Modification)
拦截器最强大的功能之一是在请求发送前动态修改它。最常见的场景是为所有请求自动添加认证令牌（Token）。

```javascript
// 模拟一个需要认证的 API
async function fakeSecureApiCall(url, options) {
  console.log(`[API] 正在向 ${url} 发送请求，配置为:`, options);
  if (options.headers && options.headers['Authorization'] === 'Bearer secret-token') {
    return { status: 200, data: '机密数据获取成功！' };
  } else {
    return { status: 401, error: '未授权访问' };
  }
}

// 创建一个可以修改请求的拦截器系统
class ApiClient {
  constructor() {
    this.requestInterceptor = null;
  }

  // 设置请求拦截器
  useRequestInterceptor(interceptor) {
    this.requestInterceptor = interceptor;
  }

  async fetch(url, options = {}) {
    let modifiedOptions = options;
    if (this.requestInterceptor) {
      // 如果有拦截器，用它来处理（可能修改）配置
      console.log('[系统] 请求已进入拦截器...');
      modifiedOptions = this.requestInterceptor(modifiedOptions);
    }
    return fakeSecureApiCall(url, modifiedOptions);
  }
}

const client = new ApiClient();

// 定义一个拦截器，为所有请求添加 Authorization 头
client.useRequestInterceptor((options) => {
  const token = 'secret-token';
  const modifiedOptions = {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    }
  };
  console.log('[拦截器] 已自动添加认证Token！');
  return modifiedOptions; // 必须返回修改后的配置
});

// 发起请求，无需手动添加 Token
client.fetch('https://api.secret.com/user')
  .then(response => console.log('[客户端] 响应:', response));
```

#### 特性2: 处理响应 (Response Handling)
拦截器同样可以捕获响应，在数据返回给调用者之前进行统一处理。例如，当服务器返回特定错误码时，可以全局处理，如自动跳转到登录页或弹出提示。

```javascript
// 模拟一个可能成功也可能失败的 API
async function fakeApiCall(url) {
  console.log(`[API] 正在向 ${url} 发送请求...`);
  // 模拟一个会话过期的场景
  if (url.includes('expired')) {
    return { status: 401, error: '会话已过期，请重新登录' };
  }
  return { status: 200, data: '用户个人资料' };
}

// 创建一个同时支持请求和响应拦截的系统
class ApiClient {
  constructor() {
    this.responseInterceptor = null;
  }

  useResponseInterceptor(interceptor) {
    this.responseInterceptor = interceptor;
  }

  async fetch(url, options = {}) {
    let response = await fakeApiCall(url, options);
    
    if (this.responseInterceptor) {
      console.log('[系统] 响应已进入拦截器...');
      // 响应拦截器可以处理或转换响应
      response = this.responseInterceptor(response);
    }
    return response;
  }
}

const client = new ApiClient();

// 定义一个响应拦截器，专门处理 401 错误
client.useResponseInterceptor((response) => {
  if (response.status === 401) {
    console.error('[拦截器] 检测到未授权(401)！正在模拟跳转到登录页...');
    // 在真实应用中，这里会执行 window.location.href = '/login'
    // 这里我们返回一个更友好的错误信息
    return { status: 'processed_error', message: '请登录后再试' };
  }
  // 如果不是 401，原样返回响应
  return response;
});

// 场景1: 请求一个会过期的资源
client.fetch('https://api.example.com/profile?session=expired')
  .then(result => console.log('[客户端] 收到处理后的结果:', result));

// 场景2: 请求一个正常的资源
client.fetch('https://api.example.com/profile?session=valid')
  .then(result => console.log('\n[客户端] 收到正常结果:', result));
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个常见的错误是在拦截器中忘记返回处理后的对象（请求配置或响应），这会中断数据流，导致后续操作失败。

```javascript
// 模拟 API 调用
async function apiCall(url, options) {
  if (!options) {
    throw new Error("[API] 错误：请求配置 (options) 未定义！");
  }
  console.log("[API] 收到请求配置:", options);
  return { success: true };
}

// 带有拦截器的客户端
class ApiClient {
  constructor() {
    this.requestInterceptor = null;
  }
  use(interceptor) {
    this.requestInterceptor = interceptor;
  }
  async fetch(url, options = {}) {
    let processedOptions = options;
    if (this.requestInterceptor) {
      processedOptions = this.requestInterceptor(options);
    }
    // 如果 processedOptions 是 undefined，这里会报错
    return apiCall(url, processedOptions);
  }
}

console.log("=== 错误用法 ===");
// ❌ 拦截器没有返回任何东西 (隐式返回 undefined)
const badClient = new ApiClient();
badClient.use((options) => {
  console.log("[错误拦截器] 正在处理请求...");
  options.headers = { 'X-Powered-By': 'Magic' };
  // 忘记 return options;
});

badClient.fetch('https://example.com/data', {})
  .catch(error => console.error(error.message));
// 解释: 这个拦截器修改了 options 对象，但没有返回它。
// ApiClient 的 fetch 方法接收到的 `processedOptions` 将是 `undefined`，
// 导致传递给 `apiCall` 的是 `undefined`，从而引发错误。

console.log("\n=== 正确用法 ===");
// ✅ 拦截器总是返回处理后的配置对象
const goodClient = new ApiClient();
goodClient.use((options) => {
  console.log("[正确拦截器] 正在处理请求...");
  const newOptions = { ...options, headers: { 'X-Powered-By': 'JavaScript' } };
  return newOptions; // 必须返回配置对象
});

goodClient.fetch('https://example.com/data', {})
  .then(response => console.log("[客户端] 成功!", response))
  .catch(error => console.error(error.message));
// 解释: 正确的拦截器接收配置，进行修改，然后返回修改后的新配置对象。
// 这确保了数据流的连续性，`apiCall` 能接收到有效的配置。
```

### 🚀 Level 4: 实战应用（真实场景）
**场景：🚀 科幻冒险 - 星际通讯系统**

我们正在开发一个用于太空飞船的通讯系统 `GalacticComms`。我们需要向不同外星文明发送消息。这个系统必须通过请求拦截器自动完成两件事：
1.  **加密协议**：为所有发出的消息自动添加 `X-Encryption-Protocol: AES-256` 头。
2.  **通用翻译器**：如果消息是发往"Zorg-Prime"星球的，自动将消息内容从人类语言翻译成Zorg语。

```javascript
// 模拟一个星际通讯网络
async function sendIntergalacticMessage(planet, message) {
  console.log(`[网络层] 正在向 ${planet} 传输消息...`);
  console.log(`[网络层] 传输内容:`, message);

  if (!message.headers || message.headers['X-Encryption-Protocol'] !== 'AES-256') {
    return { status: 'failed', reason: '传输失败：未加密的信道！' };
  }
  if (planet === 'Zorg-Prime' && !message.body.includes('glorp')) {
     return { status: 'failed', reason: '传输失败：Zorg人无法理解该消息！' };
  }
  
  return { status: 'ok', confirmation: `消息已成功抵达 ${planet}` };
}

// 我们的星际通讯系统
class GalacticComms {
  constructor() {
    this.requestInterceptors = [];
  }

  // 添加一个拦截器
  addInterceptor(interceptor) {
    this.requestInterceptors.push(interceptor);
  }

  // 发送消息
  async sendMessage(planet, text) {
    console.log(`\n--- 准备向 ${planet} 发送新消息 ---`);
    let message = {
      body: text,
      headers: {}
    };

    // 依次通过所有拦截器
    for (const interceptor of this.requestInterceptors) {
      message = interceptor(planet, message);
    }

    return sendIntergalacticMessage(planet, message);
  }
}

// 创建通讯系统实例
const comms = new GalacticComms();

// 1. 安装“加密协议”拦截器
comms.addInterceptor((planet, message) => {
  console.log('[拦截器 1 - 加密] 正在为消息添加 AES-256 加密协议...');
  const encryptedMessage = {
    ...message,
    headers: {
      ...message.headers,
      'X-Encryption-Protocol': 'AES-256'
    }
  };
  return encryptedMessage;
});

// 2. 安装“通用翻译器”拦截器
comms.addInterceptor((planet, message) => {
  if (planet === 'Zorg-Prime') {
    console.log('[拦截器 2 - 翻译] 检测到目标是Zorg-Prime，启动通用翻译器...');
    const translatedBody = message.body.replace('Hello', 'Glorp Zorp');
    return { ...message, body: translatedBody };
  }
  // 如果不是发往Zorg-Prime，则不作任何翻译
  console.log('[拦截器 2 - 翻译] 非Zorg目标，无需翻译。');
  return message;
});

// 使用通讯系统发送消息
async function runMissions() {
  // 任务1: 向火星发送问候 (无需翻译)
  const marsResponse = await comms.sendMessage('Mars', 'Hello, Mars!');
  console.log('[舰长日志] 火星任务结果:', marsResponse);

  // 任务2: 向Zorg-Prime发送问候 (需要自动翻译)
  const zorgResponse = await comms.sendMessage('Zorg-Prime', 'Hello, great leader!');
  console.log('[舰长日志] Zorg-Prime任务结果:', zorgResponse);
}

runMissions();
```

### 💡 记忆要点
- **集中处理**：请求拦截器是实现网络请求全局、集中化处理的利器，避免代码重复。
- **可修改性**：拦截器不仅能读取请求/响应，更核心的是能够**修改**它们，例如添加headers或转换数据格式。
- **链式责任**：每个拦截器都必须将处理后的对象（请求配置或响应）返回，以确保数据流能够顺利传递到下一个环节（下一个拦截器或最终的API调用）。

<!--
metadata:
  syntax: [async, await, function, arrow-function, class, const, let]
  pattern: [async-await, promise-chain, error-handling, closure]
  api: [Promise, console.log]
  concept: [higher-order-function, middleware, interception, pattern]
  difficulty: advanced
  dependencies: [无]
  related: []
-->