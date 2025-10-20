```markdown
# 构建一个简单的 ReAct Agent

### 🎯 核心概念
ReAct (Reasoning + Acting) 是一种结合推理和行动的Agent架构模式，它解决了传统Agent在复杂任务中缺乏思考过程的问题。通过让Agent在行动前进行推理，在LangGraph中构建可解释、可控制的智能工作流。

### 💡 使用方式
核心是通过 `StateGraph` 管理状态，使用条件边实现"思考-行动"的循环模式：
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
import json
```

### 📚 Level 1: 基础认知（30秒理解）
一个最简单的ReAct Agent，能够进行数学计算和文本处理：

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Literal
import json
from langchain_core.tools import tool

# 定义状态
class AgentState(TypedDict):
    task: str
    reasoning: List[str]
    actions: List[str]
    result: str

# 定义工具
@tool
def calculate(expression: str) -> str:
    """计算数学表达式"""
    try:
        return str(eval(expression))
    except:
        return "计算错误"

@tool  
def reverse_text(text: str) -> str:
    """反转文本"""
    return text[::-1]

tools = [calculate, reverse_text]
tool_map = {tool.name: tool for tool in tools}

# 思考节点
def think_node(state: AgentState):
    reasoning = f"思考如何解决任务: {state['task']}"
    return {"reasoning": state["reasoning"] + [reasoning]}

# 行动节点  
def act_node(state: AgentState):
    latest_reasoning = state["reasoning"][-1]
    
    if "计算" in latest_reasoning:
        action = "calculate"
        # 简单提取数字表达式
        import re
        numbers = re.findall(r'\d+', state["task"])
        if numbers:
            args = " ".join(numbers)
        else:
            args = "2+2"
    else:
        action = "reverse_text"
        args = state["task"].split()[-1] if len(state["task"].split()) > 1 else "hello"
    
    result = tool_map[action].invoke(args)
    return {
        "actions": state["actions"] + [f"{action}({args}) = {result}"],
        "result": result
    }

# 条件边函数
def should_continue(state: AgentState) -> Literal["think", "__end__"]:
    if len(state["actions"]) < 2:  # 简单限制执行次数
        return "think"
    return "__end__"

# 构建图
graph = StateGraph(AgentState)
graph.add_node("think", think_node)
graph.add_node("act", act_node)

graph.set_entry_point("think")
graph.add_edge("think", "act")
graph.add_conditional_edges("act", should_continue)

app = graph.compile()

# 运行示例
result = app.invoke({"task": "计算123的平方然后反转", "reasoning": [], "actions": [], "result": ""})
print("最终结果:", result["result"])
print("推理过程:", result["reasoning"])
print("执行动作:", result["actions"])
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 动态工具选择
使用LLM动态选择最合适的工具：

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-3.5-turbo")

def smart_think_node(state: AgentState):
    prompt = ChatPromptTemplate.from_template("""
    任务: {task}
    可用工具: {tools}
    
    请分析任务并选择最合适的工具。返回JSON格式:
    {{
        "reasoning": "你的推理过程",
        "tool_name": "工具名称", 
        "tool_args": "工具参数"
    }}
    """)
    
    chain = prompt | llm
    response = chain.invoke({
        "task": state["task"],
        "tools": [f"{t.name}: {t.description}" for t in tools]
    })
    
    try:
        decision = json.loads(response.content)
        return {
            "reasoning": state["reasoning"] + [decision["reasoning"]],
            "selected_tool": decision["tool_name"],
            "tool_args": decision["tool_args"]
        }
    except:
        return {"reasoning": state["reasoning"] + ["解析响应失败"]}

def smart_act_node(state: AgentState):
    if hasattr(state, "selected_tool") and state["selected_tool"] in tool_map:
        result = tool_map[state["selected_tool"]].invoke(state["tool_args"])
        return {
            "actions": state["actions"] + [f"{state['selected_tool']}({state['tool_args']}) = {result}"],
            "result": result
        }
    return {"result": "无法执行动作"}

# 更新图
smart_graph = StateGraph(AgentState)
smart_graph.add_node("think", smart_think_node)
smart_graph.add_node("act", smart_act_node)
smart_graph.set_entry_point("think")
smart_graph.add_edge("think", "act")
smart_graph.add_conditional_edges("act", should_continue)

smart_app = smart_graph.compile()
```

#### 特性2: 多步推理循环
实现完整的ReAct循环：

```python
def react_should_continue(state: AgentState) -> Literal["think", "__end__"]:
    if "答案" in state.get("result", "") or len(state["actions"]) >= 3:
        return "__end__"
    return "think"

# 完整的ReAct图
react_graph = StateGraph(AgentState)
react_graph.add_node("think", smart_think_node)
react_graph.add_node("act", smart_act_node)

react_graph.set_entry_point("think")
react_graph.add_edge("think", "act")
react_graph.add_conditional_edges("act", react_should_continue)

react_app = react_graph.compile()
```

### 🔍 Level 3: 对比学习（避免陷阱）

```python
# 错误用法：缺少状态管理
def bad_think_node(task: str):  # ❌ 没有使用状态
    return "直接思考"

# 正确用法：使用状态对象
def good_think_node(state: AgentState):  # ✅ 使用状态
    return {"reasoning": state["reasoning"] + ["新的思考"]}

# 错误用法：硬编码工具选择
def bad_act_node(state: AgentState):
    result = calculate("2+2")  # ❌ 硬编码工具
    return {"result": result}

# 正确用法：动态工具选择  
def good_act_node(state: AgentState):
    if state["selected_tool"] == "calculate":
        result = calculate(state["tool_args"])
    return {"result": result}
```

### 🚀 Level 4: 实战应用（真实场景）
构建一个能够处理复杂查询的ReAct Agent：

```python
from langchain_community.tools import DuckDuckGoSearchRun

# 添加搜索工具
search_tool = DuckDuckGoSearchRun()
tools.append(search_tool)
tool_map["duckduckgo_search"] = search_tool

def enhanced_think_node(state: AgentState):
    prompt = ChatPromptTemplate.from_template("""
    你是一个ReAct Agent。当前任务: {task}
    历史推理: {history}
    可用工具: {tools}
    
    请决定下一步行动。返回JSON:
    {{
        "reasoning": "详细推理",
        "tool": "工具名|final_answer",
        "args": "参数或最终答案"
    }}
    """)
    
    chain = prompt | llm
    response = chain.invoke({
        "task": state["task"],
        "history": state["reasoning"][-2:] if state["reasoning"] else "无",
        "tools": [t.name for t in tools]
    })
    
    try:
        decision = json.loads(response.content)
        return {
            "reasoning": state["reasoning"] + [decision["reasoning"]],
            "selected_tool": decision["tool"],
            "tool_args": decision["args"]
        }
    except:
        return {"reasoning": state["reasoning"] + ["思考失败"]}

def enhanced_act_node(state: AgentState):
    if state["selected_tool"] == "final_answer":
        return {"result": state["tool_args"], "actions": state["actions"] + ["给出最终答案"]}
    
    if state["selected_tool"] in tool_map:
        result = tool_map[state["selected_tool"]].invoke(state["tool_args"])
        return {
            "actions": state["actions"] + [f"{state['selected_tool']}({state['tool_args']})"],
            "intermediate_result": result
        }
    return {"result": "工具不存在"}

# 构建增强版ReAct Agent
enhanced_graph = StateGraph(AgentState)
enhanced_graph.add_node("think", enhanced_think_node)
enhanced_graph.add_node("act", enhanced_act_node)
enhanced_graph.set_entry_point("think")
enhanced_graph.add_edge("think", "act")
enhanced_graph.add_conditional_edges("act", react_should_continue)

enhanced_app = enhanced_graph.compile()

# 运行复杂查询
result = enhanced_app.invoke({
    "task": "搜索LangGraph的最新版本并计算其主要版本号加1",
    "reasoning": [],
    "actions": [],
    "result": ""
})
print("增强版ReAct结果:", result)
```

### 💡 记忆要点
- ReAct模式通过"思考-行动"循环实现可解释的推理过程
- 状态管理是LangGraph中构建ReAct Agent的核心
- 条件边用于控制循环的继续或终止
- 工具集成使得Agent能够执行具体行动
- 多步推理能力让Agent能够处理复杂任务
```