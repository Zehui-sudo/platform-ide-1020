## 数据库与连接池 (SQLAlchemy async, asyncpg)

### 🎯 核心概念
解决高并发场景下**同步数据库操作的IO阻塞问题**——通过异步IO（async/await）避免线程阻塞，并通过**连接池**复用数据库连接（减少重复建立连接的开销），最终提升系统吞吐量（尤其是IO密集型服务，如API接口、爬虫）。


### 💡 使用方式
1. **安装依赖**：需安装异步PostgreSQL驱动`asyncpg`和SQLAlchemy异步扩展  
   ```bash
   pip install asyncpg sqlalchemy[asyncio]
   ```
2. **核心组件**：
   - `create_async_engine`：创建异步数据库引擎（连接PostgreSQL的URL格式为`postgresql+asyncpg://user:password@host:port/dbname`）
   - `async_sessionmaker`：生成异步会话工厂（用于创建数据库会话，类似“数据库连接的代理”）
   - `AsyncSession`：异步会话对象（执行CRUD操作的入口）


### 📚 Level 1: 基础认知（30秒理解）
最简单的异步数据库操作：**连接数据库→创建表→插入数据→查询数据**

```python
import asyncio
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

# 1. 定义数据模型（ORM映射）
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, index=True)

# 2. 异步数据库配置
DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/test_db"  # 替换为你的数据库信息
async_engine = create_async_engine(DATABASE_URL, echo=True)  # echo=True打印SQL日志
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # 避免提交后对象过期
)

# 3. 异步操作函数
async def init_db():
    """创建数据库表"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # 执行同步的表创建（SQLAlchemy兼容写法）

async def add_and_get_user():
    """插入并查询用户"""
    async with AsyncSessionLocal() as session:  # 自动管理会话生命周期
        # 插入用户
        new_user = User(name="Alice", email="alice@example.com")
        session.add(new_user)
        await session.commit()  # 必须await提交！
        await session.refresh(new_user)  # 刷新对象获取数据库生成的id
        
        # 查询用户
        user = await session.get(User, new_user.id)  # 按主键查询
        print(f"查询到用户: {user.name} ({user.email})")  # 预期输出: 查询到用户: Alice (alice@example.com)

# 4. 运行异步任务
async def main():
    await init_db()
    await add_and_get_user()

asyncio.run(main())
```


### 📈 Level 2: 核心特性（深入理解）
#### 特性1: 连接池配置（控制连接数量）
连接池是异步数据库性能的关键！通过`create_async_engine`的参数调整连接池行为：
- `pool_size`：默认连接数（同时保持的空闲连接数，默认5）
- `max_overflow`：最大溢出连接数（超出pool_size时临时创建的连接数，默认10）
- `pool_recycle`：连接存活时间（避免长期闲置连接被数据库关闭，默认-1表示不回收）

```python
# 配置连接池（最多保持5个空闲连接，峰值可创建15个连接）
async_engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_size=5,         # 核心连接数
    max_overflow=10,     # 溢出连接数
    pool_recycle=3600,   # 1小时后回收连接
)
```

#### 特性2: 异步事务（原子操作）
用`async with session.begin()`开启**自动事务**（提交成功则持久化，失败则回滚），适合需要原子性的操作（如转账）：

```python
async def transfer_money(from_user_id: int, to_user_id: int, amount: float):
    async with AsyncSessionLocal() as session:
        async with session.begin():  # 自动提交/回滚
            # 1. 查询转出用户（减少余额）
            from_user = await session.get(User, from_user_id)
            if from_user.balance < amount:
                raise ValueError("余额不足")
            from_user.balance -= amount
            
            # 2. 查询转入用户（增加余额）
            to_user = await session.get(User, to_user_id)
            to_user.balance += amount
            
            # 无需手动commit！async with会自动提交
            print(f"转账成功: {from_user.name} → {to_user.name}，金额{amount}")

# 调用示例（需先给User添加balance字段）
# await transfer_money(1, 2, 100.0)
```


### 🔍 Level 3: 对比学习（避免陷阱）
#### 陷阱1: 忘记`await`导致操作未执行
**错误用法**：没`await`数据库操作，导致SQL未发送到数据库

```python
async def wrong_add_user():
    async with AsyncSessionLocal() as session:
        session.add(User(name="Bob", email="bob@example.com"))
        session.commit()  # ❌ 错误：commit是异步方法，必须await！
```

**正确用法**：

```python
async def correct_add_user():
    async with AsyncSessionLocal() as session:
        session.add(User(name="Bob", email="bob@example.com"))
        await session.commit()  # ✅ 必须await！
        await session.refresh(user)
```

#### 陷阱2: 会话未关闭导致连接泄漏
**错误用法**：手动创建会话但未关闭，导致连接池资源耗尽

```python
async def leak_connection():
    session = AsyncSessionLocal()  # 手动创建会话
    session.add(User(name="Charlie", email="charlie@example.com"))
    await session.commit()
    # ❌ 未关闭会话，连接未归还给连接池！
```

**正确用法**：用`async with`自动管理会话生命周期（推荐），或手动`await session.close()`

```python
async def no_leak_connection():
    async with AsyncSessionLocal() as session:  # ✅ 自动关闭会话
        session.add(User(name="Charlie", email="charlie@example.com"))
        await session.commit()
```


### 🚀 Level 4: 实战应用（真实场景）
**场景**：实现一个**异步用户管理系统**，支持“增删改查”四大操作：

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# 1. 定义数据模型（新增balance字段）
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, index=True)
    balance = Column(Float, default=0.0)  # 余额

# 2. 封装CRUD操作
async def create_user(session: AsyncSession, name: str, email: str) -> User:
    user = User(name=name, email=email)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def get_users(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User))  # 异步执行查询
    return result.scalars().all()  # 转换为User对象列表

async def update_user_balance(session: AsyncSession, user_id: int, new_balance: float) -> User:
    user = await session.get(User, user_id)
    if not user:
        raise ValueError("用户不存在")
    user.balance = new_balance
    await session.commit()
    await session.refresh(user)
    return user

async def delete_user(session: AsyncSession, user_id: int) -> None:
    user = await session.get(User, user_id)
    if user:
        await session.delete(user)
        await session.commit()

# 3. 运行实战任务
async def main():
    await init_db()  # 初始化表
    
    async with AsyncSessionLocal() as session:
        # 新增用户
        alice = await create_user(session, "Alice", "alice@example.com")
        bob = await create_user(session, "Bob", "bob@example.com")
        
        # 查询所有用户
        users = await get_users(session)
        print(f"所有用户: {[u.name for u in users]}")  # 输出: 所有用户: ['Alice', 'Bob']
        
        # 更新Alice的余额
        updated_alice = await update_user_balance(session, alice.id, 100.0)
        print(f"Alice的余额: {updated_alice.balance}")  # 输出: Alice的余额: 100.0
        
        # 删除Bob
        await delete_user(session, bob.id)
        remaining_users = await get_users(session)
        print(f"剩余用户: {[u.name for u in remaining_users]}")  # 输出: 剩余用户: ['Alice']

asyncio.run(main())
```


### 💡 记忆要点
- **必须用异步组件**：引擎用`create_async_engine`，会话用`async_sessionmaker`，所有数据库操作（`commit`/`execute`/`get`）都要`await`！
- **连接池是性能关键**：通过`pool_size`和`max_overflow`控制连接数量，避免连接泄漏。
- **事务用`async with`**：`async with session.begin()`自动管理事务，无需手动`commit`或`rollback`。
- **会话要关闭**：优先用`async with`自动关闭会话，避免连接未归还给连接池。


### 📌 扩展阅读
- SQLAlchemy异步文档：https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- asyncpg文档：https://magicstack.github.io/asyncpg/current/