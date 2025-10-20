## pytest-asyncio/anyio 测试

### 🎯 核心概念
解决**异步协程无法直接用普通 pytest 测试**的问题——自动管理事件循环、运行异步函数并捕获结果，让你像测试同步代码一样测试 `async def` 函数。


### 💡 使用方式
1. **安装依赖**：  
   ```bash
   pip install pytest pytest-asyncio anyio
   ```
2. **选择工具**：  
   - `pytest-asyncio`：需用 `@pytest.mark.asyncio` 装饰异步测试函数；  
   - `anyio`：更灵活（支持多后端，如 asyncio/trio），直接写 `async def` 测试函数即可。


### 📚 Level 1: 基础认知（30秒理解）
写一个测试异步加法函数的最小示例，体会异步测试的基本流程。

```python
# 待测试的异步函数
async def add(a: int, b: int) -> int:
    await asyncio.sleep(0.1)  # 模拟异步操作（比如IO）
    return a + b

# 用 pytest-asyncio 测试（需装饰器）
import pytest
import asyncio

@pytest.mark.asyncio
async def test_add_with_asyncio():
    result = await add(1, 2)
    assert result == 3  # 预期输出：测试通过

# 用 anyio 测试（无需装饰器，直接 async def）
async def test_add_with_anyio():
    result = await add(1, 2)
    assert result == 3  # 预期输出：测试通过
```


### 📈 Level 2: 核心特性（深入理解）
#### 特性1: 自动隔离事件循环
pytest-asyncio/anyio 会为**每个测试用例创建独立的事件循环**，避免测试间的状态污染。

```python
import pytest
import asyncio

async def long_running_task():
    await asyncio.sleep(1)
    return "done"

@pytest.mark.asyncio
async def test_isolated_loop1():
    task = asyncio.create_task(long_running_task())
    await asyncio.sleep(0.5)  # 运行一半
    assert not task.done()  # 任务未完成

@pytest.mark.asyncio
async def test_isolated_loop2():
    task = asyncio.create_task(long_running_task())
    await asyncio.sleep(0.5)
    assert not task.done()  # 两个测试的任务互不影响
```

#### 特性2: 异步夹具（Fixture）
支持**异步依赖注入**（比如异步数据库连接、HTTP客户端），用 `async def` 定义夹具即可。

```python
import pytest
from httpx import AsyncClient

# 异步Fixture：提供HTTP客户端（模拟真实场景）
@pytest.fixture
async def async_client():
    async with AsyncClient(base_url="http://testserver") as client:
        yield client  # 测试用例将拿到这个client

# 测试用例：依赖异步Fixture
@pytest.mark.asyncio
async def test_get_user(async_client: AsyncClient):
    response = await async_client.get("/users/1")
    assert response.status_code == 200
    assert response.json() == {"id": 1, "name": "Alice"}  # 预期接口返回
```


### 🔍 Level 3: 对比学习（避免陷阱）
#### 错误用法 vs 正确用法
**陷阱1：忘记 `await` 异步函数**  
错误示例（返回协程对象，断言失败）：
```python
def test_forget_await():
    # 错误：直接调用async函数，返回coroutine对象而非结果
    result = add(1, 2)
    assert result == 3  # 实际得到 <coroutine object add at 0x10000>
```
正确示例（用 `await` 获取结果）：
```python
async def test_correct_await():
    result = await add(1, 2)
    assert result == 3  # 正确
```

**陷阱2：用同步Fixture返回异步对象**  
错误示例（Fixture返回协程，未执行）：
```python
@pytest.fixture
def sync_fixture():
    # 错误：同步Fixture返回coroutine，测试用例拿到的是未执行的对象
    return add(1, 2)

async def test_sync_fixture(sync_fixture):
    assert sync_fixture == 3  # 失败，sync_fixture是coroutine
```
正确示例（用异步Fixture执行协程）：
```python
@pytest.fixture
async def async_fixture():
    return await add(1, 2)  # 正确：异步Fixture中await执行

async def test_async_fixture(async_fixture):
    assert async_fixture == 3  # 成功
```


### 🚀 Level 4: 实战应用（真实场景）
#### 场景：测试异步RPC服务
假设我们有一个**异步RPC客户端**，需要测试它调用`get_product`方法的正确性。

```python
# 1. 待测试的异步RPC客户端
class AsyncRPClient:
    async def get_product(self, product_id: int) -> dict:
        # 模拟RPC调用（实际是向服务器发请求）
        await asyncio.sleep(0.1)
        return {"id": product_id, "name": f"Product {product_id}"}

# 2. 测试用例（结合Fixture+参数化）
import pytest
import asyncio

@pytest.fixture
async def rpc_client():
    return AsyncRPClient()  # 提供RPC客户端实例

# 参数化测试：覆盖多场景
@pytest.mark.asyncio
@pytest.mark.parametrize("product_id, expected_name", [
    (1, "Product 1"),
    (2, "Product 2"),
    (3, "Product 3"),
])
async def test_get_product(
    rpc_client: AsyncRPClient,
    product_id: int,
    expected_name: str
):
    product = await rpc_client.get_product(product_id)
    assert product["id"] == product_id
    assert product["name"] == expected_name  # 验证结果正确性
```
运行测试：
```bash
pytest test_rpc.py -v
# 输出：3个测试用例全部通过
```


### 💡 记忆要点
- **异步测试函数必须是 `async def`**，否则无法运行协程。  
- **`pytest-asyncio` 需要 `@pytest.mark.asyncio`** 装饰器，`anyio` 可直接运行 `async def` 测试。  
- **异步Fixture用 `async def`**，并在内部处理异步逻辑（如 `await`）。  
- **永远不要忽略 `await`**：异步函数的返回值是协程对象，必须 `await` 才能拿到结果。  
- **事件循环隔离**：每个测试用例有独立的事件循环，避免状态污染。