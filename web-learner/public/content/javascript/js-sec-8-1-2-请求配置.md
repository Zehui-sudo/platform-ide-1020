## 请求配置

### 🎯 核心概念
请求配置允许我们在发送网络请求时，除了URL之外，还能精细地控制请求的各种细节，如请求方法（GET、POST等）、请求头（Headers）和请求体（Body），从而实现与服务器的复杂数据交互。

### 📚 Level 1: 基础认知（30秒理解）
最基础的`fetch`请求默认使用`GET`方法。我们可以通过传递第二个参数——一个配置对象，来明确指定请求的细节，即使只是最简单的`GET`请求。

```javascript
// 场景：预测一个名字的可能年龄
const nameToPredict = 'alice';
const apiUrl = `https://api.agify.io?name=${nameToPredict}`;

// 写法1: 不带配置对象（默认GET）
fetch(apiUrl)
  .then(response => response.json())
  .then(data => {
    console.log(`[默认GET] 预测 '${nameToPredict}' 的年龄是:`, data.age);
  });

// 写法2: 明确使用配置对象指定GET方法
fetch(apiUrl, { method: 'GET' })
  .then(response => response.json())
  .then(data => {
    console.log(`[配置GET] 预测 '${nameToPredict}' 的年龄是:`, data.age);
  });
// 输出：
// [默认GET] 预测 'alice' 的年龄是: 32
// [配置GET] 预测 'alice' 的年龄是: 32
```

### 📈 Level 2: 核心特性（深入理解）
掌握请求配置的关键在于理解`method`, `headers`, 和 `body`这三个核心属性。

#### 特性1: 指定请求方法 (`method`) 和请求体 (`body`)
`GET`请求通常用于获取数据，而`POST`请求用于向服务器提交数据。提交数据时，数据内容放在`body`属性中。

```javascript
// 使用一个能回显请求信息的公开服务(httpbin.org)来演示
async function postDataExample() {
  const userData = {
    username: 'AstroExplorer',
    level: 12,
    mission: 'Collect star dust'
  };

  const response = await fetch('https://httpbin.org/post', {
    method: 'POST', // 明确指定方法为 POST
    // body 需要是字符串。通常我们将JS对象转为JSON字符串
    body: JSON.stringify(userData) 
  });

  const result = await response.json();
  
  console.log('服务器收到的数据是:');
  // result.data 是服务器解析后收到的原始body字符串
  console.log(result.data); 
  
  console.log('服务器解析后的JSON对象是:');
  // result.json 是服务器将收到的JSON字符串转回对象后的结果
  console.log(result.json);
}

postDataExample();
// 输出：
// 服务器收到的数据是:
// {"username":"AstroExplorer","level":12,"mission":"Collect star dust"}
// 服务器解析后的JSON对象是:
// { username: 'AstroExplorer', level: 12, mission: 'Collect star dust' }
```

#### 特性2: 设置请求头 (`headers`)
请求头可以向服务器提供额外信息，例如我们发送的数据格式是什么（`Content-Type`），或者我们的身份凭证（`Authorization`）。

```javascript
// 使用 httpbin.org/headers 来查看服务器收到的请求头
async function headersExample() {
  const customHeaders = {
    // 告诉服务器，我们发送的body内容是JSON格式
    'Content-Type': 'application/json',
    // 附加一个自定义的请求头，比如API密钥或认证令牌
    'Authorization': 'Bearer my-secret-token-12345',
    'X-Client-Version': '1.0.5'
  };

  const response = await fetch('https://httpbin.org/headers', {
    method: 'GET', // headers可以用于任何类型的请求
    headers: customHeaders
  });

  const result = await response.json();

  console.log('服务器确认收到的请求头信息:');
  console.log('Authorization:', result.headers.Authorization);
  console.log('Content-Type:', result.headers['Content-Type']);
  console.log('X-Client-Version:', result.headers['X-Client-Version']);
}

headersExample();
// 输出：
// 服务器确认收到的请求头信息:
// Authorization: Bearer my-secret-token-12345
// Content-Type: application/json
// X-Client-Version: 1.0.5
```

### 🔍 Level 3: 对比学习（避免陷阱）
发送JSON数据时，最常见的错误是忘记`JSON.stringify()`和设置正确的`Content-Type`。

```javascript
// 场景：向服务器注册一个新用户
async function userRegistration() {
  const newUser = { name: 'eva', role: 'pilot' };
  const apiUrl = 'https://httpbin.org/post';

  console.log("=== 错误用法 ===");
  // ❌ 错误: 直接将JS对象作为body，并且没有设置Content-Type
  // 浏览器会尝试将对象转换为字符串"[object Object]"，服务器无法正确解析。
  try {
    const badResponse = await fetch(apiUrl, {
      method: 'POST',
      body: newUser 
    });
    const badResult = await badResponse.json();
    console.log('服务器收到的错误数据:', badResult.data);
  } catch (error) {
    console.error('请求失败:', error);
  }

  console.log("\n=== 正确用法 ===");
  // ✅ 正确: 使用JSON.stringify转换对象，并设置正确的请求头
  const goodResponse = await fetch(apiUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(newUser)
  });
  const goodResult = await goodResponse.json();
  console.log('服务器收到的正确数据:', goodResult.data);
  console.log('服务器解析后的JSON:', goodResult.json);
}

userRegistration();
// 输出：
// === 错误用法 ===
// 服务器收到的错误数据: [object Object]
//
// === 正确用法 ===
// 服务器收到的正确数据: {"name":"eva","role":"pilot"}
// 服务器解析后的JSON: { name: 'eva', role: 'pilot' }
```

### 🚀 Level 4: 实战应用（真实场景）
🚀 **科幻冒险：外星语言翻译器**

你是一名星际探险家，刚降落在一颗未知星球。你的任务是使用高科技翻译器与当地的硅基生命体“格洛布”进行交流。翻译器有两种模式：

1.  **快速翻译 (GET)**: 用于翻译单个、简单的外星词汇。
2.  **深度分析 (POST)**: 用于翻译复杂的句子，需要同时上传环境数据（如大气成分、重力）以获得更精确的上下文分析。

```javascript
// 模拟我们的高科技翻译服务器 (使用httpbin.org)
const translationServer = {
  quick: (word) => `https://httpbin.org/get?word=${word}`,
  deep: 'https://httpbin.org/post'
};

// 我们的翻译器主函数
async function translateGlonk(text, context = null) {
  console.log(`--- 正在翻译: "${text}" ---`);

  if (!context) {
    // 模式1: 快速翻译 (GET)
    console.log("模式: 快速翻译 (GET)");
    const response = await fetch(translationServer.quick(text));
    const result = await response.json();
    console.log(`[翻译结果]: 服务器收到了词汇 '${result.args.word}'。初步翻译: '问候' 或 '危险'？`);
  } else {
    // 模式2: 深度分析 (POST)
    console.log("模式: 深度分析 (POST)");
    const requestPayload = {
      sentence: text,
      enviromental_context: context
    };
    
    const response = await fetch(translationServer.deep, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Translator-Model': 'Glonk-v3.5-alpha'
      },
      body: JSON.stringify(requestPayload)
    });
    const result = await response.json();
    console.log(`[翻译结果]: 服务器收到深度分析请求。`);
    console.log(`   - 句子: ${result.json.sentence}`);
    console.log(`   - 环境: 大气成分 ${result.json.enviromental_context.atmosphere}, 重力 ${result.json.enviromental_context.gravity}G`);
    console.log(`   - 分析结论: 这句话表达了对当前'${result.json.enviromental_context.atmosphere}'大气的赞美！`);
  }
  console.log("--- 翻译结束 ---\n");
}

// 开始我们的冒险！
async function startAdventure() {
  // 遇到一个简单的词汇
  await translateGlonk("Zorp!");

  // 遇到一句复杂的句子，同时扫描环境数据
  const enviromentData = {
    atmosphere: 'Methane-rich',
    gravity: 1.7
  };
  await translateGlonk("Glarth Voo Snizzle", enviromentData);
}

startAdventure();
```

### 💡 记忆要点
- **要点1**：`fetch`的第二个参数是一个配置对象，用于自定义请求。
- **要点2**：`method`属性决定HTTP请求方法（如`'GET'`, `'POST'`），是数据交互方式的基础。
- **要点3**：当使用`POST`发送JSON数据时，务必使用`JSON.stringify()`处理`body`，并设置`headers`中的`'Content-Type': 'application/json'`。

<!--
metadata:
  syntax: [async, await, const, function]
  pattern: [async-await, error-handling]
  api: [fetch, console.log, JSON.stringify]
  concept: [http-request, request-configuration, headers, body, method]
  difficulty: intermediate
  dependencies: [无]
  related: [js-sec-8-1-1]
-->