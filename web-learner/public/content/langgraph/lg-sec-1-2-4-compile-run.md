# 编译与运行 (compile, stream)

### 🎯 核心概念
编译与运行是将构建好的 LangGraph 图转换为可执行对象并启动工作流的关键步骤，它使得静态的图定义能够处理动态的输入数据，是构建复杂 Agent 流程的基础。

### 💡 使用方式
LangGraph 提供了两种主要的执行方式：
- `compile()`: 将图编译为可执行对象
- `stream()`: 以流式方式执行图，可实时观察执行过程

```python
# 基本用法
compiled_graph = graph.compile()
result = compiled_graph.invoke(input_state)

# 流式执行
for step in graph.stream(input_state):
    print(step)
```

### 📚 Level 1: 基础认知（30秒理解）
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

# 定义状态
class State(TypedDict):
    message: str

# 定义节点函数
def process_message(state: State) -> State:
    return {"message": f"Processed: {state['message']}"}

# 构建图
graph = StateGraph(State)
graph.add_node("processor", process_message)
graph.set_entry_point("processor")
graph.set_finish_point("processor")

# 编译图
compiled_graph = graph.compile()

# 运行图
input_state = {"message": "Hello LangGraph!"}
result = compiled_graph.invoke(input_state)
print(result["message"])  # 输出: Processed: Hello LangGraph!
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 流式执行与实时监控
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict
import time

class State(TypedDict):
    message: str
    steps: int

def step1(state: State) -> State:
    time.sleep(0.5)  # 模拟处理时间
    return {"message": state["message"] + " → Step1", "steps": state["steps"] + 1}

def step2(state: State) -> State:
    time.sleep(0.5)
    return {"message": state["message"] + " → Step2", "steps": state["steps"] + 1}

# 构建图
graph = StateGraph(State)
graph.add_node("step1", step1)
graph.add_node("step2", step2)
graph.add_edge("step1", "step2")
graph.add_edge("step2", END)
graph.set_entry_point("step1")

# 流式执行，实时观察每个节点的输出
input_state = {"message": "Start", "steps": 0}
print("流式执行过程:")
for step_name, step_output in graph.stream(input_state):
    print(f"节点 {step_name}: {step_output}")

print("\n最终结果:")
result = graph.compile().invoke(input_state)
print(result)
```

#### 特性2: 批量处理与配置参数
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class State(TypedDict):
    messages: List[str]
    processed_count: int

def process_batch(state: State) -> State:
    processed = [f"PROCESSED: {msg}" for msg in state["messages"]]
    return {
        "messages": processed,
        "processed_count": state["processed_count"] + len(processed)
    }

graph = StateGraph(State)
graph.add_node("batch_processor", process_batch)
graph.set_entry_point("batch_processor")
graph.set_finish_point("batch_processor")

compiled_graph = graph.compile()

# 批量处理
batch_input = {
    "messages": ["Hello", "World", "LangGraph"],
    "processed_count": 0
}

# 使用配置参数（这里演示配置传递，虽然这个简单例子不需要配置）
result = compiled_graph.invoke(
    batch_input,
    config={"recursion_limit": 50}  # 可配置递归限制等参数
)

print(f"处理了 {result['processed_count']} 条消息")
print("处理结果:", result["messages"])
```

### 🔍 Level 3: 对比学习（避免陷阱）

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class State(TypedDict):
    value: int

def increment(state: State) -> State:
    return {"value": state["value"] + 1}

graph = StateGraph(State)
graph.add_node("increment", increment)
graph.set_entry_point("increment")
graph.set_finish_point("increment")

# ❌ 错误用法：忘记编译直接调用
try:
    graph.invoke({"value": 1})  # 会抛出 AttributeError
except AttributeError as e:
    print(f"错误: {e}")

# ✅ 正确用法：先编译再调用
compiled_graph = graph.compile()
result = compiled_graph.invoke({"value": 1})
print(f"正确结果: {result}")  # 输出: {'value': 2}

# ❌ 错误用法：错误的状态结构
try:
    compiled_graph.invoke({"wrong_field": 1})  # 缺少必需的 value 字段
except Exception as e:
    print(f"状态错误: {e}")

# ✅ 正确用法：提供完整的状态
correct_result = compiled_graph.invoke({"value": 5})
print(f"正确状态的结果: {correct_result}")
```

### 🚀 Level 4: 实战应用（真实场景）

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal
import json

class CustomerServiceState(TypedDict):
    user_query: str
    response: str
    sentiment: Literal["positive", "negative", "neutral"]
    processed: bool

def analyze_sentiment(state: CustomerServiceState) -> CustomerServiceState:
    """分析用户查询的情感倾向"""
    query = state["user_query"].lower()
    if any(word in query for word in ["problem", "issue", "help", "urgent"]):
        sentiment = "negative"
    elif any(word in query for word in ["thank", "great", "awesome"]):
        sentiment = "positive"
    else:
        sentiment = "neutral"
    
    return {**state, "sentiment": sentiment}

def generate_response(state: CustomerServiceState) -> CustomerServiceState:
    """根据情感生成相应的回复"""
    if state["sentiment"] == "negative":
        response = "I'm sorry you're experiencing issues. Let me help you resolve this problem."
    elif state["sentiment"] == "positive":
        response = "Thank you for your positive feedback! We're glad to hear you're enjoying our service."
    else:
        response = "Thank you for contacting us. How can I assist you today?"
    
    return {**state, "response": response, "processed": True}

# 构建客服工作流
graph = StateGraph(CustomerServiceState)
graph.add_node("sentiment_analysis", analyze_sentiment)
graph.add_node("response_generation", generate_response)

graph.add_edge("sentiment_analysis", "response_generation")
graph.add_edge("response_generation", END)
graph.set_entry_point("sentiment_analysis")

# 编译图
customer_service = graph.compile()

# 测试不同场景
test_cases = [
    {"user_query": "I have a problem with my account", "response": "", "sentiment": "neutral", "processed": False},
    {"user_query": "This service is awesome!", "response": "", "sentiment": "neutral", "processed": False},
    {"user_query": "I need some information", "response": "", "sentiment": "neutral", "processed": False}
]

print("客服工作流测试结果:")
print("-" * 50)

for i, test_case in enumerate(test_cases, 1):
    result = customer_service.invoke(test_case)
    print(f"案例 {i}:")
    print(f"  用户查询: {result['user_query']}")
    print(f"  情感分析: {result['sentiment']}")
    print(f"  生成回复: {result['response']}")
    print(f"  处理状态: {'已完成' if result['processed'] else '未完成'}")
    print("-" * 30)

# 流式执行演示
print("\n流式执行演示:")
negative_query = {"user_query": "This is urgent! I need help now!", "response": "", "sentiment": "neutral", "processed": False}
for step_name, step_output in graph.stream(negative_query):
    print(f"步骤 '{step_name}': {json.dumps(step_output, indent=2)}")
```

### 💡 记忆要点
- `compile()` 是将图定义转换为可执行对象的必要步骤，忘记编译是常见错误
- `stream()` 提供实时执行监控，适合调试和观察复杂工作流的执行过程
- 输入状态必须与定义的 State 结构完全匹配，否则会抛出异常
- 流式执行返回生成器，可以逐步处理每个节点的输出结果
- 编译后的图可以重复使用，适合处理多个输入请求