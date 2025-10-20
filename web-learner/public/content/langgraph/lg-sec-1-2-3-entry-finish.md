# 设置入口和出口 (Entry/Finish Point)

### 🎯 核心概念
入口点和出口点是 LangGraph 工作流的路由控制中心，它们决定了工作流的起始位置和结束条件，是构建复杂 Agent 流程的关键基础设施。

### 💡 使用方式
在 LangGraph 中，通过 `set_entry_point()` 设置工作流起始节点，`set_finish_point()` 设置工作流终止节点，`add_edge()` 连接节点间的流转关系。

```python
graph.set_entry_point("start_node")  # 设置入口节点
graph.add_edge("start_node", "end_node")  # 添加边连接
graph.set_finish_point("end_node")  # 设置出口节点
```

### 📚 Level 1: 基础认知（30秒理解）
最简单的入口出口设置示例，展示基础工作流结构。

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

# 定义状态结构
class State(TypedDict):
    message: str

# 定义节点函数
def start_node(state: State) -> State:
    return {"message": "工作流已开始"}

def end_node(state: State) -> State:
    return {"message": state["message"] + " → 工作流已结束"}

# 构建图
graph = StateGraph(State)
graph.add_node("start", start_node)
graph.add_node("end", end_node)

# 设置入口和出口
graph.set_entry_point("start")
graph.add_edge("start", "end")
graph.set_finish_point("end")

# 编译并运行
app = graph.compile()
result = app.invoke({"message": ""})
print(result["message"])
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 多入口点配置
复杂工作流可以有多个入口点，根据不同条件启动不同流程。

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal

class State(TypedDict):
    message: str
    workflow_type: Literal["A", "B"]

def workflow_a_start(state: State) -> State:
    return {"message": "工作流A启动", "workflow_type": "A"}

def workflow_b_start(state: State) -> State:
    return {"message": "工作流B启动", "workflow_type": "B"}

def common_process(state: State) -> State:
    if state["workflow_type"] == "A":
        return {"message": state["message"] + " → A流程处理"}
    else:
        return {"message": state["message"] + " → B流程处理"}

def finalize(state: State) -> State:
    return {"message": state["message"] + " → 完成"}

# 构建图
graph = StateGraph(State)
graph.add_node("start_a", workflow_a_start)
graph.add_node("start_b", workflow_b_start)
graph.add_node("process", common_process)
graph.add_node("finish", finalize)

# 设置多入口点和流转逻辑
graph.set_entry_point("start_a")
graph.set_entry_point("start_b")
graph.add_edge("start_a", "process")
graph.add_edge("start_b", "process")
graph.add_edge("process", "finish")
graph.set_finish_point("finish")

# 编译并运行不同入口
app = graph.compile()
result_a = app.invoke({"message": "", "workflow_type": "A"})
result_b = app.invoke({"message": "", "workflow_type": "B"})

print("工作流A结果:", result_a["message"])
print("工作流B结果:", result_b["message"])
```

### 🔍 Level 3: 对比学习（避免陷阱）

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class State(TypedDict):
    content: str

def process_data(state: State) -> State:
    return {"content": state["content"] + " processed"}

# 错误用法：忘记设置入口点或出口点
graph_error = StateGraph(State)
graph_error.add_node("process", process_data)
# 缺少 set_entry_point() 和 set_finish_point()
# 编译时会报错

# 正确用法：完整设置入口和出口
graph_correct = StateGraph(State)
graph_correct.add_node("process", process_data)
graph_correct.set_entry_point("process")
graph_correct.set_finish_point("process")  # 同一节点作为入口和出口

app = graph_correct.compile()
result = app.invoke({"content": "初始数据"})
print("正确结果:", result["content"])
```

### 🚀 Level 4: 实战应用（真实场景）
构建一个客户服务请求处理流程，根据请求类型路由到不同的处理节点。

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal

class CustomerState(TypedDict):
    request_type: Literal["complaint", "inquiry", "support"]
    message: str
    processed_by: list[str]

def intake_node(state: CustomerState) -> CustomerState:
    """请求接收节点"""
    return {
        "request_type": state["request_type"],
        "message": f"已接收{state['request_type']}请求: {state['message']}",
        "processed_by": ["intake"]
    }

def handle_complaint(state: CustomerState) -> CustomerState:
    """投诉处理节点"""
    return {
        "request_type": state["request_type"],
        "message": state["message"] + " → 投诉已升级处理",
        "processed_by": state["processed_by"] + ["complaint_specialist"]
    }

def handle_inquiry(state: CustomerState) -> CustomerState:
    """咨询处理节点"""
    return {
        "request_type": state["request_type"],
        "message": state["message"] + " → 咨询已解答",
        "processed_by": state["processed_by"] + ["inquiry_agent"]
    }

def handle_support(state: CustomerState) -> CustomerState:
    """技术支持节点"""
    return {
        "request_type": state["request_type"],
        "message": state["message"] + " → 技术支持已完成",
        "processed_by": state["processed_by"] + ["support_engineer"]
    }

def finalize_request(state: CustomerState) -> CustomerState:
    """最终处理节点"""
    return {
        "request_type": state["request_type"],
        "message": state["message"] + " → 请求处理完成",
        "processed_by": state["processed_by"] + ["closing"]
    }

# 构建客户服务图
service_graph = StateGraph(CustomerState)

# 添加所有节点
service_graph.add_node("intake", intake_node)
service_graph.add_node("complaint", handle_complaint)
service_graph.add_node("inquiry", handle_inquiry)
service_graph.add_node("support", handle_support)
service_graph.add_node("finalize", finalize_request)

# 设置入口点
service_graph.set_entry_point("intake")

# 根据请求类型路由到不同处理节点
service_graph.add_conditional_edges(
    "intake",
    lambda state: state["request_type"],
    {
        "complaint": "complaint",
        "inquiry": "inquiry", 
        "support": "support"
    }
)

# 所有分支最终汇聚到最终处理
service_graph.add_edge("complaint", "finalize")
service_graph.add_edge("inquiry", "finalize")
service_graph.add_edge("support", "finalize")

# 设置出口点
service_graph.set_finish_point("finalize")

# 编译并运行
service_app = service_graph.compile()

# 测试不同请求类型
test_cases = [
    {"request_type": "complaint", "message": "产品质量问题", "processed_by": []},
    {"request_type": "inquiry", "message": "询问价格信息", "processed_by": []},
    {"request_type": "support", "message": "需要技术帮助", "processed_by": []}
]

for i, test_case in enumerate(test_cases, 1):
    result = service_app.invoke(test_case)
    print(f"\n案例 {i} - {test_case['request_type']}:")
    print("处理结果:", result["message"])
    print("处理经过:", " → ".join(result["processed_by"]))
```

### 💡 记忆要点
- 每个 LangGraph 必须至少有一个入口点 (`set_entry_point()`) 和一个出口点 (`set_finish_point()` 或 `END`)
- 入口点决定了工作流的起始执行位置，支持设置多个入口点
- 出口点标记工作流的终止条件，可以使用 `END` 特殊节点或指定具体节点
- 合理的入口出口设置是构建清晰、可维护工作流的关键
- 条件边 (`add_conditional_edges()`) 可以与入口点配合实现动态路由