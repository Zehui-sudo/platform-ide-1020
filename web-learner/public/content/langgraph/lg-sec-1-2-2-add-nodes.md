## 添加节点 (Nodes)

### 🎯 核心概念
节点是 LangGraph 中的基本工作单元，每个节点代表一个特定的任务或操作（如调用 LLM、处理数据或执行计算）。添加节点是构建复杂 Agent 流程的关键步骤，因为它允许你将工作流分解为模块化、可复用的组件，从而简化开发、调试和维护。

### 💡 使用方式
在 LangGraph 中，使用 `StateGraph.add_node(name, node_func)` 方法添加节点：
- `name`: 节点的唯一标识符（字符串）。
- `node_func`: 节点函数，接受状态（State）作为输入，返回更新后的状态。

节点函数必须遵循签名：`def node_func(state: State) -> dict:`，其中 `State` 是自定义的状态类（通常使用 `TypedDict` 或 Pydantic 模型）。

### 📚 Level 1: 基础认知（30秒理解）
以下是一个最简单且完整的 LangGraph 应用示例，展示如何定义状态、添加一个节点，并运行图。该节点简单地修改状态中的消息。

```python
from typing import TypedDict
from langgraph.graph import StateGraph, END

# 定义状态结构：使用 TypedDict 来明确状态字段
class State(TypedDict):
    message: str

# 定义节点函数：接受状态，返回更新后的状态
def node_function(state: State) -> dict:
    # 修改状态中的 message 字段
    new_message = state["message"] + " (processed by node)"
    return {"message": new_message}

# 创建 StateGraph 实例，指定状态类型
graph = StateGraph(State)

# 添加节点：第一个参数是节点名称，第二个是节点函数
graph.add_node("my_node", node_function)

# 设置入口点：指定从哪个节点开始
graph.set_entry_point("my_node")

# 设置出口点：指定节点执行后结束（使用 END 常量）
graph.set_finish_point("my_node")

# 编译图
compiled_graph = graph.compile()

# 运行图：传入初始状态
initial_state = State(message="Hello")
result = compiled_graph.invoke(initial_state)

# 输出结果
print(result)
```

**预期输出**:
```
{'message': 'Hello (processed by node)'}
```

### 📈 Level 2: 核心特性（深入理解）
#### 特性1: 多个节点协同工作
添加多个节点，并通过边连接它们（边将在后续章节详细讲解，这里简要展示以体现节点作用）。节点可以按顺序执行，每个节点处理状态的不同部分。

```python
from typing import TypedDict
from langgraph.graph import StateGraph, END

# 定义状态：包含多个字段
class State(TypedDict):
    input_text: str
    processed_text: str
    final_output: str

# 节点1：处理输入文本
def process_input(state: State) -> dict:
    processed = state["input_text"].upper()  # 转换为大写
    return {"processed_text": processed}

# 节点2：生成最终输出
def generate_output(state: State) -> dict:
    final = f"Result: {state['processed_text']}"
    return {"final_output": final}

# 构建图
graph = StateGraph(State)

# 添加两个节点
graph.add_node("process_node", process_input)
graph.add_node("output_node", generate_output)

# 设置入口点
graph.set_entry_point("process_node")

# 添加边：从 process_node 到 output_node
graph.add_edge("process_node", "output_node")

# 设置出口点
graph.set_finish_point("output_node")

# 编译并运行
compiled_graph = graph.compile()
initial_state = State(input_text="hello world", processed_text="", final_output="")
result = compiled_graph.invoke(initial_state)

print(result)
```

**预期输出**:
```
{'input_text': 'hello world', 'processed_text': 'HELLO WORLD', 'final_output': 'Result: HELLO WORLD'}
```

#### 特性2: 节点访问和修改特定状态字段
节点可以只更新状态中的部分字段，而不影响其他字段。LangGraph 会自动合并更新。

```python
from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    count: int
    log: str

# 节点函数：只更新 count 字段
def increment_count(state: State) -> dict:
    new_count = state["count"] + 1
    return {"count": new_count}

# 另一个节点：只更新 log 字段
def add_log(state: State) -> dict:
    new_log = state["log"] + f"Count is {state['count']}. "
    return {"log": new_log}

graph = StateGraph(State)
graph.add_node("increment", increment_count)
graph.add_node("log", add_log)

graph.set_entry_point("increment")
graph.add_edge("increment", "log")  # 连接节点
graph.set_finish_point("log")

compiled_graph = graph.compile()
initial_state = State(count=0, log="Start. ")
result = compiled_graph.invoke(initial_state)

print(result)
```

**预期输出**:
```
{'count': 1, 'log': 'Start. Count is 1. '}
```

### 🔍 Level 3: 对比学习（避免陷阱）
#### 常见陷阱：节点函数返回格式错误
节点函数必须返回一个字典，其中键对应状态字段。如果返回错误格式，LangGraph 会抛出异常。

```python
from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    value: str

# 错误用法：节点函数返回字符串而不是字典
def bad_node(state: State) -> str:
    return "new value"  # 错误：应该返回字典

graph = StateGraph(State)
graph.add_node("bad_node", bad_node)  # 这会导致运行时错误
graph.set_entry_point("bad_node")
graph.set_finish_point("bad_node")

try:
    compiled_graph = graph.compile()
    result = compiled_graph.invoke(State(value="test"))
except Exception as e:
    print(f"错误: {e}")

# 正确用法：返回字典
def good_node(state: State) -> dict:
    return {"value": "new value"}

graph_correct = StateGraph(State)
graph_correct.add_node("good_node", good_node)
graph_correct.set_entry_point("good_node")
graph_correct.set_finish_point("good_node")

compiled_correct = graph_correct.compile()
result = compiled_correct.invoke(State(value="test"))
print(f"正确输出: {result}")
```

**预期输出**:
```
错误: Node function 'bad_node' must return a dictionary.
正确输出: {'value': 'new value'}
```

### 🚀 Level 4: 实战应用（真实场景）
设计一个简单的内容审核流程：节点1检查输入文本是否包含敏感词，节点2生成审核结果。综合运用节点添加和状态管理。

```python
from typing import TypedDict
from langgraph.graph import StateGraph, END

# 定义状态
class ModerationState(TypedDict):
    input_text: str
    has_sensitive_content: bool
    moderation_result: str

# 节点1：检查敏感词
def check_sensitive_content(state: ModerationState) -> dict:
    sensitive_words = ["bad", "stop", "danger"]
    text = state["input_text"].lower()
    has_sensitive = any(word in text for word in sensitive_words)
    return {"has_sensitive_content": has_sensitive}

# 节点2：生成审核结果
def generate_result(state: ModerationState) -> dict:
    if state["has_sensitive_content"]:
        result = "Content rejected: sensitive content found."
    else:
        result = "Content approved."
    return {"moderation_result": result}

# 构建图
graph = StateGraph(ModerationState)
graph.add_node("check_node", check_sensitive_content)
graph.add_node("result_node", generate_result)

graph.set_entry_point("check_node")
graph.add_edge("check_node", "result_node")  # 连接节点
graph.set_finish_point("result_node")

compiled_graph = graph.compile()

# 测试用例1: 无敏感内容
initial_state1 = ModerationState(input_text="Hello world", has_sensitive_content=False, moderation_result="")
result1 = compiled_graph.invoke(initial_state1)
print("测试1 (无敏感内容):", result1)

# 测试用例2: 有敏感内容
initial_state2 = ModerationState(input_text="This is bad", has_sensitive_content=False, moderation_result="")
result2 = compiled_graph.invoke(initial_state2)
print("测试2 (有敏感内容):", result2)
```

**预期输出**:
```
测试1 (无敏感内容): {'input_text': 'Hello world', 'has_sensitive_content': False, 'moderation_result': 'Content approved.'}
测试2 (有敏感内容): {'input_text': 'This is bad', 'has_sensitive_content': True, 'moderation_result': 'Content rejected: sensitive content found.'}
```

### 💡 记忆要点
- 节点是 LangGraph 的工作单元：每个节点是一个函数，执行特定任务并返回更新后的状态。
- 状态一致性：节点函数必须返回字典，键对应状态字段，LangGraph 会自动合并更新。
- 模块化设计：通过添加多个节点，可以将复杂流程分解为简单、可测试的组件。
- 错误处理：确保节点函数正确处理状态格式，避免运行时异常。