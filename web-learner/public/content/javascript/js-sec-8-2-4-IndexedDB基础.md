## IndexedDB基础

### 🎯 核心概念
IndexedDB 是一个内置在浏览器中的客户端数据库，它允许你存储大量的结构化数据（包括文件/Blobs），并为这些数据创建索引以实现高性能搜索。它解决了 `localStorage` 只能存储少量字符串数据的局限性，使得 Web 应用可以实现复杂的离线功能和数据管理。

### 📚 Level 1: 基础认知（30秒理解）
IndexedDB 的所有操作都是异步的。第一步是“打开”一个数据库。如果数据库不存在，它会被创建。这个过程不会立即完成，而是通过事件回调来通知我们结果。

```javascript
// Level 1: 打开或创建一个名为 'MyTestDatabase' 的数据库
// indexedDB.open(databaseName, version)
// 版本号必须是整数
const request = indexedDB.open('MyTestDatabase', 1);

// 当数据库打开失败时触发
request.onerror = function(event) {
  console.error("数据库打开失败:", event.target.error);
};

// 当数据库成功打开时触发
request.onsuccess = function(event) {
  const db = event.target.result;
  console.log("数据库打开成功!", db);
  // 使用完毕后，关闭数据库连接
  db.close();
};

// 当数据库需要升级版本时触发（首次创建时也会触发）
request.onupgradeneeded = function(event) {
  const db = event.target.result;
  console.log("数据库版本升级或首次创建。", db);
};
```

### 📈 Level 2: 核心特性（深入理解）
理解 IndexedDB 的关键在于掌握“对象存储”和“事务”。

#### 特性1: 对象存储（Object Store）和版本升级
数据存储在“对象存储”中，类似于 SQL 数据库中的“表”。对象存储只能在 `onupgradeneeded` 事件中创建或修改，这个事件在数据库版本变化时触发。

```javascript
// Level 2, Feature 1: 创建一个对象存储
const dbName = 'MyGameDB';
const dbVersion = 1;

const request = indexedDB.open(dbName, dbVersion);

request.onerror = (event) => {
  console.error(`打开数据库 '${dbName}' 失败:`, event.target.error);
};

request.onsuccess = (event) => {
  console.log(`成功打开数据库 '${dbName}' 版本 ${dbVersion}`);
  const db = event.target.result;
  db.close(); // 完成操作后关闭
};

// onupgradeneeded 是创建和修改数据库结构的唯一地方
request.onupgradeneeded = (event) => {
  console.log("数据库需要升级，正在创建对象存储...");
  const db = event.target.result;

  // 创建一个名为 'players' 的对象存储
  // keyPath 指定了对象中哪个属性是主键
  if (!db.objectStoreNames.contains('players')) {
    const objectStore = db.createObjectStore('players', { keyPath: 'id' });
    console.log("对象存储 'players' 创建成功！");

    // 可以在这里创建索引，用于未来高效查询
    // objectStore.createIndex('name', 'name', { unique: false });
    // console.log("为 'name' 字段创建索引成功！");
  }
};
```

#### 特性2: 事务（Transactions）
所有的数据读写操作（增删改查）都必须在“事务”中进行。事务保证了数据操作的原子性，要么全部成功，要么全部失败。

```javascript
// Level 2, Feature 2: 在事务中添加数据
const dbName = 'MyGameDB_L2_F2'; // 使用新库名避免与上例冲突
const dbVersion = 1;

const request = indexedDB.open(dbName, dbVersion);

request.onupgradeneeded = (event) => {
  const db = event.target.result;
  if (!db.objectStoreNames.contains('players')) {
    db.createObjectStore('players', { keyPath: 'id' });
  }
};

request.onsuccess = (event) => {
  console.log("数据库已准备好，开始事务...");
  const db = event.target.result;

  // 1. 创建一个事务
  // 参数1: 要操作的对象存储名数组
  // 参数2: 模式 ('readonly' 或 'readwrite')
  const transaction = db.transaction(['players'], 'readwrite');

  // 2. 获取对象存储
  const playersStore = transaction.objectStore('players');

  // 3. 创建要添加的数据
  const newPlayer = { id: 'player001', name: 'Pikachu', level: 5 };

  // 4. 添加数据
  const addRequest = playersStore.add(newPlayer);

  addRequest.onsuccess = () => {
    console.log(`玩家 '${newPlayer.name}' 已成功添加到 'players' 仓库！`);
  };

  addRequest.onerror = (e) => {
    console.error(`添加玩家失败:`, e.target.error);
  };

  // 事务完成后关闭数据库
  transaction.oncomplete = () => {
    console.log("所有添加操作的事务已完成。");
    db.close();
  };
};

request.onerror = (event) => {
  console.error("数据库打开失败:", event.target.error);
};
```

### 🔍 Level 3: 对比学习（避免陷阱）
新手最常见的错误是忘记 IndexedDB 的异步性，试图在数据库连接成功前就进行操作。

```javascript
// Level 3: 对比异步操作的时机
const dbName = 'MyMistakeDB';
const dbVersion = 1;

console.log("=== 错误用法 ===");
// ❌ 错误：在 open() 请求之后立即尝试使用数据库
try {
  const request = indexedDB.open(dbName, 1);
  // 此时 request 刚刚发出，数据库连接还未建立成功
  // db 变量是 undefined，因为 onsuccess 回调还没执行
  const db = request.result; 
  const transaction = db.transaction(['users'], 'readwrite'); // 这行会立即抛出错误
  console.log("错误代码中的事务:", transaction);
} catch (error) {
  console.error("❌ 错误用法捕获到异常:", error.message);
  console.log("解释：不能在 onsuccess 事件触发前访问 request.result。IndexedDB 操作是异步的，必须在回调函数中处理。");
}


console.log("\n=== 正确用法 ===");
// ✅ 正确：所有数据库操作都在 onsuccess 事件回调函数中进行
const correctRequest = indexedDB.open(dbName, 1);

correctRequest.onupgradeneeded = event => {
  const db = event.target.result;
  if (!db.objectStoreNames.contains('users')) {
    db.createObjectStore('users', { keyPath: 'id' });
  }
};

correctRequest.onerror = event => {
  console.error("✅ 正确用法中的数据库错误:", event.target.error);
};

correctRequest.onsuccess = event => {
  console.log("✅ 数据库连接成功，现在可以安全地进行操作了。");
  const db = event.target.result;
  const transaction = db.transaction(['users'], 'readwrite');
  console.log("✅ 成功创建事务:", transaction);

  transaction.oncomplete = () => {
    console.log("✅ 事务完成，关闭数据库。");
    db.close();
  };
  
  transaction.onerror = (e) => {
     console.error("✅ 事务中发生错误:", e.target.error);
  }
};
```

### 🚀 Level 4: 实战应用（真实场景）
**场景：🐾 虚拟宠物互动养成游戏**

我们来创建一个简单的虚拟宠物养成游戏。你可以创造一只宠物，给它喂食，然后检查它的状态。所有宠物的状态都会保存在 IndexedDB 中，这样即使关闭浏览器再打开，你的宠物还在！

```javascript
// Level 4: 虚拟宠物养成游戏
const DBNAME = "PetPalDB";
const DBVERSION = 1;
const STORENAME = "pets";

// --- 数据库助手函数 ---
function getDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DBNAME, DBVERSION);
    request.onerror = event => reject(`数据库错误: ${event.target.error}`);
    request.onsuccess = event => resolve(event.target.result);
    request.onupgradeneeded = event => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains(STORENAME)) {
        db.createObjectStore(STORENAME, { keyPath: "id", autoIncrement: true });
        console.log("宠物小屋（对象存储）建好啦！");
      }
    };
  });
}

// --- 宠物操作函数 ---

// 创造一只新宠物
async function createPet(name, type) {
  console.log(`正在创造一只新的宠物: ${name} (${type})...`);
  const db = await getDB();
  const transaction = db.transaction(STORENAME, "readwrite");
  const store = transaction.objectStore(STORENAME);
  const pet = { name, type, happiness: 100, hunger: 0 };
  const request = store.add(pet);

  return new Promise((resolve, reject) => {
    request.onsuccess = event => {
      console.log(`🎉 欢迎来到新世界, ${name}! 你的ID是 ${event.target.result}`);
      resolve(event.target.result);
    };
    request.onerror = event => reject(`创造宠物失败: ${event.target.error}`);
    transaction.oncomplete = () => db.close();
  });
}

// 给宠物喂食
async function feedPet(petId) {
  console.log(`准备给ID为 ${petId} 的宠物喂好吃的...`);
  const db = await getDB();
  const transaction = db.transaction(STORENAME, "readwrite");
  const store = transaction.objectStore(STORENAME);
  const getRequest = store.get(petId);

  getRequest.onsuccess = () => {
    const pet = getRequest.result;
    if (pet) {
      pet.hunger = Math.max(0, pet.hunger - 20); // 减少饥饿度
      pet.happiness += 10; // 增加开心值
      const updateRequest = store.put(pet);
      updateRequest.onsuccess = () => {
        console.log(`🍖 ${pet.name} 吃得很开心！饥饿度: ${pet.hunger}, 开心值: ${pet.happiness}`);
      };
    } else {
      console.log(`咦？找不到ID为 ${petId} 的宠物。`);
    }
  };
  getRequest.onerror = event => console.error(`查找宠物失败: ${event.target.error}`);
  transaction.oncomplete = () => db.close();
}

// 检查所有宠物的状态
async function checkAllPetsStatus() {
  console.log("\n--- 正在检查所有宠物的状态 ---");
  const db = await getDB();
  const transaction = db.transaction(STORENAME, "readonly");
  const store = transaction.objectStore(STORENAME);
  const getAllRequest = store.getAll();

  getAllRequest.onsuccess = () => {
    const pets = getAllRequest.result;
    if (pets.length > 0) {
      pets.forEach(p => {
        console.log(`🐾 ID: ${p.id}, 名字: ${p.name}, 类型: ${p.type}, 开心值: ${p.happiness}, 饥饿度: ${p.hunger}`);
      });
    } else {
      console.log("你的宠物小屋还是空的，快去创造一只吧！");
    }
  };
  transaction.oncomplete = () => db.close();
}


// --- 模拟游戏流程 ---
async function gameLoop() {
  // 为了确保每次运行都是干净的，我们先删除旧数据库
  indexedDB.deleteDatabase(DBNAME);
  await new Promise(resolve => setTimeout(resolve, 100)); // 等待删除操作完成

  await checkAllPetsStatus(); // 初始检查，应该是空的
  const petId = await createPet("闪电狗", "电子犬");
  await feedPet(petId);
  await feedPet(petId);
  await createPet("泡泡猫", "水系猫");
  await checkAllPetsStatus(); // 最终检查
}

// 启动游戏！
gameLoop();
```

### 💡 记忆要点
- **异步为王**：IndexedDB 所有操作都是异步的，必须使用 `onsuccess`, `onerror` 等事件回调函数来处理结果。
- **事务是必须的**：任何数据的读写（CRUD）都必须在事务（Transaction）中进行，这保证了数据的完整性。
- **版本控制结构**：数据库的结构（如创建对象存储或索引）只能在 `onupgradeneeded` 事件中修改，这个事件由数据库版本号控制。

<!--
metadata:
  syntax: [function, async, await]
  pattern: [callback, promise-chain, error-handling]
  api: [IndexedDB, IDBFactory, IDBDatabase, IDBTransaction, IDBObjectStore, Promise]
  concept: [asynchronous-programming, client-side-storage, database, transaction]
  difficulty: advanced
  dependencies: [无]
  related: [js-sec-8-2-1, js-sec-8-2-2]
-->