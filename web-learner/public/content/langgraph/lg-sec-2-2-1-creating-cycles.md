```markdown
# 在图中创建循环

### 🎯 核心概念
循环允许图中节点重复执行，这是构建能够自我修正、多轮交互或迭代处理复杂任务的智能代理的关键机制。

### 💡 使用方式
通过 `add_conditional_edges()` 方法创建条件边，结合 `END` 特殊节点实现循环控制：

```python
graph.add_conditional_edges(
    "decision_node",
    should_continue,  # 决定是否继续循环的条件函数
    {"continue": "next_node", "end": END}
)
```

### 📚 Level 1: 基础认知（30秒理解）
最简单的计数器循环示例：

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

# 定义状态
class State(TypedDict):
    count: int
    max_count: int

# 计数器节点
def counter_node(state: State):
    return {"count": state["count"] + 1}

# 条件判断函数
def should_continue(state: State):
    if state["count"] < state["max_count"]:
        return "continue"
    return "end"

# 构建图
graph = StateGraph(State)
graph.add_node("counter", counter_node)
graph.set_entry_point("counter")
graph.add_conditional_edges("counter", should_continue, {"continue": "counter", "end": END})

# 编译运行
app = graph.compile()
result = app.invoke({"count": 0, "max_count": 3})
print(result)  # {'count': 3, 'max_count': 3}
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 动态循环终止条件
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal

class State(TypedDict):
    messages: list
    iteration: int

def process_message(state: State):
    new_message = f"Processed iteration {state['iteration']}"
    return {
        "messages": state["messages"] + [new_message],
        "iteration": state["iteration"] + 1
    }

def check_completion(state: State) -> Literal["continue", "end"]:
    # 模拟动态条件：迭代3次或随机提前结束
    if state["iteration"] >= 3 or len(state["messages"]) > 5:
        return "end"
    return "continue"

graph = StateGraph(State)
graph.add_node("process", process_message)
graph.set_entry_point("process")
graph.add_conditional_edges("process", check_completion, {
    "continue": "process", 
    "end": END
})

app = graph.compile()
result = app.invoke({"messages": [], "iteration": 0})
print(result["messages"])
```

### 🔍 Level 3: 对比学习（避免陷阱）

```python
# ❌ 错误用法：缺少终止条件的无限循环
def bad_condition(state):
    return "continue"  # 永远返回continue → 无限循环

# ✅ 正确用法：确保有明确的终止条件
def good_condition(state):
    if state.get("should_stop", False):
        return "end"
    if state["attempts"] > 5:  # 安全上限
        return "end"
    return "continue"
```

### 🚀 Level 4: 实战应用（真实场景）
构建一个自我修正的代码生成代理：

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal
import random

class CodeGenState(TypedDict):
    requirement: str
    generated_code: str
    attempts: int
    feedback: str

def generate_code(state: CodeGenState):
    # 模拟代码生成（实际中可接入LLM）
    attempts = state["attempts"]
    if attempts == 0:
        code = "def hello():\n    print('Hello')"  # 初始有错误的代码
    else:
        code = "def hello():\n    print('Hello World!')"  # 修正后的代码
    
    return {
        "generated_code": code,
        "attempts": attempts + 1
    }

def validate_code(state: CodeGenState):
    code = state["generated_code"]
    # 模拟代码验证
    if "print('Hello World!')" in code:
        return {"feedback": "代码正确！", "should_stop": True}
    else:
        return {"feedback": "缺少完整输出语句", "should_stop": False}

def should_continue(state: CodeGenState) -> Literal["generate", "end"]:
    if state.get("should_stop", False) or state["attempts"] >= 3:
        return "end"
    return "generate"

graph = StateGraph(CodeGenState)
graph.add_node("generate", generate_code)
graph.add_node("validate", validate_code)

graph.set_entry_point("generate")
graph.add_edge("generate", "validate")
graph.add_conditional_edges("validate", should_continue, {
    "generate": "generate",
    "end": END
})

app = graph.compile()
result = app.invoke({
    "requirement": "打印Hello World",
    "generated_code": "",
    "attempts": 0,
    "feedback": ""
})

print(f"最终代码: {result['generated_code']}")
print(f"尝试次数: {result['attempts']}")
print(f"最终反馈: {result['feedback']}")
```

### 💡 记忆要点
- 循环通过条件边和`END`节点的组合实现
- 必须设置明确的循环终止条件，避免无限循环
- 循环状态需要在节点间正确传递和更新
- 可设置最大迭代次数作为安全机制
```