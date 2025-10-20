```markdown
# 运行完整的多Agent协作流程

### 🎯 核心概念
运行完整的多Agent协作流程是构建复杂AI系统的关键，它解决了单个Agent能力有限的问题，通过多个专业化Agent的协同工作，能够处理更复杂的任务并产生更优质的结果。

### 💡 使用方式
核心API是`app.stream()`或`app.invoke()`，用于执行构建好的多Agent图。通过定义清晰的状态流转规则和Agent分工，实现高效的协作流程。

### 📚 Level 1: 基础认知（30秒理解）
一个最简单的多Agent协作流程，包含研究员和写作员两个Agent的协同工作。

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict
from langchain_openai import ChatOpenAI

# 定义共享状态
class ResearchState(TypedDict):
    topic: str
    research_data: str
    final_report: str

# 初始化模型
llm = ChatOpenAI(model="gpt-3.5-turbo")

# 定义研究员Agent
def research_agent(state: ResearchState):
    prompt = f"请研究以下主题并提供详细资料: {state['topic']}"
    response = llm.invoke(prompt)
    return {"research_data": response.content}

# 定义写作员Agent
def writer_agent(state: ResearchState):
    prompt = f"根据以下研究资料撰写报告:\n{state['research_data']}\n\n主题: {state['topic']}"
    response = llm.invoke(prompt)
    return {"final_report": response.content}

# 构建图
builder = StateGraph(ResearchState)
builder.add_node("researcher", research_agent)
builder.add_node("writer", writer_agent)

# 设置流程
builder.set_entry_point("researcher")
builder.add_edge("researcher", "writer")
builder.add_edge("writer", END)

# 编译图
app = builder.compile()

# 运行完整流程
result = app.invoke({"topic": "人工智能在医疗领域的应用"})
print("最终报告:", result["final_report"])
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 条件路由与动态决策
实现基于内容质量的条件路由，让Supervisor Agent决定是否需要进一步研究。

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal
from langchain_openai import ChatOpenAI
import json

class ResearchState(TypedDict):
    topic: str
    research_data: str
    final_report: str
    quality_check: Literal["pass", "need_more_research"]

llm = ChatOpenAI(model="gpt-3.5-turbo")

def research_agent(state: ResearchState):
    prompt = f"深入研究: {state['topic']}"
    response = llm.invoke(prompt)
    return {"research_data": response.content}

def writer_agent(state: ResearchState):
    prompt = f"撰写报告: {state['research_data']}"
    response = llm.invoke(prompt)
    return {"final_report": response.content}

def quality_checker(state: ResearchState):
    prompt = f"""评估以下研究资料的质量，如果资料充分且相关返回pass，否则返回need_more_research:
    
    主题: {state['topic']}
    研究资料: {state['research_data']}
    
    只返回JSON: {{"decision": "pass"}} 或 {{"decision": "need_more_research"}}"""
    
    response = llm.invoke(prompt)
    decision = json.loads(response.content)["decision"]
    return {"quality_check": decision}

def should_continue(state: ResearchState):
    if state["quality_check"] == "pass":
        return "writer"
    return "researcher"

# 构建图
builder = StateGraph(ResearchState)
builder.add_node("researcher", research_agent)
builder.add_node("quality_check", quality_checker)
builder.add_node("writer", writer_agent)

builder.set_entry_point("researcher")
builder.add_edge("researcher", "quality_check")
builder.add_conditional_edges("quality_check", should_continue, ["researcher", "writer"])
builder.add_edge("writer", END)

app = builder.compile()

# 运行带条件检查的流程
result = app.invoke({"topic": "量子计算的最新进展"})
print("最终报告:", result["final_report"])
```

### 🔍 Level 3: 对比学习（避免陷阱）

#### 状态共享的正确方式
错误方式：直接修改全局状态；正确方式：通过返回字典更新状态

```python
# 错误用法：直接修改传入的状态对象
def bad_research_agent(state: ResearchState):
    # 错误：直接修改传入的状态
    state["research_data"] = "一些数据"  # 这不会正确更新状态
    return state

# 正确用法：返回要更新的字段字典
def good_research_agent(state: ResearchState):
    # 正确：返回要更新的字段
    return {"research_data": "一些数据"}
```

### 🚀 Level 4: 实战应用（真实场景）
构建一个完整的研究团队，包含领域专家、数据分析师和报告撰写员。

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict
from langchain_openai import ChatOpenAI
import asyncio

class ResearchTeamState(TypedDict):
    topic: str
    expert_analysis: str
    data_analysis: str
    final_report: str

llm = ChatOpenAI(model="gpt-3.5-turbo")

async def expert_analyst(state: ResearchTeamState):
    prompt = f"作为领域专家，请分析: {state['topic']}"
    response = await llm.ainvoke(prompt)
    return {"expert_analysis": response.content}

async def data_analyst(state: ResearchTeamState):
    prompt = f"作为数据分析师，请提供数据视角: {state['topic']}"
    response = await llm.ainvoke(prompt)
    return {"data_analysis": response.content}

async def report_writer(state: ResearchTeamState):
    prompt = f"""综合以下信息撰写专业报告:
    
    专家分析: {state['expert_analysis']}
    数据分析: {state['data_analysis']}
    
    主题: {state['topic']}"""
    
    response = await llm.ainvoke(prompt)
    return {"final_report": response.content}

# 构建并行执行的研究团队
builder = StateGraph(ResearchTeamState)

# 添加并行执行的专家节点
builder.add_node("expert", expert_analyst)
builder.add_node("analyst", data_analyst)
builder.add_node("writer", report_writer)

# 设置并行执行路径
builder.set_entry_point("expert")
builder.set_entry_point("analyst")

# 等待两个专家完成后再进入写作阶段
builder.add_edge("expert", "writer")
builder.add_edge("analyst", "writer")
builder.add_edge("writer", END)

app = builder.compile()

# 运行完整的研究团队
async def run_research_team():
    result = await app.ainvoke({"topic": "可再生能源的未来发展趋势"})
    print("研究团队最终报告:")
    print(result["final_report"])

# 执行异步任务
asyncio.run(run_research_team())
```

### 💡 记忆要点
- 多Agent协作通过专业化分工提升整体任务处理能力
- 状态管理是Agent间通信的关键，必须通过返回字典正确更新
- 条件路由允许根据中间结果动态调整工作流程
- 并行执行可以显著提高多Agent系统的效率
- 清晰的Agent角色定义和接口设计是成功协作的基础
```