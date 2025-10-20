```markdown
## 案例: 多轮问答或自我修正

### 🎯 核心概念
多轮问答和自修正机制让 Agent 能够处理复杂查询，通过循环迭代逐步完善答案或请求更多信息，这是构建智能对话系统的关键能力。

### 💡 使用方式
通过 `add_conditional_edges()` 和循环边实现多轮交互，使用状态管理追踪对话历史。

### 📚 Level 1: 基础认知（30秒理解）
一个简单的多轮问答系统，能够根据用户输入决定是否需要更多信息。

```python
from typing import Literal, TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

# 定义状态
class AgentState(TypedDict):
    question: str
    history: list[str]
    response: str
    need_clarification: bool

# 初始化模型
llm = ChatOpenAI(model="gpt-3.5-turbo")

# 定义问答节点
def answer_node(state: AgentState):
    history_str = "\n".join(state["history"])
    prompt = f"""基于对话历史回答问题：
{history_str}
当前问题: {state['question']}

请给出专业回答。如果问题不够明确需要澄清，请说明需要什么额外信息。"""
    
    response = llm.invoke(prompt)
    need_clarification = "需要更多信息" in response.content or "不够明确" in response.content
    
    return {
        "response": response.content,
        "need_clarification": need_clarification,
        "history": state["history"] + [f"用户: {state['question']}", f"助手: {response.content}"]
    }

# 定义路由逻辑
def route_question(state: AgentState):
    if state["need_clarification"]:
        return "clarify"
    return "end"

# 构建图
builder = StateGraph(AgentState)
builder.add_node("answer", answer_node)
builder.set_entry_point("answer")
builder.add_conditional_edges(
    "answer",
    route_question,
    {"clarify": "answer", "end": END}
)

graph = builder.compile()

# 运行示例
result = graph.invoke({
    "question": "请解释量子计算",
    "history": [],
    "response": "",
    "need_clarification": False
})
print(result["response"])
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 自我修正机制
Agent 能够检测回答质量并自动修正不完善的回答。

```python
from typing import Literal, TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
import re

class RefinementState(TypedDict):
    question: str
    draft_answer: str
    final_answer: str
    refinement_count: int

llm = ChatOpenAI(model="gpt-3.5-turbo")

def generate_draft(state: RefinementState):
    prompt = f"请回答以下问题：{state['question']}"
    response = llm.invoke(prompt)
    return {"draft_answer": response.content}

def refine_answer(state: RefinementState):
    critique_prompt = f"""请批判性评估以下回答的质量：
问题: {state['question']}
回答: {state['draft_answer']}

指出回答中的不足或需要改进的地方。"""
    
    critique = llm.invoke(critique_prompt)
    
    refinement_prompt = f"""基于以下批评改进回答：
原始问题: {state['question']}
原始回答: {state['draft_answer']}
批评意见: {critique.content}

请提供改进后的回答。"""
    
    refined = llm.invoke(refinement_prompt)
    
    return {
        "draft_answer": refined.content,
        "refinement_count": state["refinement_count"] + 1
    }

def should_continue(state: RefinementState):
    if state["refinement_count"] >= 2:  # 最多修正2次
        return "end"
    
    quality_check = f"""评估以下回答的完整性和准确性：
问题: {state['question']}
回答: {state['draft_answer']}

如果回答已经完整准确，回复'EXCELLENT'，否则回复'NEEDS_IMPROVEMENT'。"""
    
    assessment = llm.invoke(quality_check)
    if "EXCELLENT" in assessment.content:
        return "end"
    return "refine"

builder = StateGraph(RefinementState)
builder.add_node("draft", generate_draft)
builder.add_node("refine", refine_answer)
builder.set_entry_point("draft")
builder.add_conditional_edges("draft", should_continue, 
                             {"refine": "refine", "end": END})
builder.add_conditional_edges("refine", should_continue,
                             {"refine": "refine", "end": END})

refinement_graph = builder.compile()

# 测试自我修正
result = refinement_graph.invoke({
    "question": "请详细解释Transformer架构在自然语言处理中的应用",
    "draft_answer": "",
    "final_answer": "",
    "refinement_count": 0
})
print(f"最终回答（经过{result['refinement_count']}次修正）：")
print(result['draft_answer'])
```

### 🔍 Level 3: 对比学习（避免陷阱）

```python
# 错误用法：缺少终止条件的无限循环
def faulty_router(state):
    return "always_loop"  # 总是返回循环，导致无限循环

# 正确用法：确保有终止条件
def proper_router(state):
    if state["iteration_count"] > 5:  # 设置最大迭代次数
        return "end"
    if "答案完整" in state["assessment"]:
        return "end"
    return "continue_loop"
```

### 🚀 Level 4: 实战应用（真实场景）
构建一个智能研究助手，能够进行多轮问答并自我修正。

```python
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
import asyncio

class ResearchState(TypedDict):
    research_topic: str
    conversation_history: list
    current_query: str
    current_response: str
    research_depth: int
    needs_more_info: bool

llm = ChatOpenAI(model="gpt-3.5-turbo")

def research_agent(state: ResearchState):
    history = "\n".join(state["conversation_history"][-5:])  # 最近5轮对话
    
    prompt = f"""作为研究助手，请帮助用户深入研究主题：{state['research_topic']}

对话历史：
{history}

当前查询：{state['current_query']}

请提供详细的研究性回答。如果需要更多上下文信息，请明确询问。"""
    
    response = llm.invoke(prompt)
    needs_info = any(phrase in response.content.lower() 
                    for phrase in ["请问", "需要更多", "能否提供"])
    
    return {
        "current_response": response.content,
        "needs_more_info": needs_info,
        "conversation_history": state["conversation_history"] + [
            f"用户: {state['current_query']}",
            f"助手: {response.content}"
        ],
        "research_depth": state["research_depth"] + 1
    }

def research_router(state: ResearchState):
    if state["needs_more_info"] and state["research_depth"] < 5:
        return "continue_research"
    if state["research_depth"] >= 5:
        return "end"
    return "end"

def user_simulator(state: ResearchState):
    # 模拟用户提供更多信息
    follow_up = f"关于{state['research_topic']}，我想了解更多细节"
    return {"current_query": follow_up}

# 构建研究助手图
builder = StateGraph(ResearchState)
builder.add_node("research", research_agent)
builder.add_node("get_user_input", user_simulator)
builder.set_entry_point("research")

builder.add_conditional_edges(
    "research",
    research_router,
    {"continue_research": "get_user_input", "end": END}
)
builder.add_edge("get_user_input", "research")

research_graph = builder.compile()

# 运行研究助手
async def run_research_assistant():
    result = await research_graph.ainvoke({
        "research_topic": "人工智能伦理",
        "conversation_history": [],
        "current_query": "请介绍AI伦理的主要原则",
        "current_response": "",
        "research_depth": 0,
        "needs_more_info": False
    })
    
    print("研究完成！对话轮数:", result["research_depth"])
    print("最终回答:", result["current_response"])

# asyncio.run(run_research_assistant())
```

### 💡 记忆要点
- 循环机制通过 `add_conditional_edges()` 实现，必须包含明确的终止条件
- 状态管理是关键，需要妥善维护对话历史和迭代计数
- 自我修正需要设计质量评估机制来决策是否继续迭代
- 多轮问答要合理处理信息需求和上下文维护
```