# 实现一个简单的路由 Agent

## 🎯 核心概念
路由 Agent 是 LangGraph 中实现条件分支的关键机制，它通过智能判断输入内容来决定执行流程的走向，解决了单一线性流程无法处理多样化任务的问题，是构建复杂多能力 Agent 系统的基石。

## 💡 使用方式
核心 API 是 `add_conditional_edges()` 方法，它允许根据条件函数的返回值动态选择下一个节点：

```python
graph.add_conditional_edges(
    "current_node",
    router_function,  # 条件判断函数
    {
        "route_a": "node_a",
        "route_b": "node_b",
        "route_c": "node_c"
    }
)
```

## 📚 Level 1: 基础认知（30秒理解）
最简单的路由 Agent：根据输入内容长度决定处理方式

```python
from typing import Literal
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict

# 定义状态
class State(TypedDict):
    input: str
    result: str

# 定义节点函数
def short_processor(state: State) -> State:
    return {"result": f"处理短文本: {state['input']}"}

def long_processor(state: State) -> State:
    return {"result": f"处理长文本: {state['input']}"}

# 路由函数
def route_by_length(state: State) -> Literal["short", "long"]:
    return "short" if len(state["input"]) < 10 else "long"

# 构建图
graph = StateGraph(State)
graph.add_node("short_processor", short_processor)
graph.add_node("long_processor", long_processor)

# 设置条件边
graph.add_conditional_edges(
    "__start__",
    route_by_length,
    {"short": "short_processor", "long": "long_processor"}
)

graph.add_edge("short_processor", END)
graph.add_edge("long_processor", END)

# 编译并运行
app = graph.compile()

# 测试运行
print("短文本测试:")
result = app.invoke({"input": "Hello"})
print(result["result"])

print("\n长文本测试:")
result = app.invoke({"input": "这是一个很长的文本内容，需要特殊处理"})
print(result["result"])
```

## 📈 Level 2: 核心特性（深入理解）

### 特性1: 多路路由决策
实现基于内容类型的多路路由，支持多种处理路径

```python
from typing import Literal
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict
import re

class State(TypedDict):
    input: str
    result: str

# 定义多个处理节点
def math_processor(state: State) -> State:
    # 简单数学计算
    expression = state["input"].replace("计算", "").strip()
    try:
        result = eval(expression)
        return {"result": f"计算结果: {expression} = {result}"}
    except:
        return {"result": f"无法计算表达式: {expression}"}

def weather_processor(state: State) -> State:
    # 模拟天气查询
    location = state["input"].replace("天气", "").strip()
    return {"result": f"{location}的天气: 晴朗, 25°C"}

def general_processor(state: State) -> State:
    # 通用处理器
    return {"result": f"已处理您的问题: {state['input']}"}

# 智能路由函数
def smart_router(state: State) -> Literal["math", "weather", "general"]:
    input_text = state["input"]
    
    if "计算" in input_text or any(op in input_text for op in ["+", "-", "*", "/"]):
        return "math"
    elif "天气" in input_text:
        return "weather"
    else:
        return "general"

# 构建图
graph = StateGraph(State)
graph.add_node("math_node", math_processor)
graph.add_node("weather_node", weather_processor)
graph.add_node("general_node", general_processor)

# 设置条件路由
graph.add_conditional_edges(
    "__start__",
    smart_router,
    {
        "math": "math_node",
        "weather": "weather_node", 
        "general": "general_node"
    }
)

graph.add_edge("math_node", END)
graph.add_edge("weather_node", END)
graph.add_edge("general_node", END)

app = graph.compile()

# 测试多种场景
test_cases = [
    "计算 2 + 3 * 4",
    "北京天气怎么样",
    "你好，今天过得如何"
]

for test in test_cases:
    print(f"\n输入: {test}")
    result = app.invoke({"input": test})
    print(f"输出: {result['result']}")
```

## 🔍 Level 3: 对比学习（避免陷阱）

### 错误用法 vs 正确用法

```python
from typing import Literal
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict

class State(TypedDict):
    input: str
    category: str
    result: str

# ❌ 错误用法：路由函数修改状态（违反纯函数原则）
def bad_router(state: State) -> Literal["a", "b"]:
    state["category"] = "processed"  # 错误：修改了状态
    return "a" if len(state["input"]) > 5 else "b"

# ✅ 正确用法：路由函数只读不写
def good_router(state: State) -> Literal["a", "b"]:
    # 只读取状态，不修改
    return "a" if len(state["input"]) > 5 else "b"

def processor_a(state: State) -> State:
    return {"result": "处理路径A", "category": "A类"}

def processor_b(state: State) -> State:
    return {"result": "处理路径B", "category": "B类"}

# 正确构建图
graph = StateGraph(State)
graph.add_node("a_node", processor_a)
graph.add_node("b_node", processor_b)

graph.add_conditional_edges(
    "__start__",
    good_router,  # 使用正确的只读路由函数
    {"a": "a_node", "b": "b_node"}
)

graph.add_edge("a_node", END)
graph.add_edge("b_node", END)

app = graph.compile()

# 测试运行
result = app.invoke({"input": "short"})
print(f"短输入结果: {result}")

result = app.invoke({"input": "这是一个较长的输入"})
print(f"长输入结果: {result}")
```

## 🚀 Level 4: 实战应用（真实场景）
构建一个智能客服路由系统，根据用户问题类型自动路由到相应的处理模块

```python
from typing import Literal
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict
import re

class CustomerServiceState(TypedDict):
    user_input: str
    department: str
    response: str
    priority: str

# 各部门处理函数
def billing_department(state: CustomerServiceState) -> CustomerServiceState:
    issues = {
        "账单": "您的账单问题已记录，将在24小时内处理",
        "支付": "支付问题需要您提供订单号，请稍等",
        "退款": "退款申请已提交，处理需要3-5个工作日"
    }
    response = issues.get("账单", "已转接账单专员为您服务")
    return {"response": response, "department": "billing"}

def technical_department(state: CustomerServiceState) -> CustomerServiceState:
    issues = {
        "登录": "请尝试重置密码或联系技术支持",
        "错误": "请提供错误代码，我们将为您排查",
        "无法使用": "技术团队正在检查系统问题"
    }
    response = issues.get("登录", "技术专员将尽快联系您")
    return {"response": response, "department": "technical", "priority": "high"}

def general_department(state: CustomerServiceState) -> CustomerServiceState:
    return {
        "response": "感谢您的咨询，客服代表将为您服务",
        "department": "general",
        "priority": "normal"
    }

# 智能路由判断
def customer_service_router(state: CustomerServiceState) -> Literal["billing", "technical", "general"]:
    input_text = state["user_input"].lower()
    
    billing_keywords = ["账单", "支付", "退款", "收费", "价格"]
    technical_keywords = ["登录", "错误", "bug", "无法使用", "崩溃", "技术"]
    
    if any(keyword in input_text for keyword in billing_keywords):
        return "billing"
    elif any(keyword in input_text for keyword in technical_keywords):
        return "technical"
    else:
        return "general"

# 构建客服路由图
graph = StateGraph(CustomerServiceState)
graph.add_node("billing", billing_department)
graph.add_node("technical", technical_department)
graph.add_node("general", general_department)

graph.add_conditional_edges(
    "__start__",
    customer_service_router,
    {
        "billing": "billing",
        "technical": "technical",
        "general": "general"
    }
)

graph.add_edge("billing", END)
graph.add_edge("technical", END)
graph.add_edge("general", END)

customer_service_app = graph.compile()

# 模拟客服对话场景
test_cases = [
    "我的账单有问题，金额不对",
    "系统登录不了，一直报错",
    "我想咨询一下产品信息",
    "支付过程中页面崩溃了",
    "你们公司的营业时间是多少"
]

print("智能客服路由系统测试:\n")
for i, query in enumerate(test_cases, 1):
    print(f"案例 {i}:")
    print(f"用户问题: {query}")
    result = customer_service_app.invoke({"user_input": query})
    print(f"路由部门: {result['department']}")
    print(f"回复内容: {result['response']}")
    if 'priority' in result:
        print(f"处理优先级: {result['priority']}")
    print("-" * 50)
```

## 💡 记忆要点
- 路由函数必须是纯函数，只读取状态不修改状态
- 条件边的返回值必须与路由映射中的键完全匹配
- 路由决策可以基于状态的任何属性，实现灵活的流程控制
- 多路路由支持复杂的业务逻辑分支，是构建智能 Agent 的核心
- 始终为所有可能的路由返回值提供对应的节点映射，避免运行时错误