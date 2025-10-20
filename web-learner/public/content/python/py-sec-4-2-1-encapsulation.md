好的，作为一名顶级的Python教育专家，我将为你生成关于 **“封装 (公有与私有)”** 的详细教学内容。

---

## 封装 (公有与私有)

### 🎯 核心概念
封装就像给你的代码造一个"保险箱"，把重要的数据（属性）和操作数据的方法打包在一起，并隐藏内部复杂的实现细节，只暴露有限的、安全的接口（公有方法）供外部使用，从而保护数据不被随意篡改。

### 💡 使用方式
在Python中，我们通过命名约定来区分属性和方法的访问权限：

1.  **公有 (Public):**
    - **命名:** 无任何前缀，例如 `self.name`。
    - **访问:** 可以在类的内部、外部以及子类中随意访问。这是默认的访问级别。

2.  **受保护 (Protected):**
    - **命名:** 单个下划线前缀，例如 `self._health`。
    - **访问:** 这是一种**约定**，告诉其他程序员：“这是内部属性，不建议在类的外部直接访问，但如果你非要访问，我也拦不住你。” Python本身并不会强制限制访问。

3.  **私有 (Private):**
    - **命名:** 双下划线前缀，例如 `self.__secret_code`。
    - **访问:** Python 会进行**名称改写 (Name Mangling)**，使得在类的外部很难直接访问。这是最强的封装级别。

### 📚 Level 1: 基础认知（30秒理解）
让我们创建一个简单的 `Cat` 类，看看公有和私有属性的区别。

```python
class Cat:
    def __init__(self, name, age):
        # 公有属性，谁都可以访问
        self.name = name
        # 私有属性，外部不应该直接访问
        self.__age = age

    def meow(self):
        print(f"{self.name} (年龄保密哦) 正在喵喵叫~")

# 创建一个 Cat 实例
my_cat = Cat("咪咪", 2)

# 1. 访问公有属性 - 成功！
print(f"我的猫叫: {my_cat.name}")

# 2. 调用公有方法 - 成功！
my_cat.meow()

# 3. 尝试直接访问私有属性 - 失败！
try:
    print(f"猫的年龄是: {my_cat.__age}")
except AttributeError as e:
    print(f"访问失败了: {e}")

# 预期输出:
# 我的猫叫: 咪咪
# 咪咪 (年龄保密哦) 正在喵喵叫~
# 访问失败了: 'Cat' object has no attribute '__age'
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 通过公有方法安全地访问私有属性 (Getter/Setter)
我们不直接暴露私有属性，而是提供公有的`get`和`set`方法来控制访问。这允许我们在修改属性前进行数据验证。

```python
class BankAccount:
    def __init__(self, account_holder, initial_balance):
        self.account_holder = account_holder
        # 私有余额，不能随意修改
        self.__balance = initial_balance

    # "Getter" 方法：提供一个只读的访问途径
    def get_balance(self):
        print("正在查询余额...")
        return self.__balance

    # "Setter" 方法：提供一个受控的修改途径
    def set_balance(self, amount):
        print("正在进行存款操作...")
        if amount > 0:
            self.__balance += amount
            print(f"存款成功！当前余额: {self.__balance}")
        else:
            print("存款金额必须大于0！")

# 创建账户
account = BankAccount("小明", 1000)

# 使用 getter 方法安全地读取余额
current_balance = account.get_balance()
print(f"账户持有人: {account.account_holder}, 余额: {current_balance}")

# 使用 setter 方法安全地修改余额
account.set_balance(500)
account.set_balance(-50) # 尝试存入一个无效金额

# 预期输出:
# 正在查询余额...
# 账户持有人: 小明, 余额: 1000
# 正在进行存款操作...
# 存款成功！当前余额: 1500
# 正在进行存款操作...
# 存款金额必须大于0！
```

#### 特性2: 私有属性的“名称改写” (Name Mangling)
Python的私有属性并不是真的无法访问，它只是玩了一个“改名”的把戏。`__attribute` 会被自动改写成 `_ClassName__attribute`。了解这一点有助于调试，但**强烈不推荐**在正常代码中使用这种方式访问。

```python
class SecretAgent:
    def __init__(self, code_name, secret_id):
        self.code_name = code_name
        self.__secret_id = secret_id

    def reveal_secret(self):
        print(f"我的秘密ID是: {self.__secret_id}")

agent_007 = SecretAgent("James Bond", "007")

# 正常方式无法访问
try:
    print(agent_007.__secret_id)
except AttributeError as e:
    print(f"直接访问失败: {e}")

# 揭秘“名称改写”：通过特殊格式可以访问到
# 格式: _类名__私有属性名
mangled_name = '_SecretAgent__secret_id'
print(f"Python内部把它改名为: {mangled_name}")
print(f"通过改写后的名字访问: {getattr(agent_007, mangled_name)}")

# 预期输出:
# 直接访问失败: 'SecretAgent' object has no attribute '__secret_id'
# Python内部把它改名为: _SecretAgent__secret_id
# 通过改写后的名字访问: 007
```

### 🔍 Level 3: 对比学习（避免陷阱）
**场景:** 管理一个游戏角色的生命值（HP），生命值不能超过100，也不能低于0。

```python
# === 错误用法 ===
# ❌ 将HP设为公有，导致数据可以被随意篡改，破坏游戏规则
class PlayerWrong:
    def __init__(self, name):
        self.name = name
        self.hp = 100 # 公有属性

player_w = PlayerWrong("鲁莽的玩家")
print(f"初始HP: {player_w.hp}")

# 外部代码可以随意设置不合逻辑的值
player_w.hp = 9999  # 破坏了HP上限
print(f"被非法修改后的HP: {player_w.hp}")
player_w.hp = -50   # 破坏了HP下限
print(f"再次被非法修改后的HP: {player_w.hp}")

# 解释：公有属性就像一个没有上锁的房间，任何人都可以进去乱动东西，非常不安全。

# === 正确用法 ===
# ✅ 将HP设为私有，通过方法来控制修改，保证数据安全
class PlayerRight:
    def __init__(self, name):
        self.name = name
        self.__hp = 100 # 私有属性

    def get_hp(self):
        return self.__hp

    def take_damage(self, damage):
        if damage > 0:
            self.__hp -= damage
            if self.__hp < 0:
                self.__hp = 0 # 保证HP不低于0
        print(f"{self.name} 受到 {damage} 点伤害, 剩余HP: {self.__hp}")

    def heal(self, amount):
        if amount > 0:
            self.__hp += amount
            if self.__hp > 100:
                self.__hp = 100 # 保证HP不高于100
        print(f"{self.name} 恢复了 {amount} 点生命, 剩余HP: {self.__hp}")

player_r = PlayerRight("聪明的玩家")
print(f"\n初始HP: {player_r.get_hp()}")
player_r.take_damage(30)
player_r.heal(500) # 尝试过量治疗
player_r.take_damage(999) # 尝试过量伤害
print(f"最终HP: {player_r.get_hp()}")

# 解释：通过封装，我们将HP保护起来，只提供 take_damage 和 heal 两个“官方通道”来修改它。
# 在这两个通道里，我们可以加入逻辑判断，确保HP值永远在0-100的有效范围内。
```

### 🚀 Level 4: 实战应用（真实场景）

**场景：** 🐾 电子宠物“代码精灵”饲养模拟器

我们的代码精灵有一个隐藏的“心情”属性，它会根据我们的互动（喂食、玩耍）而变化。我们无法直接设置它的心情，只能通过行为来影响它。

```python
import random

class CodeSprite:
    """
    一个可爱的电子宠物：代码精灵！
    它的心情是私有的，我们只能通过互动来影响它。
    """
    def __init__(self, name):
        self.name = name
        # 公有属性：饥饿度
        self.hunger = 50
        # 私有属性：心情指数，范围0-100
        self.__mood = 70

    # 私有方法：内部逻辑，用于更新心情
    def __update_mood(self, value):
        self.__mood += value
        if self.__mood > 100: self.__mood = 100
        if self.__mood < 0: self.__mood = 0

    # 公有方法：喂食
    def feed(self):
        print(f"你喂了 {self.name} 一块能量方块...")
        self.hunger -= 10
        if self.hunger < 0: self.hunger = 0
        self.__update_mood(5) # 喂食会增加少量心情
        print(f"{self.name} 的饥饿度下降了！")

    # 公有方法：玩耍
    def