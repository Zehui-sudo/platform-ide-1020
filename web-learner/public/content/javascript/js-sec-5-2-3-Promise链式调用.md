## Promise链式调用

### 🎯 核心概念
Promise链式调用允许我们将多个异步操作按顺序串联起来，像链条一样一个接一个地执行，使得代码结构更清晰、更易读，有效解决了“回调地狱”（Callback Hell）问题。

### 📚 Level 1: 基础认知（30秒理解）
想象一个简单的流水线：第一步操作完成后，将结果传递给第二步。Promise链就是这样，通过 `.then()` 将多个步骤连接起来。

```javascript
// 创建一个立即解决的Promise，值为10
const promise = Promise.resolve(10);

promise
  .then(value => {
    // 第一个.then接收到值10
    console.log("第一步: 接收到初始值", value);
    // 将值乘以2，并返回，传递给下一步
    return value * 2;
  })
  .then(value => {
    // 第二个.then接收到上一步返回的20
    console.log("第二步: 接收到处理后的值", value);
    // 将值加上5
    return value + 5;
  })
  .then(finalValue => {
    // 第三个.then接收到最终值25
    console.log("第三步: 得到最终结果", finalValue);
  });

// 输出:
// 第一步: 接收到初始值 10
// 第二步: 接收到处理后的值 20
// 第三步: 得到最终结果 25
```

### 📈 Level 2: 核心特性（深入理解）
#### 特性1: 返回值传递
每个 `.then()` 中的回调函数可以通过 `return` 将一个值传递给链中的下一个 `.then()`。如果不返回任何东西，下一个 `.then()` 会接收到 `undefined`。

```javascript
const startPromise = new Promise((resolve, reject) => {
  console.log("开始处理...");
  setTimeout(() => {
    resolve("数据A");
  }, 500);
});

startPromise
  .then(result1 => {
    console.log("第一环: 拿到", result1);
    // 返回一个新值，传递给下一环
    return "数据B";
  })
  .then(result2 => {
    console.log("第二环: 拿到", result2);
    // 这里没有返回任何值
  })
  .then(result3 => {
    console.log("第三环: 拿到", result3); // 因为上一环没有返回，所以这里是undefined
  });

// 输出:
// 开始处理...
// (等待500ms后)
// 第一环: 拿到 数据A
// 第二环: 拿到 数据B
// 第三环: 拿到 undefined
```

#### 特性2: 返回新的Promise
这是链式调用最强大的地方。如果 `.then()` 中返回的是一个新的Promise，那么整个链条会“暂停”，等待这个新的Promise完成后，再把它的结果传递给下一个 `.then()`。这使得串联多个异步操作变得轻而易举。

```javascript
// 模拟一个异步操作：获取用户信息
function fetchUser(userId) {
  console.log(`正在获取用户 ${userId} 的信息...`);
  return new Promise(resolve => {
    setTimeout(() => {
      console.log(`✅ 用户 ${userId} 信息获取成功!`);
      resolve({ id: userId, name: "Alice" });
    }, 1000);
  });
}

// 模拟另一个异步操作：获取用户文章
function fetchPosts(user) {
  console.log(`正在获取用户 ${user.name} 的文章...`);
  return new Promise(resolve => {
    setTimeout(() => {
      console.log(`✅ 用户 ${user.name} 的文章获取成功!`);
      resolve(["文章1", "文章2"]);
    }, 1000);
  });
}

// 链式调用
fetchUser(101)
  .then(user => {
    // 第一个then接收到用户信息
    // 然后返回一个新的Promise来获取文章
    return fetchPosts(user);
  })
  .then(posts => {
    // 第二个then会等待fetchPosts完成后，接收到文章数据
    console.log("最终拿到的文章列表:", posts);
  });

// 输出:
// 正在获取用户 101 的信息...
// (等待1秒)
// ✅ 用户 101 信息获取成功!
// 正在获取用户 Alice 的文章...
// (再等待1秒)
// ✅ 用户 Alice 的文章获取成功!
// 最终拿到的文章列表: [ '文章1', '文章2' ]
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个常见的错误是“嵌套Promise”而不是“链式调用”，这会使代码重回“回调地狱”的混乱状态。

```javascript
// 模拟一个异步函数
function asyncOperation(step, delay) {
  return new Promise(resolve => {
    setTimeout(() => {
      console.log(`步骤 ${step} 完成`);
      resolve(`结果 ${step}`);
    }, delay);
  });
}

console.log("=== 错误用法：嵌套Promise ===");
// ❌ 错误做法：在.then内部嵌套另一个.then
// 这导致代码缩进越来越深，难以阅读和维护，也叫"Promise Hell"
asyncOperation(1, 500).then(result1 => {
  asyncOperation(2, 500).then(result2 => {
    asyncOperation(3, 500).then(result3 => {
      console.log("嵌套调用全部完成！", result1, result2, result3);
    });
  });
});
// 这种结构难以进行统一的错误处理

setTimeout(() => {
    console.log("\n=== 正确用法：链式调用 ===");
    // ✅ 正确做法：使用扁平的链式结构
    // 代码清晰，呈线性结构，易于理解
    asyncOperation(1, 500)
      .then(result1 => {
        // 返回一个新的Promise，链条会自动等待它完成
        return asyncOperation(2, 500);
      })
      .then(result2 => {
        return asyncOperation(3, 500);
      })
      .then(result3 => {
        console.log("链式调用全部完成！");
      })
      .catch(error => {
        // 任何一步出错，都会被这个catch捕获
        console.error("链条中出现错误:", error);
      });
}, 2000); // 延迟执行，以便和错误用法分开看


// 输出:
// === 错误用法：嵌套Promise ===
// (等待500ms)
// 步骤 1 完成
// (再等待500ms)
// 步骤 2 完成
// (再等待500ms)
// 步骤 3 完成
// 嵌套调用全部完成！ 结果 1 结果 2 结果 3
//
// === 正确用法：链式调用 ===
// (等待500ms)
// 步骤 1 完成
// (再等待500ms)
// 步骤 2 完成
// (再等待500ms)
// 步骤 3 完成
// 链式调用全部完成！
```

### 🚀 Level 4: 实战应用（真实场景）
**🎮 游戏场景：宠物小精灵进化之旅**

让我们模拟一个训练师培养小精灵的冒险过程。这个过程包含几个连续的异步步骤：找到小精灵、进行训练、最终进化。

```javascript
// 模拟异步操作：在草丛里寻找小精灵
function findPokemon() {
  console.log(" trainer: 好的，开始在草丛里搜寻... 🌿");
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const found = Math.random() > 0.3; // 70% 概率找到
      if (found) {
        const pokemon = { name: "皮卡丘", level: 1 };
        console.log(` trainer: 找到了！是一只 Lv.${pokemon.level} 的 ${pokemon.name}! ⚡️`);
        resolve(pokemon);
      } else {
        console.log(" trainer: 哎呀，什么都没找到...下次再来吧。");
        reject("未找到小精灵");
      }
    }, 1500);
  });
}

// 模拟异步操作：训练小精灵提升等级
function trainPokemon(pokemon) {
  console.log(` trainer: 开始训练 ${pokemon.name}... (ง •̀_•́)ง`);
  return new Promise(resolve => {
    setTimeout(() => {
      pokemon.level += 5;
      console.log(` trainer: 训练结束！${pokemon.name} 升到了 Lv.${pokemon.level}! ✨`);
      resolve(pokemon);
    }, 2000);
  });
}

// 模拟异步操作：尝试进化
function evolvePokemon(pokemon) {
  console.log(` trainer: ${pokemon.name} 身上发出了耀眼的光芒... क्या?`);
  return new Promise(resolve => {
    setTimeout(() => {
      if (pokemon.level >= 5) {
        pokemon.name = "雷丘";
        console.log(` trainer: 恭喜！${pokemon.name} 进化成功！变成了 ${pokemon.name}! 🏆`);
        resolve(pokemon);
      } else {
        console.log(` trainer: 光芒消失了...看来等级还不够。`);
        resolve(pokemon); // 即使没进化，也把当前状态传下去
      }
    }, 1500);
  });
}

// --- 开始我们的冒险之旅 ---
findPokemon()
  .then(pokemon => {
    // 找到后，进行训练，返回训练的Promise
    return trainPokemon(pokemon);
  })
  .then(trainedPokemon => {
    // 训练完后，尝试进化，返回进化的Promise
    return evolvePokemon(trainedPokemon);
  })
  .then(finalPokemon => {
    // 进化结束后，展示最终状态
    console.log(`\n--- 冒险日志 ---`);
    console.log(`最终伙伴: ${finalPokemon.name}`);
    console.log(`等级: ${finalPokemon.level}`);
    console.log(` trainer: 我们成为了更强的伙伴！🎉`);
  })
  .catch(error => {
    // 如果在findPokemon步骤失败，链条会直接跳到这里
    console.error(`\n--- 冒险日志 ---`);
    console.error(`本次冒险失败: ${error}`);
  });
```

### 💡 记忆要点
- **返回即传递**：`.then()` 方法中的 `return` 值会作为下一个 `.then()` 的输入参数。
- **返回Promise则等待**：如果在 `.then()` 中返回一个新的Promise，整个链条会等待这个新Promise完成后再继续执行。
- **扁平化结构**：始终追求扁平的 `.then().then()...` 结构，避免嵌套，这样代码更清晰，错误处理也更方便。

<!--
metadata:
  syntax: [function, arrow-function, const]
  pattern: [promise-chain, error-handling]
  api: [Promise, then, catch, resolve, reject, setTimeout, console.log]
  concept: [asynchronous, callback]
  difficulty: intermediate
  dependencies: [无]
  related: [js-sec-5-2-1, js-sec-5-2-2]
-->