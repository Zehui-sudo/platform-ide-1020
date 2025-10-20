```markdown
## 使用 `get_graph().draw_mermaid()` 进行可视化

### 🎯 核心概念
`get_graph().draw_mermaid()` 是 LangGraph 提供的强大可视化工具，它能将复杂的 Agent 工作流转换为清晰的 Mermaid 图表，帮助开发者直观理解图结构、调试流程逻辑，是构建和维护复杂多步骤 Agent 系统的关键工具。

### 💡 使用方式
核心 API 非常简单：在编译图后调用 `get_graph().draw_mermaid()` 即可生成图的 Mermaid 表示。

```python
graph = workflow.compile()
print(graph.get_graph().draw_mermaid())
```

### 📚 Level 1: 基础认知（30秒理解）
最简单的线性工作流可视化示例：

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

# 定义状态
class State(TypedDict):
    message: str

# 定义节点函数
def node1(state: State):
    return {"message": state["message"] + " processed by node1"}

def node2(state: State):
    return {"message": state["message"] + " → node2"}

# 构建图
workflow = StateGraph(State)
workflow.add_node("node1", node1)
workflow.add_node("node2", node2)
workflow.set_entry_point("node1")
workflow.add_edge("node1", "node2")
workflow.add_edge("node2", END)

# 编译并可视化
graph = workflow.compile()
print("Mermaid 图表：")
print(graph.get_graph().draw_mermaid())
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 可视化条件分支
展示包含条件分支的复杂图结构：

```python
from langgraph.graph import StateGraph, END
from langgraph.graph import add_messages
from typing import TypedDict, Literal
from typing_extensions import Annotated

# 定义包含决策状态的状态
class State(TypedDict):
    messages: Annotated[list, add_messages]
    decision: Literal["continue", "end"]

def start_node(state: State):
    return {"messages": [("user", "Hello! Should we continue?")]}

def process_node(state: State):
    last_message = state["messages"][-1][1]
    if "continue" in last_message.lower():
        return {"decision": "continue", "messages": state["messages"] + [("assistant", "Continuing processing...")]}
    else:
        return {"decision": "end", "messages": state["messages"] + [("assistant", "Ending conversation.")]}

def continue_node(state: State):
    return {"messages": state["messages"] + [("assistant", "Additional processing complete!")]}

# 构建带条件分支的图
workflow = StateGraph(State)
workflow.add_node("start", start_node)
workflow.add_node("process", process_node)
workflow.add_node("continue", continue_node)

workflow.set_entry_point("start")
workflow.add_edge("start", "process")

# 条件边
def decide_next(state: State):
    return state["decision"]

workflow.add_conditional_edges(
    "process",
    decide_next,
    {
        "continue": "continue",
        "end": END
    }
)
workflow.add_edge("continue", END)

# 编译并可视化
graph = workflow.compile()
print("条件分支图：")
print(graph.get_graph().draw_mermaid())
```

### 🔍 Level 3: 对比学习（避免陷阱）

#### 可视化时机：编译前 vs 编译后
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class State(TypedDict):
    value: int

def node1(state: State):
    return {"value": state["value"] + 1}

# 错误用法：在编译前尝试可视化
workflow = StateGraph(State)
workflow.add_node("node1", node1)
workflow.set_entry_point("node1")
workflow.add_edge("node1", END)

try:
    # 这会报错：图必须先编译
    workflow.get_graph().draw_mermaid()
except Exception as e:
    print(f"错误：{e}")

# 正确用法：编译后可视化
graph = workflow.compile()
print("正确可视化：")
print(graph.get_graph().draw_mermaid())
```

### 🚀 Level 4: 实战应用（真实场景）
多轮对话工作流可视化，包含自我修正循环：

```python
from langgraph.graph import StateGraph, END
from langgraph.graph import add_messages
from typing import TypedDict, Literal
from typing_extensions import Annotated

class State(TypedDict):
    messages: Annotated[list, add_messages]
    needs_correction: bool
    correction_count: int

def receive_input(state: State):
    user_input = "Tell me about AI"  # 模拟用户输入
    return {"messages": state["messages"] + [("user", user_input)]}

def generate_response(state: State):
    last_msg = state["messages"][-1][1] if state["messages"] else ""
    response = f"AI is a field of computer science. {'' if state['correction_count'] < 2 else '(Final answer)'}"
    return {
        "messages": state["messages"] + [("assistant", response)],
        "needs_correction": state["correction_count"] < 2,
        "correction_count": state["correction_count"] + 1
    }

def quality_check(state: State):
    # 模拟质量检查：前两次都需要修正
    return {"needs_correction": state["correction_count"] < 3}

# 构建自修正工作流
workflow = StateGraph(State)
workflow.add_node("receive", receive_input)
workflow.add_node("generate", generate_response)
workflow.add_node("check_quality", quality_check)

workflow.set_entry_point("receive")
workflow.add_edge("receive", "generate")
workflow.add_edge("generate", "check_quality")

def should_correct(state: State):
    return "correct" if state["needs_correction"] else "end"

workflow.add_conditional_edges(
    "check_quality",
    should_correct,
    {"correct": "generate", "end": END}
)

# 编译并可视化复杂循环图
graph = workflow.compile()
print("多轮自修正工作流：")
mermaid_output = graph.get_graph().draw_mermaid()
print(mermaid_output)

# 实际执行查看流程
print("\n执行结果：")
result = graph.invoke({"messages": [], "needs_correction": False, "correction_count": 0})
for msg in result["messages"]:
    print(f"{msg[0]}: {msg[1]}")
```

### 💡 记忆要点
- `get_graph().draw_mermaid()` 必须在图编译后才能调用
- Mermaid 图表能清晰展示条件分支、循环等复杂流程结构
- 可视化是调试复杂工作流和团队协作的重要工具
- 生成的 Mermaid 代码可以粘贴到支持 Mermaid 的编辑器中查看图形化结果
```