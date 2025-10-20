```markdown
## 什么是 LangGraph? (解决什么问题)

### 🎯 核心概念
LangGraph 是一个用于构建复杂、有状态的多步骤工作流的框架，它解决了传统链式调用在处理循环、条件分支和并行执行时的局限性，是构建智能 Agent 系统的核心基础设施。

### 💡 使用方式
核心 API 围绕 `StateGraph` 构建，通过定义节点(nodes)和边(edges)来创建工作流，支持条件路由和循环执行。

### 📚 Level 1: 基础认知（30秒理解）
最简单的问答工作流示例：

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

# 定义状态结构
class AgentState(TypedDict):
    question: str
    answer: str

# 定义问答节点
def answer_node(state: AgentState):
    return {"answer": f"已回答: {state['question']}"}

# 构建图
graph = StateGraph(AgentState)
graph.add_node("answer", answer_node)
graph.set_entry_point("answer")
graph.set_finish_point("answer")
app = graph.compile()

# 运行图
result = app.invoke({"question": "LangGraph是什么?"})
print(result["answer"])
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 条件分支路由
```python
from langgraph.graph import StateGraph, END
from typing import Literal, TypedDict
from typing_extensions import Annotated

class RoutingState(TypedDict):
    query: str
    category: Annotated[Literal["tech", "general"], "问题类型"]

def classify_query(state: RoutingState):
    if "python" in state["query"].lower():
        return {"category": "tech"}
    return {"category": "general"}

def tech_support(state: RoutingState):
    return {"response": "技术问题已处理"}

def general_support(state: RoutingState):
    return {"response": "一般问题已处理"}

def route_by_category(state: RoutingState):
    return state["category"]

# 构建有条件路由的图
graph = StateGraph(RoutingState)
graph.add_node("classify", classify_query)
graph.add_node("tech", tech_support)
graph.add_node("general", general_support)

graph.set_entry_point("classify")
graph.add_conditional_edges("classify", route_by_category, {
    "tech": "tech",
    "general": "general"
})
graph.add_edge("tech", END)
graph.add_edge("general", END)

app = graph.compile()

# 测试不同查询
tech_result = app.invoke({"query": "Python怎么使用?"})
print(tech_result["response"])  # 技术问题已处理

general_result = app.invoke({"query": "你好吗?"})
print(general_result["response"])  # 一般问题已处理
```

### 🔍 Level 3: 对比学习（避免陷阱）

```python
# ❌ 错误用法：直接修改状态（函数式编程原则）
def bad_node(state: dict):
    state["modified"] = True  # 直接修改原状态
    return state

# ✅ 正确用法：返回状态更新
def good_node(state: dict):
    return {"modified": True}  # 返回更新部分

# 验证正确用法
from langgraph.graph import StateGraph

class TestState(TypedDict):
    value: str
    modified: bool

graph = StateGraph(TestState)
graph.add_node("test", good_node)
graph.set_entry_point("test")
graph.set_finish_point("test")
app = graph.compile()

result = app.invoke({"value": "test", "modified": False})
print(result)  # {'value': 'test', 'modified': True}
```

### 🚀 Level 4: 实战应用（真实场景）
多轮问答自我修正系统：

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
from typing_extensions import Literal

class QAState(TypedDict):
    question: str
    answer: str
    attempts: Annotated[int, "尝试次数"]
    status: Annotated[Literal["pending", "satisfied", "retry"], "回答状态"]

def generate_answer(state: QAState):
    # 模拟答案生成
    attempts = state.get("attempts", 0) + 1
    if attempts == 1:
        return {"answer": "初步答案（可能需要改进）", "attempts": attempts}
    return {"answer": "改进后的最终答案", "attempts": attempts}

def evaluate_answer(state: QAState):
    # 模拟答案评估
    if "改进" in state["answer"]:
        return {"status": "satisfied"}
    return {"status": "retry"}

def should_retry(state: QAState):
    if state["status"] == "satisfied" or state.get("attempts", 0) >= 3:
        return "end"
    return "retry"

graph = StateGraph(QAState)
graph.add_node("generate", generate_answer)
graph.add_node("evaluate", evaluate_answer)

graph.set_entry_point("generate")
graph.add_edge("generate", "evaluate")
graph.add_conditional_edges("evaluate", should_retry, {
    "retry": "generate",
    "end": END
})

app = graph.compile()

# 运行多轮问答
result = app.invoke({
    "question": "如何学习LangGraph?",
    "attempts": 0,
    "status": "pending"
})

print(f"最终答案: {result['answer']}")
print(f"尝试次数: {result['attempts']}")
```

### 💡 记忆要点
- LangGraph 的核心是状态管理和流程控制
- 使用函数式编程范式，通过返回字典来更新状态
- 支持条件分支和循环，适合复杂工作流
- 每个节点都是独立的工作单元，易于测试和维护
```