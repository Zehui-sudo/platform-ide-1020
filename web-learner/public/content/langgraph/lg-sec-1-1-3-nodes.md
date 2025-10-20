```markdown
# Nodes (节点): 工作单元

### 🎯 核心概念
节点是 LangGraph 中最基本的工作单元，负责执行具体的任务和处理状态。它解决了"如何将复杂流程分解为可管理的步骤"的问题，是构建可维护、可测试的 Agent 流程的关键组件。

### 💡 使用方式
在 LangGraph 中，节点是一个接收状态、处理业务逻辑，并返回更新后状态的函数。基本用法：
```python
def node_function(state: State):
    # 处理逻辑
    return {"key": "value"}  # 返回状态更新
```

### 📚 Level 1: 基础认知（30秒理解）
最简单的节点示例：一个接收用户输入并生成问候语的节点。

```python
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

# 定义状态结构
class State(TypedDict):
    user_input: str
    greeting: str

# 创建问候节点
def greeting_node(state: State):
    return {"greeting": f"你好，{state['user_input']}！欢迎使用 LangGraph！"}

# 构建图
graph = StateGraph(State)
graph.add_node("greet", greeting_node)
graph.set_entry_point("greet")
graph.set_finish_point("greet")
app = graph.compile()

# 运行图
result = app.invoke({"user_input": "开发者"})
print(result["greeting"])
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 多节点协作
节点可以协同工作，每个节点专注于特定任务。

```python
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class State(TypedDict):
    user_input: str
    processed_input: str
    response: str

# 输入处理节点
def process_input_node(state: State):
    processed = state['user_input'].strip().upper()
    return {"processed_input": processed}

# 响应生成节点
def generate_response_node(state: State):
    response = f"处理后的输入: {state['processed_input']}"
    return {"response": response}

# 构建多节点工作流
graph = StateGraph(State)
graph.add_node("process", process_input_node)
graph.add_node("generate", generate_response_node)

# 设置节点连接
graph.set_entry_point("process")
graph.add_edge("process", "generate")
graph.set_finish_point("generate")

app = graph.compile()

# 执行
result = app.invoke({"user_input": "  hello world  "})
print(result["response"])
```

#### 特性2: 状态修改与传递
节点可以读取和修改共享状态。

```python
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class State(TypedDict):
    counter: int
    message: str

# 计数器节点
def counter_node(state: State):
    new_count = state.get('counter', 0) + 1
    return {"counter": new_count, "message": f"计数: {new_count}"}

graph = StateGraph(State)
graph.add_node("count", counter_node)
graph.set_entry_point("count")
graph.set_finish_point("count")

app = graph.compile()

# 多次执行展示状态保持
for i in range(3):
    result = app.invoke({})
    print(result["message"])
```

### 🔍 Level 3: 对比学习（避免陷阱）

```python
# 错误用法：直接修改传入的状态（违反函数式编程原则）
def bad_node(state: State):
    state['counter'] = state.get('counter', 0) + 1  # ❌ 直接修改
    return state

# 正确用法：返回新的状态更新
def good_node(state: State):
    return {"counter": state.get('counter', 0) + 1}  # ✅ 返回更新字典
```

### 🚀 Level 4: 实战应用（真实场景）
构建一个简单的用户反馈处理流水线。

```python
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import re

class FeedbackState(TypedDict):
    user_feedback: str
    sentiment: str
    response: str

# 情感分析节点
def sentiment_analysis_node(state: FeedbackState):
    feedback = state['user_feedback'].lower()
    if any(word in feedback for word in ['great', 'awesome', 'excellent']):
        return {"sentiment": "positive"}
    elif any(word in feedback for word in ['bad', 'terrible', 'awful']):
        return {"sentiment": "negative"}
    else:
        return {"sentiment": "neutral"}

# 响应生成节点
def response_generation_node(state: FeedbackState):
    if state['sentiment'] == 'positive':
        return {"response": "感谢您的积极反馈！我们会继续努力。"}
    elif state['sentiment'] == 'negative':
        return {"response": "很抱歉让您失望了。我们会认真改进。"}
    else:
        return {"response": "感谢您的反馈。我们会持续优化服务。"}

# 构建反馈处理流水线
graph = StateGraph(FeedbackState)
graph.add_node("analyze", sentiment_analysis_node)
graph.add_node("respond", response_generation_node)

graph.set_entry_point("analyze")
graph.add_edge("analyze", "respond")
graph.set_finish_point("respond")

feedback_app = graph.compile()

# 测试不同反馈
test_feedbacks = [
    "This product is awesome!",
    "I hate this service",
    "It's okay I guess"
]

for feedback in test_feedbacks:
    result = feedback_app.invoke({"user_feedback": feedback})
    print(f"反馈: {feedback}")
    print(f"回应: {result['response']}")
    print("---")
```

### 💡 记忆要点
- 节点是 LangGraph 中最基本的工作单元，每个节点负责一个特定任务
- 节点函数接收状态作为输入，返回状态更新字典
- 遵循函数式编程原则：不直接修改输入状态，而是返回新的状态更新
- 多个节点可以连接形成复杂的工作流，每个节点专注于单一职责
- 节点的设计应该保持简单和可测试性
```