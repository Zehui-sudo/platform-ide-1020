```markdown
## 共享状态设计：Agent之间的信息流

### 🎯 核心概念
共享状态设计解决了多Agent系统中信息隔离和传递的问题，通过统一的State对象让不同Agent能够安全地读写共享数据，是实现复杂协作流程的关键架构模式。

### 💡 使用方式
核心是通过定义统一的State类，使用`add_messages`字段记录对话历史，自定义字段存储共享数据：

```python
from typing import Annotated, List
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[List, add_messages]
    shared_data: str  # 自定义共享字段
```

### 📚 Level 1: 基础认知（30秒理解）
最简单的两个Agent通过共享状态传递信息：

```python
from typing import Annotated, List
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage

# 定义共享状态
class State(TypedDict):
    messages: Annotated[List, add_messages]
    processed_data: str

# 第一个Agent：处理输入
def agent1(state: State):
    user_input = state["messages"][-1].content
    return {"processed_data": f"Processed: {user_input.upper()}"}

# 第二个Agent：使用处理结果
def agent2(state: State):
    return {"messages": [HumanMessage(content=f"Result: {state['processed_data']}")]}

# 构建图
builder = StateGraph(State)
builder.add_node("agent1", agent1)
builder.add_node("agent2", agent2)
builder.add_edge("agent1", "agent2")
builder.add_edge("agent2", END)

graph = builder.compile()

# 执行
result = graph.invoke({"messages": [HumanMessage(content="hello world")]})
print(result["messages"][-1].content)  # 输出: Result: Processed: HELLO WORLD
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 状态隔离与安全访问
```python
from typing import Annotated, List
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage

class State(TypedDict):
    messages: Annotated[List, add_messages]
    research_data: dict
    analysis_result: str

# 研究Agent：收集数据
def research_agent(state: State):
    query = state["messages"][-1].content
    return {"research_data": {"source": "web", "findings": f"Data about {query}"}}

# 分析Agent：使用研究数据
def analysis_agent(state: State):
    findings = state["research_data"]["findings"]
    return {"analysis_result": f"Analysis: {findings} is very important"}

# 报告Agent：综合所有信息
def report_agent(state: State):
    analysis = state["analysis_result"]
    return {"messages": [HumanMessage(content=f"Final Report: {analysis}")]}

builder = StateGraph(State)
builder.add_node("research", research_agent)
builder.add_node("analysis", analysis_agent)
builder.add_node("report", report_agent)

builder.add_edge("research", "analysis")
builder.add_edge("analysis", "report")
builder.add_edge("report", END)

graph = builder.compile()

result = graph.invoke({"messages": [HumanMessage(content="AI technology")]})
print(result["messages"][-1].content)
```

#### 特性2: 状态更新与合并
```python
from typing import Annotated, List
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[List, add_messages]
    task_status: dict
    results: list

def task_planner(state: State):
    return {"task_status": {"stage": "planning", "tasks": ["task1", "task2"]}}

def task_executor(state: State):
    current_tasks = state["task_status"]["tasks"]
    return {
        "results": [f"Completed {task}" for task in current_tasks],
        "task_status": {"stage": "executing", "progress": "50%"}
    }

def status_updater(state: State):
    return {
        "task_status": {"stage": "completed", "progress": "100%"},
        "messages": [HumanMessage(content=f"Results: {state['results']}")]
    }

builder = StateGraph(State)
builder.add_node("plan", task_planner)
builder.add_node("execute", task_executor)
builder.add_node("update", status_updater)

builder.add_edge("plan", "execute")
builder.add_edge("execute", "update")
builder.add_edge("update", END)

graph = builder.compile()
result = graph.invoke({"messages": []})
print(result["task_status"])  # 显示最终状态
```

### 🔍 Level 3: 对比学习（避免陷阱）

```python
# 错误用法：直接修改状态（可能导致竞态条件）
def bad_agent(state: State):
    # 错误：直接修改原状态
    state["shared_data"] += " new data"
    return {}

# 正确用法：返回更新字典（线程安全）
def good_agent(state: State):
    # 正确：返回更新部分
    return {"shared_data": state["shared_data"] + " new data"}

# 错误用法：假设状态顺序
def assuming_agent(state: State):
    # 错误：假设其他Agent已执行
    if "processed" not in state:
        raise ValueError("Dependent data missing")
    
# 正确用法：使用默认值或检查
def safe_agent(state: State):
    # 正确：处理可能缺失的数据
    data = state.get("processed", "default_value")
    return {"result": f"Using: {data}"}
```

### 🚀 Level 4: 实战应用（真实场景）
构建一个多Agent会议记录处理系统：

```python
from typing import Annotated, List
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage

class State(TypedDict):
    messages: Annotated[List, add_messages]
    raw_transcript: str
    summarized_points: list
    action_items: list
    final_report: str

def transcript_processor(state: State):
    raw_text = state["messages"][-1].content
    return {"raw_transcript": raw_text}

def summary_agent(state: State):
    transcript = state["raw_transcript"]
    # 模拟摘要生成
    return {"summarized_points": [
        "讨论项目时间线",
        "确定资源分配",
        "安排下周会议"
    ]}

def action_extractor(state: State):
    points = state["summarized_points"]
    return {"action_items": [
        f"跟进: {point}" for point in points
    ]}

def report_generator(state: State):
    summary = state["summarized_points"]
    actions = state["action_items"]
    report = f"会议摘要: {summary}\n待办事项: {actions}"
    return {"final_report": report, "messages": [HumanMessage(content=report)]}

# 构建工作流
builder = StateGraph(State)
builder.add_node("process_transcript", transcript_processor)
builder.add_node("generate_summary", summary_agent)
builder.add_node("extract_actions", action_extractor)
builder.add_node("generate_report", report_generator)

builder.add_edge("process_transcript", "generate_summary")
builder.add_edge("generate_summary", "extract_actions")
builder.add_edge("extract_actions", "generate_report")
builder.add_edge("generate_report", END)

graph = builder.compile()

# 模拟会议记录输入
meeting_text = """
今天会议讨论了项目进展，决定延长截止日期到月底。
需要分配更多开发资源，并安排下周再次开会检查进度。
"""

result = graph.invoke({
    "messages": [HumanMessage(content=meeting_text)]
})

print("最终报告:")
print(result["final_report"])
print("\n共享状态内容:")
print(f"原始记录: {result['raw_transcript'][:50]}...")
print(f"摘要要点: {result['summarized_points']}")
print(f"行动项: {result['action_items']}")
```

### 💡 记忆要点
- 使用TypedDict定义明确的State结构，确保类型安全
- 通过返回字典更新状态，避免直接修改原状态
- 合理设计状态字段的粒度，平衡灵活性和复杂性
- 考虑Agent执行顺序对状态依赖的影响
- 使用get()方法安全访问可能未初始化的状态字段
```