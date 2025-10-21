在 5.1 节中，我们已经掌握了如何用 `class` 蓝图创建独立的实例，这好比是制造了许多功能相同的标准零件。但如果我们需要制造一些在标准零件基础上进行升级或特化的“高级零件”呢？

这就是继承与多态发挥作用的地方。它们是面向对象编程的两大支柱，能让我们的代码世界变得更加井然有序、富有层次感且灵活多变。

---

### 🎯 核心概念

继承（Inheritance）让一个类（子类）能够直接“继承”另一个类（父类）的属性和方法，实现了**代码复用**与**功能扩展**；而多态（Polymorphism）则允许我们用同样的方式与不同子类的对象进行交互，它们会各自表现出符合自己特点的行为，这极大地增强了代码的**灵活性**和**可维护性**。

### 💡 使用方式

在 Python 中，继承的语法是在定义类时，在类名后的括号里写上父类的名字。子类可以重写（override）父类的方法来提供自己的实现，并使用 `super()` 函数来调用父类中被重写的方法。

```python
# 1. 定义一个父类 (Parent Class)
class Parent:
    def __init__(self, name):
        self.name = name
        print("父类构造方法被调用。")

    def speak(self):
        return f"我是父类，我的名字是 {self.name}。"

# 2. 定义一个子类 (Child Class)，继承自 Parent
class Child(Parent):
    # 3. 重写 (Override) 父类的构造方法
    def __init__(self, name, toy):
        # 4. 使用 super() 调用父类的 __init__ 方法来初始化继承的属性
        super().__init__(name) 
        self.toy = toy # 添加子类自己的新属性
        print("子类构造方法被调用。")

    # 5. 重写 (Override) 父类的 speak 方法
    def speak(self):
        # 使用 super() 调用父类原来的 speak 方法，并在此基础上扩展
        parent_speech = super().speak()
        return f"{parent_speech} 我还有一个玩具：{self.toy}。"

# 创建子类实例
child_instance = Child("小明", "乐高积木")
print(child_instance.speak())
```

```text
# 预期输出:
父类构造方法被调用。
子类构造方法被调用。
我是父类，我的名字是 小明。 我还有一个玩具：乐高积木。
```

### 📚 Level 1: 基础认知（30秒理解）

想象一下，“动物”是一个父类，它会“吃”。“狗”是一个子类，它继承了“动物”，所以它天生就会“吃”，同时它还有自己独特的能力——“叫”。

```python
# 定义一个父类 Animal
class Animal:
    def eat(self):
        print("这个动物正在吃东西...")

# 定义一个子类 Dog，它继承自 Animal
class Dog(Animal):
    # Dog 类自己独有的方法
    def bark(self):
        print("汪！汪！汪！")

# 创建一个 Dog 实例
my_dog = Dog()

# 调用从 Animal 父类继承来的 eat 方法
my_dog.eat()

# 调用 Dog 子类自己的 bark 方法
my_dog.bark()
```

```text
# 预期输出:
这个动物正在吃东西...
汪！汪！汪！
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 方法重写 (Overriding) 与 `super()` 函数

当父类的方法不能完全满足子类的需求时，子类可以“重写”这个方法，提供自己的版本。如果你希望在子类的实现中，仍然执行父类版本的逻辑，`super()` 函数就派上了用场。它允许你调用父类的方法。

```python
class Employee:
    def __init__(self, name, salary):
        self.name = name
        self.salary = salary

    def get_details(self):
        return f"姓名: {self.name}, 薪水: {self.salary}"

# Manager 继承自 Employee
class Manager(Employee):
    def __init__(self, name, salary, department):
        # 使用 super().__init__ 来完成 name 和 salary 的初始化
        # 避免在子类中重复写 self.name = name, self.salary = salary
        super().__init__(name, salary)
        # 添加 Manager 自己的属性
        self.department = department

    # 重写 get_details 方法
    def get_details(self):
        # 使用 super().get_details() 获取父类生成的基础信息
        base_details = super().get_details()
        # 在基础信息上添加新内容
        return f"{base_details}, 部门: {self.department}"

# 创建实例
emp = Employee("张三", 5000)
mgr = Manager("李四", 10000, "技术部")

print(f"普通员工信息: {emp.get_details()}")
print(f"经理信息: {mgr.get_details()}")
```

```text
# 预期输出:
普通员工信息: 姓名: 张三, 薪水: 5000
经理信息: 姓名: 李四, 薪水: 10000, 部门: 技术部
```

#### 特性2: 多态的概念与实践

多态（Polymorphism）意味着“多种形态”。在编程中，它指不同的子类对象在响应同一个方法调用时，会表现出各自不同的行为。这使得我们可以编写更通用的代码，处理一系列相关的对象，而无需关心每个对象的具体类型。

```python
# 定义几个具有相同接口 (speak 方法) 的类
class Duck:
    def speak(self):
        print("嘎嘎嘎")

class Chicken:
    def speak(self):
        print("咯咯咯")

class Dog:
    def speak(self):
        print("汪汪汪")

# 这个函数接收任何有 .speak() 方法的对象
# 它不关心对象的具体类型是 Duck, Chicken 还是 Dog
def make_it_speak(animal_like_object):
    print("听，它在说话:")
    animal_like_object.speak()

# 创建不同类的实例
duck = Duck()
chicken = Chicken()
dog = Dog()

# 将不同类型的对象传入同一个函数，它们表现出不同的行为
print("--- 演示多态 ---")
make_it_speak(duck)
make_it_speak(chicken)
make_it_speak(dog)
```

```text
# 预期输出:
--- 演示多态 ---
听，它在说话:
嘎嘎嘎
听，它在说话:
咯咯咯
听，它在说话:
汪汪汪
```

### 🔍 Level 3: 对比学习（避免陷阱）

一个常见的陷阱是过度使用类型检查（如 `type()`），这会破坏多态带来的灵活性。推荐使用 `isinstance()`，因为它能正确处理继承关系。

```python
class Shape:
    def draw(self):
        raise NotImplementedError("子类必须实现 draw 方法")

class Circle(Shape):
    def draw(self):
        return "画一个圆形 ○"

class Square(Shape):
    def draw(self):
        return "画一个正方形 □"
```

> **进阶提示**：
> 在父类中通过 `raise NotImplementedError` 来强制子类实现某个方法是一种简单有效的约定。对于更大型或需要更严格接口约束的项目，Python 提供了 `abc` 模块（Abstract Base Classes），它允许我们创建正式的抽象基类和抽象方法，能够在子类实例化时就进行检查，从而提供更强的约束力。

```python
# === 错误用法 ===
# ❌ 使用 type() 进行类型判断，代码僵化且难以扩展
def draw_shape_bad(s):
    if type(s) is Circle:
        print(f"这是一个圆形，让我们来... {s.draw()}")
    elif type(s) is Square:
        print(f"这是一个正方形，让我们来... {s.draw()}")
    else:
        print("未知的形状类型")
# 解释为什么是错的:
# 这种写法完全违背了多态的思想。如果未来我们新增一个 Triangle 类，
# 就必须修改 draw_shape_bad 函数，在里面增加一个 elif 分支。
# 这使得代码耦合度高，维护成本也高。

print("--- 错误的方式 ---")
c = Circle()
s = Square()
draw_shape_bad(c)
draw_shape_bad(s)


# === 正确用法 ===
# ✅ 利用多态，编写通用代码，必要时使用 isinstance()
def draw_shape_good(s):
    # 直接调用 draw 方法，不关心 s 的具体类型是什么
    # 这就是多态的精髓：我们只依赖于共同的接口（draw方法）
    print(s.draw())

# 有时我们确实需要检查类型，比如只有圆形才能计算半径
def analyze_shape(s):
    print(f"分析图形: {s.draw()}")
    if isinstance(s, Circle):
        print("检测到这是一个圆形，它可以有半径。")
    elif isinstance(s, Square):
        print("检测到这是一个正方形，它可以有边长。")

# 解释为什么这样是对的:
# draw_shape_good 函数非常灵活，无论未来增加多少种 Shape 的子类，
# 只要它们实现了 draw 方法，这个函数就无需任何修改。
# analyze_shape 函数使用 isinstance() 来检查类型。`isinstance()` 比 `type()` 更好，
# 因为如果有一个 `MagicCircle` 继承自 `Circle`，`isinstance(magic_c, Circle)` 
# 依然会返回 True，它正确地识别了继承链。

print("\n--- 正确的方式 ---")
draw_shape_good(c)
draw_shape_good(s)
print("\n--- 使用 isinstance 进行特定检查 ---")
analyze_shape(c)
analyze_shape(s)
```

### 🚀 Level 4: 实战应用（真实场景）

**场景：** 📜 奇幻角色扮演游戏 (RPG) 的技能系统

在一个游戏中，有不同职业的角色，如战士和法师。他们都继承自一个基础的 `Character` 类。虽然他们都有一个 `use_skill` 的动作，但不同职业释放的技能效果截然不同。这就是一个典型的继承与多态的应用场景。

```python
import random

# 基础角色类 (父类)
class Character:
    def __init__(self, name, hp):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        print(f"[{self.name}] 踏上了冒险之旅！")

    def is_alive(self):
        return self.hp > 0

    def take_damage(self, damage):
        self.hp = max(0, self.hp - damage)
        print(f"💥 {self.name} 受到了 {damage} 点伤害，剩余生命: {self.hp}/{self.max_hp}")
        if not self.is_alive():
            print(f"💀 {self.name} 已被击败。")

    def use_skill(self, target):
        print(f"{self.name} 试图使用一个通用技能...")
        # 父类的技能效果很普通
        damage = random.randint(3, 8)
        print(f"造成了 {damage} 点伤害。")
        target.take_damage(damage)

# 战士类 (子类)
class Warrior(Character):
    def __init__(self, name, hp=120, rage=0):
        super().__init__(name, hp)
        self.rage = rage # 战士独有的怒气值

    # 重写 use_skill 方法
    def use_skill(self, target):
        print(f"⚔️ {self.name} 怒吼一声，发动了【英勇打击】！")
        damage = random.randint(15, 25) + self.rage
        print(f"对 {target.name} 造成了 {damage} 点巨额物理伤害！")
        target.take_damage(damage)
        self.rage += 5 # 每次攻击增加怒气

# 法师类 (子类)
class Mage(Character):
    def __init__(self, name, hp=80, mana=100):
        super().__init__(name, hp)
        self.mana = mana # 法师独有的法力值

    # 重写 use_skill 方法
    def use_skill(self, target):
        skill_cost = 20
        if self.mana >= skill_cost:
            self.mana -= skill_cost
            print(f"✨ {self.name} 吟唱咒语，释放了【火焰球】！(消耗{skill_cost}法力)")
            damage = random.randint(20, 30)
            print(f"对 {target.name} 造成了 {damage} 点毁灭性火焰伤害！")
            target.take_damage(damage)
        else:
            print(f"💧 {self.name} 的法力不足，施法失败！")

# --- 战斗开始 ---
garen = Warrior("盖伦")
veigar = Mage("维迦")

# 角色列表，展现多态的威力
characters = [garen, veigar]
monster = Character("哥布林", 100) # 怪物也是一个角色

print("\n--- 回合制战斗 ---")
round_num = 1
while all(c.is_alive() for c in characters) and monster.is_alive():
    print(f"\n--- 第 {round_num} 回合 ---")
    # 无论角色是 Warrior 还是 Mage，我们都用同样的方式调用 use_skill
    for char in characters:
        if char.is_alive() and monster.is_alive():
            char.use_skill(monster)
    round_num += 1

print("\n--- 战斗结束 ---")
```

```text
# 预期输出 (随机值可能不同):
[盖伦] 踏上了冒险之旅！
[维迦] 踏上了冒险之旅！
[哥布林] 踏上了冒险之旅！

--- 回合制战斗 ---

--- 第 1 回合 ---
⚔️ 盖伦 怒吼一声，发动了【英勇打击】！
对 哥布林 造成了 22 点巨额物理伤害！
💥 哥布林 受到了 22 点伤害，剩余生命: 78/100
✨ 维迦 吟唱咒语，释放了【火焰球】！(消耗20法力)
对 哥布林 造成了 25 点毁灭性火焰伤害！
💥 哥布林 受到了 25 点伤害，剩余生命: 53/100

--- 第 2 回合 ---
⚔️ 盖伦 怒吼一声，发动了【英勇打击】！
对 哥布林 造成了 28 点巨额物理伤害！
💥 哥布林 受到了 28 点伤害，剩余生命: 25/100
✨ 维迦 吟唱咒语，释放了【火焰球】！(消耗20法力)
对 哥布林 造成了 26 点毁灭性火焰伤害！
💥 哥布林 受到了 26 点伤害，剩余生命: 0/100
💀 哥布林 已被击败。

--- 战斗结束 ---
```

### 💡 记忆要点

- **要点1**: **继承是“是...的一种”关系**。`class Dog(Animal):` 意味着“狗是一种动物”。子类自动获得父类的非私有属性和方法，实现了代码的复用和层级化。
- **要点2**: **多态是“一个接口，多种形态”**。对于同一个指令（如 `character.use_skill()`），不同的对象（战士、法师）会给出不同的响应（物理攻击、魔法攻击）。这让我们的代码更具通用性和扩展性。
- **要点3**: **`super()` 是子类与父类沟通的桥梁**。当子类重写了父类的方法后，如果还想执行父类的原始逻辑，就用 `super().method_name()`，这好比“在巨人的肩膀上”添加自己的创新。