# 在流程中加入等待人工输入的节点

### 🎯 核心概念
在 LangGraph 中引入人工介入节点，允许工作流在特定节点暂停并等待外部人工输入，这对于需要人类决策、审核或补充信息的复杂 Agent 流程至关重要，确保了自动化流程的可控性和灵活性。

### 💡 使用方式
使用 `HumanApproval` 类创建人工审核节点，通过 `add_node` 添加到图中，并使用条件边控制流程分支。

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import HumanApproval
from typing import TypedDict, Annotated
import operator

# 定义状态
class State(TypedDict):
    user_input: str
    approval_status: Annotated[str, operator.add]
    final_result: str

# 创建人工审核节点
human_approval = HumanApproval(
    input_node="input_node",
    approval_node="approval_node"
)
```

### 📚 Level 1: 基础认知（30秒理解）
最简单的带有人工审核节点的流程，展示基本结构和工作原理。

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import HumanApproval
from typing import TypedDict, Annotated
import operator

# 定义状态
class State(TypedDict):
    user_input: str
    approval_status: Annotated[str, operator.add]
    final_result: str

# 创建人工审核节点
human_approval = HumanApproval(
    input_node="input_node",
    approval_node="approval_node"
)

# 定义初始节点
def input_node(state: State):
    return {"user_input": "需要人工审核的内容"}

# 定义处理节点
def process_node(state: State):
    if state.get("approval_status") == "APPROVED":
        return {"final_result": f"已审核通过: {state['user_input']}"}
    else:
        return {"final_result": "审核未通过"}

# 构建图
builder = StateGraph(State)
builder.add_node("input_node", input_node)
builder.add_node("process_node", process_node)
builder.add_node("human_approval", human_approval)

# 设置边
builder.set_entry_point("input_node")
builder.add_edge("input_node", "human_approval")
builder.add_conditional_edges(
    "human_approval",
    lambda state: "process_node" if state.get("approval_status") else "human_approval"
)
builder.add_edge("process_node", END)

# 编译图
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

# 运行图（首次运行会等待人工输入）
config = {"configurable": {"thread_id": "1"}}
result = graph.invoke({}, config)
print(result)
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 动态修改后续流程
根据人工输入的不同结果，动态决定后续执行路径。

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import HumanApproval
from typing import TypedDict, Annotated, Literal
import operator

# 扩展状态定义
class State(TypedDict):
    user_input: str
    approval_status: Annotated[str, operator.add]
    next_action: Literal["process", "revise", "reject"]
    final_result: str

# 创建带选项的人工审核
human_approval = HumanApproval(
    input_node="input_node",
    approval_node="approval_node",
    options=["APPROVE", "REVISE", "REJECT"]
)

def input_node(state: State):
    return {"user_input": "重要文档内容需要审核"}

def process_node(state: State):
    return {"final_result": f"文档已处理: {state['user_input']}"}

def revise_node(state: State):
    return {"final_result": "文档需要修订，已返回修改"}

def reject_node(state: State):
    return {"final_result": "文档已被拒绝"}

def decide_next_action(state: State):
    approval_status = state.get("approval_status", "")
    if "APPROVE" in approval_status:
        return {"next_action": "process"}
    elif "REVISE" in approval_status:
        return {"next_action": "revise"}
    else:
        return {"next_action": "reject"}

# 构建图
builder = StateGraph(State)
builder.add_node("input_node", input_node)
builder.add_node("human_approval", human_approval)
builder.add_node("decide_action", decide_next_action)
builder.add_node("process_node", process_node)
builder.add_node("revise_node", revise_node)
builder.add_node("reject_node", reject_node)

builder.set_entry_point("input_node")
builder.add_edge("input_node", "human_approval")
builder.add_edge("human_approval", "decide_action")

# 条件边根据决策选择不同路径
builder.add_conditional_edges(
    "decide_action",
    lambda state: state["next_action"] + "_node"
)

builder.add_edge("process_node", END)
builder.add_edge("revise_node", END)
builder.add_edge("reject_node", END)

# 编译并运行
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

# 首次运行等待人工输入
config = {"configurable": {"thread_id": "2"}}
initial_result = graph.invoke({}, config)
print("等待人工审核...")
```

#### 特性2: 超时和默认处理
设置超时机制，当人工未及时响应时执行默认操作。

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import HumanApproval
from typing import TypedDict, Annotated
import operator
import asyncio

class State(TypedDict):
    request: str
    approval_status: Annotated[str, operator.add]
    result: str

# 带超时的人工审核
human_approval = HumanApproval(
    input_node="create_request",
    approval_node="await_approval",
    timeout=30  # 30秒超时
)

def create_request(state: State):
    return {"request": "紧急系统访问请求"}

def process_approved(state: State):
    return {"result": "访问已授权"}

def process_timeout(state: State):
    return {"result": "请求超时，已自动拒绝"}

def check_approval(state: State):
    status = state.get("approval_status", "")
    if "APPROVED" in status:
        return "process_approved"
    elif "TIMEOUT" in status:
        return "process_timeout"
    else:
        return "await_approval"  # 继续等待

builder = StateGraph(State)
builder.add_node("create_request", create_request)
builder.add_node("await_approval", human_approval)
builder.add_node("process_approved", process_approved)
builder.add_node("process_timeout", process_timeout)

builder.set_entry_point("create_request")
builder.add_edge("create_request", "await_approval")
builder.add_conditional_edges("await_approval", check_approval)
builder.add_edge("process_approved", END)
builder.add_edge("process_timeout", END)

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

# 异步运行示例
async def run_with_timeout():
    config = {"configurable": {"thread_id": "3"}}
    result = await graph.ainvoke({}, config)
    print(result)

# asyncio.run(run_with_timeout())
```

### 🔍 Level 3: 对比学习（避免陷阱）

```python
# 错误用法：忘记使用 checkpointer，导致状态无法持久化
def wrong_human_loop():
    builder = StateGraph(State)
    builder.add_node("input", lambda state: {"data": "test"})
    builder.add_node("approval", human_approval)
    builder.set_entry_point("input")
    builder.add_edge("input", "approval")
    
    # 错误：没有使用 checkpointer
    graph = builder.compile()  # 缺少 checkpointer
    # 人工输入后状态会丢失

# 正确用法：使用 MemorySaver 或其它 checkpointer
def correct_human_loop():
    builder = StateGraph(State)
    builder.add_node("input", lambda state: {"data": "test"})
    builder.add_node("approval", human_approval)
    builder.set_entry_point("input")
    builder.add_edge("input", "approval")
    
    # 正确：使用 checkpointer 持久化状态
    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)
    return graph
```

### 🚀 Level 4: 实战应用（真实场景）
构建一个内容审核工作流，包含多级人工审核和自动处理逻辑。

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import HumanApproval
from typing import TypedDict, Annotated, Literal
import operator

class ContentReviewState(TypedDict):
    content: str
    risk_level: Literal["low", "medium", "high"]
    first_approval: Annotated[str, operator.add]
    second_approval: Annotated[str, operator.add]
    final_decision: str

def analyze_content(state: ContentReviewState):
    content = state.get("content", "")
    # 简单的风险分析逻辑
    if any(word in content.lower() for word in ["紧急", "重要", "机密"]):
        return {"risk_level": "high"}
    elif any(word in content.lower() for word in ["审核", "检查", "验证"]):
        return {"risk_level": "medium"}
    else:
        return {"risk_level": "low"}

def route_based_on_risk(state: ContentReviewState):
    risk = state.get("risk_level", "low")
    if risk == "high":
        return "high_risk_approval"
    elif risk == "medium":
        return "medium_risk_approval"
    else:
        return "auto_approve"

def auto_approve(state: ContentReviewState):
    return {"final_decision": "自动审核通过"}

def make_final_decision(state: ContentReviewState):
    approvals = state.get("first_approval", "") + state.get("second_approval", "")
    if "APPROVED" in approvals:
        return {"final_decision": "最终审核通过"}
    else:
        return {"final_decision": "审核未通过"}

# 创建不同级别的人工审核节点
first_approval = HumanApproval(
    input_node="analyze_content",
    approval_node="first_review"
)

second_approval = HumanApproval(
    input_node="first_review",
    approval_node="second_review"
)

# 构建完整审核工作流
builder = StateGraph(ContentReviewState)
builder.add_node("analyze_content", analyze_content)
builder.add_node("route_risk", route_based_on_risk)
builder.add_node("first_review", first_approval)
builder.add_node("second_review", second_approval)
builder.add_node("auto_approve", auto_approve)
builder.add_node("final_decision", make_final_decision)

builder.set_entry_point("analyze_content")
builder.add_edge("analyze_content", "route_risk")

# 基于风险等级路由
builder.add_conditional_edges(
    "route_risk",
    lambda state: state["risk_level"] + "_approval" if state["risk_level"] != "low" else "auto_approve"
)

# 高风险需要两级审核
builder.add_edge("high_risk_approval", "first_review")
builder.add_edge("first_review", "second_review")
builder.add_edge("second_review", "final_decision")

# 中等风险只需要一级审核
builder.add_edge("medium_risk_approval", "first_review")
builder.add_edge("first_review", "final_decision")

# 低风险自动通过
builder.add_edge("auto_approve", END)
builder.add_edge("final_decision", END)

# 编译并运行
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

def test_content_review(content):
    config = {"configurable": {"thread_id": f"review_{hash(content)}"}}
    initial_state = {"content": content}
    result = graph.invoke(initial_state, config)
    print(f"内容: {content}")
    print(f"风险等级: {result.get('risk_level', 'unknown')}")
    print(f"最终决定: {result.get('final_decision', 'pending')}")
    print("-" * 50)

# 测试不同内容
test_content_review("这是一篇普通博客文章")
test_content_review("需要审核的重要公告")
test_content_review("紧急机密文件请立即处理")
```

### 💡 记忆要点
- 使用 `HumanApproval` 类创建人工介入节点，必须配合 `checkpointer` 使用
- 人工输入通过条件边影响后续流程走向，实现动态工作流
- 可以设置超时机制来处理人工未响应的情况
- 多级人工审核可以通过串联多个 `HumanApproval` 节点实现
- 人工介入节点的状态更新使用 `Annotated[str, operator.add]` 来累积审核结果