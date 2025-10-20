```markdown
## Edges (边): 连接流程

### 🎯 核心概念
边（Edges）定义了图中节点之间的连接关系，决定了工作流的执行路径。它是构建复杂 Agent 流程的关键，通过控制节点间的流转逻辑，实现条件分支、循环和并行执行等高级功能。

### 💡 使用方式
在 LangGraph 中，使用 `add_edge()` 方法连接两个节点，或使用 `add_conditional_edges()` 添加条件边（将在后续章节详细介绍）。

### 📚 Level 1: 基础认知（30秒理解）
最简单的线性流程：两个节点通过边连接，按顺序执行。

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

# 定义状态
class State(TypedDict):
    message: str

# 定义节点函数
def node1(state: State) -> State:
    return {"message": state["message"] + "经过节点1处理 "}

def node2(state: State) -> State:
    return {"message": state["message"] + "经过节点2处理 "}

# 构建图
graph = StateGraph(State)
graph.add_node("node1", node1)
graph.add_node("node2", node2)

# 添加边：连接节点
graph.add_edge("node1", "node2")  # node1 -> node2
graph.add_edge("node2", END)     # node2 -> 结束

# 设置入口点
graph.set_entry_point("node1")

# 编译图
app = graph.compile()

# 运行图
result = app.invoke({"message": "初始输入 "})
print(result["message"])
# 输出: 初始输入 经过节点1处理 经过节点2处理 
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 多路径分支
通过添加多条边，实现从一个节点到多个不同节点的分支。

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class State(TypedDict):
    message: str
    route: str

def start_node(state: State) -> State:
    return {"message": "开始处理", "route": "path_b"}

def path_a_node(state: State) -> State:
    return {"message": state["message"] + " → 路径A"}

def path_b_node(state: State) -> State:
    return {"message": state["message"] + " → 路径B"}

def final_node(state: State) -> State:
    return {"message": state["message"] + " → 完成"}

# 构建图
graph = StateGraph(State)
graph.add_node("start", start_node)
graph.add_node("path_a", path_a_node)
graph.add_node("path_b", path_b_node)
graph.add_node("final", final_node)

# 添加多条边实现分支
graph.add_edge("start", "path_a")
graph.add_edge("start", "path_b")
graph.add_edge("path_a", "final")
graph.add_edge("path_b", "final")
graph.add_edge("final", END)

graph.set_entry_point("start")

app = graph.compile()

# 测试不同路径
result = app.invoke({"message": "", "route": "path_a"})
print(result["message"])
# 输出: 开始处理 → 路径A → 完成
```

#### 特性2: 跳过节点
通过直接连接到 END，实现节点跳过功能。

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class State(TypedDict):
    message: str
    skip_processing: bool

def input_node(state: State) -> State:
    if state["skip_processing"]:
        return {"message": "直接跳过处理", "skip_processing": True}
    return {"message": "需要处理", "skip_processing": False}

def process_node(state: State) -> State:
    return {"message": state["message"] + " → 已处理"}

def decide_next_node(state: State) -> State:
    # 根据条件决定下一个节点
    if state["skip_processing"]:
        return {"message": state["message"] + " → 跳过后续", "skip_processing": True}
    return {"message": state["message"], "skip_processing": False}

graph = StateGraph(State)
graph.add_node("input", input_node)
graph.add_node("process", process_node)
graph.add_node("decide", decide_next_node)

# 添加边连接
graph.add_edge("input", "decide")
graph.add_edge("decide", "process")
graph.add_edge("decide", END)  # 跳过处理的路径
graph.add_edge("process", END)

graph.set_entry_point("input")

app = graph.compile()

# 测试跳过处理
result1 = app.invoke({"message": "", "skip_processing": True})
print("跳过处理:", result1["message"])

# 测试正常处理
result2 = app.invoke({"message": "", "skip_processing": False})
print("正常处理:", result2["message"])
```

### 🔍 Level 3: 对比学习（避免陷阱）

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class State(TypedDict):
    value: int

# 错误用法：忘记添加必要的边
def incorrect_usage():
    graph = StateGraph(State)
    
    def node_a(state: State) -> State:
        return {"value": state["value"] + 1}
    
    def node_b(state: State) -> State:
        return {"value": state["value"] * 2}
    
    graph.add_node("A", node_a)
    graph.add_node("B", node_b)
    
    # 错误：只添加了 A->B，但没有设置入口和出口
    graph.add_edge("A", "B")
    # 缺少: graph.set_entry_point("A")
    # 缺少: graph.add_edge("B", END)
    
    try:
        app = graph.compile()
        result = app.invoke({"value": 5})
        print(result)
    except Exception as e:
        print(f"错误: {e}")

# 正确用法：完整的边连接
def correct_usage():
    graph = StateGraph(State)
    
    def node_a(state: State) -> State:
        return {"value": state["value"] + 1}
    
    def node_b(state: State) -> State:
        return {"value": state["value"] * 2}
    
    graph.add_node("A", node_a)
    graph.add_node("B", node_b)
    
    # 正确：完整的边连接
    graph.add_edge("A", "B")
    graph.add_edge("B", END)
    graph.set_entry_point("A")
    
    app = graph.compile()
    result = app.invoke({"value": 5})
    print(f"正确结果: {result}")

print("=== 错误用法 ===")
incorrect_usage()

print("\n=== 正确用法 ===")
correct_usage()
```

### 🚀 Level 4: 实战应用（真实场景）
构建一个简单的文档处理流水线，包含输入验证、内容处理和结果输出三个阶段。

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
import re

class DocumentState(TypedDict):
    raw_text: str
    processed_text: str
    is_valid: bool
    error_message: str
    steps: List[str]

def validate_input(state: DocumentState) -> DocumentState:
    """验证输入文本"""
    steps = state.get("steps", [])
    steps.append("输入验证")
    
    if not state["raw_text"] or len(state["raw_text"].strip()) < 5:
        return {
            "is_valid": False,
            "error_message": "输入文本太短或为空",
            "steps": steps
        }
    
    return {
        "is_valid": True,
        "error_message": "",
        "steps": steps,
        "raw_text": state["raw_text"]
    }

def process_content(state: DocumentState) -> DocumentState:
    """处理文本内容"""
    steps = state.get("steps", [])
    steps.append("内容处理")
    
    # 简单的文本处理：去除多余空格，首字母大写
    processed = re.sub(r'\s+', ' ', state["raw_text"]).strip()
    processed = processed.capitalize()
    
    return {
        "processed_text": processed,
        "steps": steps,
        "is_valid": state["is_valid"],
        "raw_text": state["raw_text"]
    }

def generate_output(state: DocumentState) -> DocumentState:
    """生成最终输出"""
    steps = state.get("steps", [])
    steps.append("生成输出")
    
    if not state["is_valid"]:
        return {
            "processed_text": f"错误: {state['error_message']}",
            "steps": steps
        }
    
    return {
        "processed_text": f"处理结果: {state['processed_text']}",
        "steps": steps
    }

# 构建文档处理图
graph = StateGraph(DocumentState)
graph.add_node("validate", validate_input)
graph.add_node("process", process_content)
graph.add_node("output", generate_output)

# 添加边连接
graph.add_edge("validate", "process")
graph.add_edge("process", "output")
graph.add_edge("output", END)

# 添加错误处理边：验证失败时直接跳到输出
graph.add_edge("validate", "output")

graph.set_entry_point("validate")

app = graph.compile()

# 测试有效输入
print("=== 测试有效输入 ===")
result1 = app.invoke({
    "raw_text": "hello   world   this   is   a   test   ",
    "processed_text": "",
    "is_valid": True,
    "error_message": "",
    "steps": []
})
print("处理结果:", result1["processed_text"])
print("执行步骤:", result1["steps"])

print("\n=== 测试无效输入 ===")
# 测试无效输入
result2 = app.invoke({
    "raw_text": "hi",
    "processed_text": "",
    "is_valid": True,
    "error_message": "",
    "steps": []
})
print("处理结果:", result2["processed_text"])
print("执行步骤:", result2["steps"])
```

### 💡 记忆要点
- 边定义了节点之间的执行顺序和数据流向
- 每个节点必须有明确的入口和出口边连接（除了 END 节点）
- 可以通过多条边实现分支逻辑
- 边可以连接到 END 来实现提前终止
- 合理的边设计是构建复杂工作流的基础
```