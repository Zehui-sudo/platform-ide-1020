```markdown
## Supervisor模式：构建Agent团队大脑

### 🎯 核心概念
Supervisor模式通过一个中央协调器（Supervisor Agent）来管理和调度多个专家Agent，解决复杂任务的分解、分配和结果整合问题。它是构建复杂多Agent系统的关键架构，能够实现1+1>2的协同效应。

### 💡 使用方式
核心API包括：
- `StateGraph`: 定义工作流状态
- `add_node`: 添加Agent节点  
- `add_conditional_edges`: 添加条件路由
- `set_entry_point`: 设置入口节点

### 📚 Level 1: 基础认知（30秒理解）
最简单的Supervisor模式示例：一个主管协调两个专家Agent

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal
import operator

# 定义状态结构
class AgentState(TypedDict):
    task: str
    agent_type: Literal["writer", "reviewer", "supervisor"]
    result: str

# 定义专家Agent节点
def writer_node(state: AgentState):
    return {"result": f"Written content for: {state['task']}"}

def reviewer_node(state: AgentState):
    return {"result": f"Reviewed: {state['result']}"}

# 主管Agent的路由逻辑
def supervisor_router(state: AgentState):
    if "draft" in state["task"].lower():
        return "writer"
    elif "review" in state["task"].lower():
        return "reviewer"
    return "supervisor"

# 构建工作流
builder = StateGraph(AgentState)
builder.add_node("writer", writer_node)
builder.add_node("reviewer", reviewer_node)
builder.add_node("supervisor", lambda state: {"result": "Task completed"})

builder.set_entry_point("supervisor")
builder.add_conditional_edges("supervisor", supervisor_router)
builder.add_edge("writer", "supervisor")
builder.add_edge("reviewer", "supervisor")

graph = builder.compile()

# 运行示例
result = graph.invoke({"task": "draft a report", "agent_type": "supervisor"})
print(result["result"])
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 动态任务分发
Supervisor根据任务内容动态选择最合适的专家Agent

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal
import operator

class AgentState(TypedDict):
    task: str
    agent_type: Literal["coder", "analyst", "writer", "supervisor"]
    result: str

def coder_agent(state: AgentState):
    return {"result": f"Code solution for: {state['task']}"}

def analyst_agent(state: AgentState):
    return {"result": f"Analysis report: {state['task']}"}

def writer_agent(state: AgentState):
    return {"result": f"Written document: {state['task']}"}

def smart_supervisor(state: AgentState):
    task = state["task"].lower()
    
    if any(keyword in task for keyword in ["code", "program", "algorithm"]):
        return {"agent_type": "coder"}
    elif any(keyword in task for keyword in ["analyze", "data", "statistics"]):
        return {"agent_type": "analyst"}
    elif any(keyword in task for keyword in ["write", "document", "report"]):
        return {"agent_type": "writer"}
    else:
        return {"result": "No suitable agent found"}

def supervisor_router(state: AgentState):
    return state["agent_type"]

builder = StateGraph(AgentState)
builder.add_node("coder", coder_agent)
builder.add_node("analyst", analyst_agent)
builder.add_node("writer", writer_agent)
builder.add_node("supervisor", smart_supervisor)

builder.set_entry_point("supervisor")
builder.add_conditional_edges("supervisor", supervisor_router)
builder.add_edge("coder", END)
builder.add_edge("analyst", END)
builder.add_edge("writer", END)

graph = builder.compile()

# 测试不同任务
tasks = [
    "write a technical document",
    "analyze sales data",
    "code a sorting algorithm"
]

for task in tasks:
    result = graph.invoke({"task": task, "agent_type": "supervisor"})
    print(f"Task: {task} -> {result['result']}")
```

#### 特性2: 结果汇总与质量控制
Supervisor对专家Agent的结果进行质量检查和整合

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal

class QualityState(TypedDict):
    task: str
    agent_type: Literal["worker", "supervisor", "quality_checker"]
    result: str
    quality_score: int

def worker_agent(state: QualityState):
    return {"result": f"Completed: {state['task']}", "quality_score": 85}

def quality_checker(state: QualityState):
    score = state["quality_score"]
    if score >= 90:
        return {"result": f"✅ Quality approved: {state['result']}"}
    elif score >= 70:
        return {"result": f"⚠️ Needs improvement: {state['result']}"}
    else:
        return {"result": f"❌ Rejected: {state['result']}"}

def supervisor_agent(state: QualityState):
    return {"agent_type": "worker"}

builder = StateGraph(QualityState)
builder.add_node("worker", worker_agent)
builder.add_node("quality_checker", quality_checker)
builder.add_node("supervisor", supervisor_agent)

builder.set_entry_point("supervisor")
builder.add_edge("supervisor", "worker")
builder.add_edge("worker", "quality_checker")
builder.add_edge("quality_checker", END)

graph = builder.compile()

# 运行质量检查流程
result = graph.invoke({
    "task": "produce product design",
    "agent_type": "supervisor",
    "quality_score": 0
})
print(result["result"])
```

### 🔍 Level 3: 对比学习（避免陷阱）

```python
# ❌ 错误用法：直接硬编码路由，缺乏灵活性
def bad_router(state):
    if state["task"] == "task_a":  # 硬编码特定任务
        return "agent_a"
    return "agent_b"

# ✅ 正确用法：基于语义的路由，支持未知任务
def good_router(state):
    task = state["task"].lower()
    
    # 基于关键词智能路由
    if "analysis" in task or "data" in task:
        return "analyst_agent"
    elif "code" in task or "program" in task:
        return "coder_agent"
    elif "write" in task or "document" in task:
        return "writer_agent"
    else:
        # 默认处理未知任务
        return "general_agent"
```

### 🚀 Level 4: 实战应用（真实场景）
构建一个完整的内容创作团队：主管协调写手、编辑和发布专家

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal
from datetime import datetime

class ContentTeamState(TypedDict):
    topic: str
    agent_type: Literal["writer", "editor", "publisher", "supervisor"]
    content: str
    status: str
    timestamp: str

def writer_agent(state: ContentTeamState):
    return {
        "content": f"初稿文章：{state['topic']}\n这是关于{state['topic']}的详细内容...",
        "status": "draft_created"
    }

def editor_agent(state: ContentTeamState):
    edited_content = state["content"].replace("初稿", "编辑后的").replace("详细内容", "优化内容")
    return {
        "content": edited_content,
        "status": "edited"
    }

def publisher_agent(state: ContentTeamState):
    return {
        "content": f"📢 已发布：{state['content']}",
        "status": "published",
        "timestamp": datetime.now().isoformat()
    }

def content_supervisor(state: ContentTeamState):
    if state["status"] == "start":
        return {"agent_type": "writer"}
    elif state["status"] == "draft_created":
        return {"agent_type": "editor"}
    elif state["status"] == "edited":
        return {"agent_type": "publisher"}
    return {"agent_type": "supervisor"}

def supervisor_router(state: ContentTeamState):
    return state["agent_type"]

# 构建内容团队工作流
builder = StateGraph(ContentTeamState)
builder.add_node("writer", writer_agent)
builder.add_node("editor", editor_agent)
builder.add_node("publisher", publisher_agent)
builder.add_node("supervisor", content_supervisor)

builder.set_entry_point("supervisor")
builder.add_conditional_edges("supervisor", supervisor_router)
builder.add_edge("writer", "supervisor")
builder.add_edge("editor", "supervisor")
builder.add_edge("publisher", END)

content_graph = builder.compile()

# 运行完整的内容创作流程
final_result = content_graph.invoke({
    "topic": "人工智能发展趋势",
    "agent_type": "supervisor",
    "status": "start",
    "content": "",
    "timestamp": ""
})

print("最终结果:")
print(f"状态: {final_result['status']}")
print(f"内容: {final_result['content']}")
print(f"时间: {final_result['timestamp']}")
```

### 💡 记忆要点
- Supervisor模式的核心是中央协调器管理多个专家Agent
- 使用条件路由实现智能的任务分发
- 状态管理是多个Agent间信息传递的关键
- 支持动态的工作流调整和错误处理
- 适合复杂任务分解和结果整合场景
```