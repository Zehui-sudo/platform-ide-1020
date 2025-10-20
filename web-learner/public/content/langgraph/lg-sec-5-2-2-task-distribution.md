```markdown
# 实现任务分发与结果汇总

## 🎯 核心概念
任务分发与结果汇总是多智能体协作的核心机制，它解决了如何将复杂任务拆解分配给不同专业Agent，并有效整合各Agent工作成果的问题，是构建可扩展Agent系统的关键。

## 💡 使用方式
在LangGraph中，通过`StateGraph`的状态共享机制和条件边实现任务分发，使用聚合节点进行结果汇总。核心API包括：
- `add_node()` 添加工作节点
- `add_conditional_edges()` 实现动态路由
- 共享State实现数据传递

## 📚 Level 1: 基础认知（30秒理解）
最简单的任务分发与汇总实现，包含两个工作Agent和一个汇总节点：

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Annotated
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
import operator

# 定义状态
class ResearchState(TypedDict):
    tasks: List[str]
    results: Annotated[List[str], operator.add]
    final_report: str

# 初始化LLM
llm = ChatOpenAI(model="gpt-3.5-turbo")

# 定义工作节点
def research_agent(state: ResearchState):
    task = state["tasks"].pop(0)
    response = llm.invoke([
        HumanMessage(content=f"请研究以下任务：{task}，提供详细分析")
    ])
    return {"results": [response.content]}

def writer_agent(state: ResearchState):
    task = state["tasks"].pop(0)
    response = llm.invoke([
        HumanMessage(content=f"请撰写关于 {task} 的详细报告")
    ])
    return {"results": [response.content]}

# 定义汇总节点
def summarizer_agent(state: ResearchState):
    all_results = "\n".join(state["results"])
    response = llm.invoke([
        HumanMessage(content=f"基于以下研究结果生成最终报告：\n{all_results}")
    ])
    return {"final_report": response.content}

# 构建图
builder = StateGraph(ResearchState)

# 添加节点
builder.add_node("researcher", research_agent)
builder.add_node("writer", writer_agent)
builder.add_node("summarizer", summarizer_agent)

# 设置入口点
builder.set_entry_point("researcher")

# 添加边
builder.add_edge("researcher", "writer")
builder.add_edge("writer", "summarizer")
builder.add_edge("summarizer", END)

# 编译图
graph = builder.compile()

# 运行
result = graph.invoke({
    "tasks": ["人工智能发展趋势", "机器学习最新进展"],
    "results": [],
    "final_report": ""
})

print("最终报告:", result["final_report"])
```

## 📈 Level 2: 核心特性（深入理解）

### 特性1: 动态任务分发
根据任务类型自动路由到不同的专业Agent：

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Annotated, Literal
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
import operator

class ResearchState(TypedDict):
    tasks: List[str]
    results: Annotated[List[str], operator.add]
    final_report: str
    current_task: str

llm = ChatOpenAI(model="gpt-3.5-turbo")

def task_router(state: ResearchState) -> Literal["tech_researcher", "business_analyst", "summarizer"]:
    task = state["tasks"][0] if state["tasks"] else ""
    
    if "技术" in task or "AI" in task or "算法" in task:
        return "tech_researcher"
    elif "市场" in task or "商业" in task or "经济" in task:
        return "business_analyst"
    else:
        return "summarizer"

def tech_researcher(state: ResearchState):
    task = state["tasks"].pop(0)
    response = llm.invoke([
        HumanMessage(content=f"作为技术研究员，请分析：{task}")
    ])
    return {"results": [f"技术分析: {response.content}"]}

def business_analyst(state: ResearchState):
    task = state["tasks"].pop(0)
    response = llm.invoke([
        HumanMessage(content=f"作为商业分析师，请分析：{task}")
    ])
    return {"results": [f"商业分析: {response.content}"]}

def summarizer_agent(state: ResearchState):
    if not state["tasks"]:
        all_results = "\n".join(state["results"])
        response = llm.invoke([
            HumanMessage(content=f"整合所有分析结果：\n{all_results}")
        ])
        return {"final_report": response.content}
    return {}

builder = StateGraph(ResearchState)

builder.add_node("router", lambda state: state)  # 路由节点
builder.add_node("tech_researcher", tech_researcher)
builder.add_node("business_analyst", business_analyst)
builder.add_node("summarizer", summarizer_agent)

builder.set_entry_point("router")

# 条件边实现动态路由
builder.add_conditional_edges(
    "router",
    task_router,
    {
        "tech_researcher": "tech_researcher",
        "business_analyst": "business_analyst",
        "summarizer": "summarizer"
    }
)

builder.add_edge("tech_researcher", "router")
builder.add_edge("business_analyst", "router")
builder.add_conditional_edges("summarizer", lambda state: END if state["final_report"] else "router")

graph = builder.compile()

# 执行
result = graph.invoke({
    "tasks": ["AI技术发展趋势", "机器学习市场分析", "人工智能经济影响"],
    "results": [],
    "final_report": "",
    "current_task": ""
})

print("整合报告:", result["final_report"])
```

## 🔍 Level 3: 对比学习（避免陷阱）

### 错误用法 vs 正确用法

```python
# ❌ 错误用法：状态管理混乱
def bad_researcher(state: ResearchState):
    # 直接修改原始任务列表，可能导致状态不一致
    task = state["tasks"].pop(0)
    # 没有返回完整的状态更新
    return {"result": f"分析: {task}"}

# ✅ 正确用法：纯净的状态处理
def good_researcher(state: ResearchState):
    # 创建任务副本进行处理
    remaining_tasks = state["tasks"][1:]
    current_task = state["tasks"][0]
    
    response = llm.invoke([
        HumanMessage(content=f"分析任务: {current_task}")
    ])
    
    # 返回完整的状态更新
    return {
        "tasks": remaining_tasks,
        "results": [response.content]
    }
```

## 🚀 Level 4: 实战应用（真实场景）
构建完整的研究团队，包含任务拆分、专业分配、质量检查和最终汇总：

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Annotated, Literal
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import operator

class ResearchState(TypedDict):
    main_task: str
    subtasks: List[str]
    research_results: Annotated[List[str], operator.add]
    quality_checked: bool
    final_report: str

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)

def task_decomposer(state: ResearchState):
    """将主任务拆分为子任务"""
    response = llm.invoke([
        SystemMessage(content="你是一个任务分解专家，请将复杂任务拆分为3-5个子任务"),
        HumanMessage(content=f"请将以下任务拆分为子任务：{state['main_task']}")
    ])
    return {"subtasks": response.content.split("\n")}

def research_agent(state: ResearchState):
    """研究Agent处理子任务"""
    if not state["subtasks"]:
        return {"subtasks": []}
    
    task = state["subtasks"].pop(0)
    response = llm.invoke([
        SystemMessage(content="你是专业研究员，提供详细的技术分析"),
        HumanMessage(content=f"请深入研究：{task}")
    ])
    return {
        "subtasks": state["subtasks"],
        "research_results": [f"## {task}\n{response.content}"]
    }

def quality_checker(state: ResearchState):
    """质量检查节点"""
    if not state["research_results"]:
        return {"quality_checked": False}
    
    latest_result = state["research_results"][-1]
    response = llm.invoke([
        SystemMessage(content="你是质量检查专家，评估研究内容的完整性和准确性"),
        HumanMessage(content=f"请检查以下研究质量：\n{latest_result}")
    ])
    return {"quality_checked": "通过" in response.content}

def report_generator(state: ResearchState):
    """最终报告生成"""
    all_results = "\n\n".join(state["research_results"])
    response = llm.invoke([
        SystemMessage(content="你是高级报告撰写专家，生成结构化的专业报告"),
        HumanMessage(content=f"基于以下研究结果生成最终报告：\n{all_results}")
    ])
    return {"final_report": response.content}

def router(state: ResearchState) -> Literal["research", "quality_check", "generate_report", "end"]:
    """智能路由"""
    if not state.get("subtasks"):
        return "research"
    elif state["subtasks"] and not state.get("quality_checked", False):
        return "quality_check"
    elif not state["subtasks"] and state.get("quality_checked", False):
        return "generate_report"
    else:
        return "end"

# 构建图
builder = StateGraph(ResearchState)

builder.add_node("decomposer", task_decomposer)
builder.add_node("researcher", research_agent)
builder.add_node("quality_checker", quality_checker)
builder.add_node("report_generator", report_generator)

builder.set_entry_point("decomposer")

builder.add_conditional_edges(
    "decomposer",
    lambda state: "researcher",
    {"researcher": "researcher"}
)

builder.add_conditional_edges(
    "researcher",
    router,
    {
        "research": "researcher",
        "quality_check": "quality_checker",
        "generate_report": "report_generator",
        "end": END
    }
)

builder.add_conditional_edges(
    "quality_checker",
    lambda state: "researcher" if not state["quality_checked"] else "researcher",
    {"researcher": "researcher"}
)

builder.add_edge("report_generator", END)

graph = builder.compile()

# 执行完整流程
result = graph.invoke({
    "main_task": "人工智能对未来就业市场的影响",
    "subtasks": [],
    "research_results": [],
    "quality_checked": False,
    "final_report": ""
})

print("=" * 50)
print("最终研究报告:")
print("=" * 50)
print(result["final_report"])
```

## 💡 记忆要点
- 状态设计是关键：合理设计State结构确保数据流清晰
- 节点职责单一：每个节点只负责一个明确的任务
- 错误处理重要：确保任务失败时有适当的恢复机制
- 结果聚合策略：设计有效的结果汇总和冲突解决机制
```