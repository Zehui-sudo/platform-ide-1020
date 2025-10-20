# 条件边的使用

### 🎯 核心概念
条件边允许 LangGraph 根据当前状态的值动态选择下一个节点，实现分支逻辑，这是构建智能 Agent 工作流的关键，因为它使流程能适应不同输入或情境，实现更复杂的决策路径。

### 💡 使用方式
在 LangGraph 中，条件边通过 `add_conditional_edges` 方法添加，需要一个条件函数（返回下一个节点名称）和可能的目标节点映射。核心 API 包括：
- `graph.add_conditional_edges(source, condition, path_map)`: 添加条件边，其中 `condition` 是函数，`path_map` 是可选的节点映射。

### 📚 Level 1: 基础认知（30秒理解）
以下是一个最简单且完整可运行的示例：根据输入数字是奇数还是偶数，选择不同的节点处理。
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

# 定义状态结构
class State(TypedDict):
    number: int
    result: str

# 定义节点函数
def process_even(state: State) -> State:
    return {"result": f"{state['number']} is even."}

def process_odd(state: State) -> State:
    return {"result": f"{state['number']} is odd."}

# 条件函数：根据数字奇偶性返回下一个节点名称
def route_by_number(state: State) -> str:
    if state["number"] % 2 == 0:
        return "even_node"
    else:
        return "odd_node"

# 构建图
graph = StateGraph(State)
graph.add_node("even_node", process_even)
graph.add_node("odd_node", process_odd)
graph.set_entry_point("start")
# 添加条件边：从"start"开始，根据条件函数路由
graph.add_conditional_edges("start", route_by_number, {"even_node": "even_node", "odd_node": "odd_node"})
graph.add_edge("even_node", END)
graph.add_edge("odd_node", END)

# 编译图
app = graph.compile()

# 运行图
if __name__ == "__main__":
    # 测试偶数
    result1 = app.invoke({"number": 4})
    print(result1["result"])  # 输出: 4 is even.
    # 测试奇数
    result2 = app.invoke({"number": 3})
    print(result2["result"])  # 输出: 3 is odd.
```

### 📈 Level 2: 核心特性（深入理解）
#### 特性1: 基于多个状态字段的条件路由
条件函数可以访问状态的多个字段，实现更复杂的决策。例如，根据数字和用户类型路由。
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

# 扩展状态结构
class AdvancedState(TypedDict):
    number: int
    user_type: str  # e.g., "vip" or "normal"
    result: str

# 节点函数
def vip_even(state: AdvancedState) -> AdvancedState:
    return {"result": f"VIP even: {state['number']} is special!"}

def normal_even(state: AdvancedState) -> AdvancedState:
    return {"result": f"Normal even: {state['number']} is even."}

def odd_handler(state: AdvancedState) -> AdvancedState:
    return {"result": f"Odd: {state['number']} is odd for {state['user_type']} user."}

# 条件函数：基于数字和用户类型
def advanced_route(state: AdvancedState) -> str:
    if state["number"] % 2 == 0:
        if state["user_type"] == "vip":
            return "vip_even_node"
        else:
            return "normal_even_node"
    else:
        return "odd_node"

# 构建图
graph = StateGraph(AdvancedState)
graph.add_node("vip_even_node", vip_even)
graph.add_node("normal_even_node", normal_even)
graph.add_node("odd_node", odd_handler)
graph.set_entry_point("start")
graph.add_conditional_edges("start", advanced_route, {
    "vip_even_node": "vip_even_node",
    "normal_even_node": "normal_even_node",
    "odd_node": "odd_node"
})
graph.add_edge("vip_even_node", END)
graph.add_edge("normal_even_node", END)
graph.add_edge("odd_node", END)

app = graph.compile()

# 运行示例
if __name__ == "__main__":
    # VIP 用户偶数
    result1 = app.invoke({"number": 4, "user_type": "vip"})
    print(result1["result"])  # 输出: VIP even: 4 is special!
    # 普通用户奇数
    result2 = app.invoke({"number": 3, "user_type": "normal"})
    print(result2["result"])  # 输出: Odd: 3 is odd for normal user.
```

### 🔍 Level 3: 对比学习（避免陷阱）
常见陷阱是条件函数没有覆盖所有可能情况，导致运行时错误。以下展示错误用法和正确用法。
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class State(TypedDict):
    value: int
    output: str

def positive_node(state: State) -> State:
    return {"output": "Positive"}

def negative_node(state: State) -> State:
    return {"output": "Negative"}

# 错误用法：条件函数未处理零值，可能导致 KeyError 或未定义行为
def bad_condition(state: State) -> str:
    if state["value"] > 0:
        return "positive_node"
    elif state["value"] < 0:  # 缺少 zero 的处理
        return "negative_node"
    # 如果 value==0，没有返回，会出错

# 正确用法：覆盖所有情况，包括默认路由
def good_condition(state: State) -> str:
    if state["value"] > 0:
        return "positive_node"
    elif state["value"] < 0:
        return "negative_node"
    else:
        return "default_node"  # 处理零值

def default_node(state: State) -> State:
    return {"output": "Zero or default"}

# 构建错误图（会导致错误）
bad_graph = StateGraph(State)
bad_graph.add_node("positive_node", positive_node)
bad_graph.add_node("negative_node", negative_node)
bad_graph.set_entry_point("start")
bad_graph.add_conditional_edges("start", bad_condition, {"positive_node": "positive_node", "negative_node": "negative_node"})  # 缺少 default_node 映射
# 尝试运行会报错：例如 app.invoke({"value": 0})

# 构建正确图
good_graph = StateGraph(State)
good_graph.add_node("positive_node", positive_node)
good_graph.add_node("negative_node", negative_node)
good_graph.add_node("default_node", default_node)
good_graph.set_entry_point("start")
good_graph.add_conditional_edges("start", good_condition, {
    "positive_node": "positive_node",
    "negative_node": "negative_node",
    "default_node": "default_node"  # 包括所有可能返回
})
good_graph.add_edge("positive_node", END)
good_graph.add_edge("negative_node", END)
good_graph.add_edge("default_node", END)

app_good = good_graph.compile()

# 运行正确示例
if __name__ == "__main__":
    try:
        # 错误示例会崩溃，但这里跳过运行错误图
        # 正确示例处理零值
        result = app_good.invoke({"value": 0})
        print(result["output"])  # 输出: Zero or default
    except Exception as e:
        print(f"Error: {e}")  # 错误图会触发异常，但正确图不会
```

### 🚀 Level 4: 实战应用（真实场景）
设计一个简单的客户服务聊天机器人：根据用户输入的情绪（正面、负面、中性）路由到不同的处理节点。
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict
import re  # 用于简单情绪分析

# 状态结构
class ChatState(TypedDict):
    user_input: str
    response: str
    emotion: str  # 存储检测到的情绪

# 节点函数
def detect_emotion(state: ChatState) -> ChatState:
    text = state["user_input"].lower()
    if re.search(r"\b(高兴|好|谢谢|满意)\b", text):
        emotion = "positive"
    elif re.search(r"\b(生气|糟糕|差|投诉)\b", text):
        emotion = "negative"
    else:
        emotion = "neutral"
    return {"emotion": emotion}

def positive_response(state: ChatState) -> ChatState:
    return {"response": "感谢您的积极反馈！我们很高兴为您服务。"}

def negative_response(state: ChatState) -> ChatState:
    return {"response": "抱歉听到您的不愉快，我们会尽快解决您的问题。"}

def neutral_response(state: ChatState) -> ChatState:
    return {"response": "谢谢您的输入，请问有什么具体需要帮助的吗？"}

# 条件函数：根据情绪路由
def route_by_emotion(state: ChatState) -> str:
    return f"{state['emotion']}_response"

# 构建图
graph = StateGraph(ChatState)
graph.add_node("detect_emotion_node", detect_emotion)
graph.add_node("positive_response_node", positive_response)
graph.add_node("negative_response_node", negative_response)
graph.add_node("neutral_response_node", neutral_response)
graph.set_entry_point("detect_emotion_node")
graph.add_conditional_edges("detect_emotion_node", route_by_emotion, {
    "positive_response": "positive_response_node",
    "negative_response": "negative_response_node",
    "neutral_response": "neutral_response_node"
})
graph.add_edge("positive_response_node", END)
graph.add_edge("negative_response_node", END)
graph.add_edge("neutral_response_node", END)

app = graph.compile()

# 运行示例
if __name__ == "__main__":
    test_inputs = [
        {"user_input": "我很高兴你们的服务！"},
        {"user_input": "这太糟糕了，我要投诉。"},
        {"user_input": "我想问问价格。"}
    ]
    for input_state in test_inputs:
        result = app.invoke(input_state)
        print(f"Input: {input_state['user_input']}")
        print(f"Response: {result['response']}\n")
# 预期输出:
# Input: 我很高兴你们的服务！
# Response: 感谢您的积极反馈！我们很高兴为您服务。
#
# Input: 这太糟糕了，我要投诉。
# Response: 抱歉听到您的不愉快，我们会尽快解决您的问题。
#
# Input: 我想问问价格。
# Response: 谢谢您的输入，请问有什么具体需要帮助的吗？
```

### 💡 记忆要点
- 条件边通过 `add_conditional_edges` 添加，依赖条件函数返回下一个节点名称。
- 条件函数必须覆盖所有可能状态情况，避免运行时错误。
- 条件边使工作流动态化，适合实现分支逻辑，如路由、决策树。
- 在真实应用中，结合状态多个字段可以实现复杂路由策略。