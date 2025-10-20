# State (状态): 图的记忆

### 🎯 核心概念
State 是 LangGraph 中用于在图的执行过程中存储和传递数据的核心机制，它解决了多步骤 Agent 流程中的状态管理问题，是构建复杂工作流的关键基础。

### 💡 使用方式
在 LangGraph 中，State 通过 `StateGraph` 类定义，使用 TypedDict 来声明状态结构。每个节点函数接收并返回状态，图会自动管理状态的更新和传递。

```python
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
```

### 📚 Level 1: 基础认知（30秒理解）
最简单的状态使用示例：创建一个维护对话历史的状态

```python
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

# 定义状态结构
class ConversationState(TypedDict):
    messages: List[str]
    user_name: str

# 创建节点函数
def greet_user(state: ConversationState):
    return {"messages": [f"Hello, {state['user_name']}! How can I help you today?"]}

def respond_to_message(state: ConversationState):
    last_message = state["messages"][-1]
    return {"messages": [f"I received your message: '{last_message}'"]}

# 构建图
builder = StateGraph(ConversationState)

# 添加节点
builder.add_node("greet", greet_user)
builder.add_node("respond", respond_to_message)

# 设置入口和边
builder.set_entry_point("greet")
builder.add_edge("greet", "respond")
builder.add_edge("respond", END)

# 编译图
graph = builder.compile()

# 运行图
initial_state = {"messages": [], "user_name": "Alice"}
result = graph.invoke(initial_state)
print("Final state:", result)
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 状态更新与合并
LangGraph 自动处理多个节点返回的状态更新，支持部分更新

```python
from typing import TypedDict
from langgraph.graph import StateGraph, END

class UserProfileState(TypedDict):
    name: str
    age: int
    preferences: dict
    conversation_history: list

def collect_name(state: UserProfileState):
    return {"name": "John Doe"}

def collect_age(state: UserProfileState):
    return {"age": 30}

def collect_preferences(state: UserProfileState):
    return {"preferences": {"theme": "dark", "language": "en"}}

def finalize_profile(state: UserProfileState):
    summary = f"Profile: {state['name']}, {state['age']} years, Preferences: {state['preferences']}"
    return {"conversation_history": [summary]}

# 构建图
builder = StateGraph(UserProfileState)
builder.add_node("get_name", collect_name)
builder.add_node("get_age", collect_age)
builder.add_node("get_prefs", collect_preferences)
builder.add_node("finalize", finalize_profile)

# 设置线性流程
builder.set_entry_point("get_name")
builder.add_edge("get_name", "get_age")
builder.add_edge("get_age", "get_prefs")
builder.add_edge("get_prefs", "finalize")
builder.add_edge("finalize", END)

graph = builder.compile()

# 运行 - 初始状态可以为空或部分字段
result = graph.invoke({})
print("Final profile:", result)
```

#### 特性2: 状态类型安全与验证
使用 TypedDict 确保状态结构的类型安全

```python
from typing import TypedDict, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END

# 使用更严格的状态定义
class StrictState(TypedDict):
    task: str
    progress: float  # 0.0 to 1.0
    metadata: dict
    completed: bool

def start_task(state: StrictState):
    return {"task": "Process data", "progress": 0.0, "completed": False}

def update_progress(state: StrictState):
    new_progress = min(state["progress"] + 0.3, 1.0)
    completed = new_progress >= 1.0
    return {"progress": new_progress, "completed": completed}

def add_metadata(state: StrictState):
    return {"metadata": {"started_at": "2024-01-01", "priority": "high"}}

builder = StateGraph(StrictState)
builder.add_node("start", start_task)
builder.add_node("progress", update_progress)
builder.add_node("metadata", add_metadata)

builder.set_entry_point("start")
builder.add_edge("start", "progress")
builder.add_edge("progress", "metadata")
builder.add_edge("metadata", END)

graph = builder.compile()

result = graph.invoke({})
print("Task completion state:", result)
```

### 🔍 Level 3: 对比学习（避免陷阱）

```python
from typing import TypedDict
from langgraph.graph import StateGraph, END

class CounterState(TypedDict):
    count: int

# ❌ 错误用法：直接修改状态而不是返回更新
def bad_increment(state: CounterState):
    state["count"] += 1  # 这不会正确更新状态
    return state

# ✅ 正确用法：返回要更新的字段
def good_increment(state: CounterState):
    return {"count": state["count"] + 1}

builder = StateGraph(CounterState)
builder.add_node("increment", good_increment)  # 使用正确的方法
builder.set_entry_point("increment")
builder.add_edge("increment", END)

graph = builder.compile()

# 测试
result = graph.invoke({"count": 0})
print("Count after increment:", result["count"])  # 应该是 1
```

### 🚀 Level 4: 实战应用（真实场景）
构建一个多轮对话系统，维护对话上下文和用户偏好

```python
from typing import TypedDict, List, Literal
from langgraph.graph import StateGraph, END

class DialogState(TypedDict):
    messages: List[str]
    user_intent: Literal["greeting", "question", "farewell", None]
    user_mood: Literal["happy", "neutral", "upset"]
    conversation_topic: str
    response_count: int

def detect_intent(state: DialogState):
    last_message = state["messages"][-1] if state["messages"] else ""
    
    if "hello" in last_message.lower():
        intent = "greeting"
    elif "?" in last_message:
        intent = "question"
    elif "bye" in last_message.lower():
        intent = "farewell"
    else:
        intent = None
    
    return {"user_intent": intent}

def analyze_mood(state: DialogState):
    last_message = state["messages"][-1] if state["messages"] else ""
    
    if "!" in last_message or "great" in last_message:
        mood = "happy"
    elif "sad" in last_message or "angry" in last_message:
        mood = "upset"
    else:
        mood = "neutral"
    
    return {"user_mood": mood}

def generate_response(state: DialogState):
    response_count = state.get("response_count", 0) + 1
    
    if state["user_intent"] == "greeting":
        response = "Hello! How can I help you today?"
    elif state["user_intent"] == "question":
        response = "That's an interesting question. Let me think about it."
    elif state["user_intent"] == "farewell":
        response = "Goodbye! Have a great day!"
    else:
        response = "I'm here to help. What would you like to talk about?"
    
    # 根据情绪调整回应
    if state["user_mood"] == "happy":
        response += " 😊"
    elif state["user_mood"] == "upset":
        response = "I'm sorry you're feeling that way. " + response
    
    return {
        "messages": [response],
        "response_count": response_count,
        "conversation_topic": state["messages"][-1][:20] + "..." if state["messages"] else "general"
    }

# 构建多轮对话图
builder = StateGraph(DialogState)
builder.add_node("intent_detection", detect_intent)
builder.add_node("mood_analysis", analyze_mood)
builder.add_node("response_generation", generate_response)

builder.set_entry_point("intent_detection")
builder.add_edge("intent_detection", "mood_analysis")
builder.add_edge("mood_analysis", "response_generation")
builder.add_edge("response_generation", END)

graph = builder.compile()

# 模拟多轮对话
conversation = [
    "Hello there!",
    "How does LangGraph handle state management?",
    "I'm feeling great today!",
    "Bye for now!"
]

current_state = {"messages": [], "user_intent": None, "user_mood": "neutral", "conversation_topic": "", "response_count": 0}

for i, message in enumerate(conversation):
    print(f"\n--- Round {i+1} ---")
    print(f"User: {message}")
    
    current_state["messages"].append(message)
    current_state = graph.invoke(current_state)
    
    print(f"Assistant: {current_state['messages'][-1]}")
    print(f"Detected intent: {current_state['user_intent']}")
    print(f"Detected mood: {current_state['user_mood']}")
    print(f"Response count: {current_state['response_count']}")

print(f"\nFinal conversation topic: {current_state['conversation_topic']}")
```

### 💡 记忆要点
- State 使用 TypedDict 定义，提供类型安全和结构清晰性
- 节点函数应该返回要更新的字段字典，而不是直接修改传入的状态
- LangGraph 自动合并多个节点返回的状态更新
- State 是整个图的共享记忆，使得多步骤流程能够保持上下文
- 合理设计状态结构是构建复杂工作流的关键基础