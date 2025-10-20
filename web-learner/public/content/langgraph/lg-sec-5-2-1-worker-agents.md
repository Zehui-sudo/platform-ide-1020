## 定义工作Agent

### 🎯 核心概念
工作Agent是多智能体团队中的具体执行单元，负责处理特定子任务（如数据检索、分析或内容生成），它是实现复杂工作流分工的关键，通过专业化提高效率和效果。在LangGraph中，工作Agent通常定义为节点函数，接收共享状态并返回更新后的状态， enabling seamless collaboration in multi-agent systems.

### 💡 使用方式
在LangGraph中，工作Agent通过`add_node`方法添加到图中，核心API包括状态定义（TypedDict）、节点函数（接收和返回状态）、以及图构建。基本用法是定义一个函数处理状态中的特定字段，并返回更新部分。必要时可集成LangChain Tools来扩展能力。

### 📚 Level 1: 基础认知（30秒理解）
一个最简单的工作Agent示例，接收输入文本并转换为大写。完整可运行代码，展示基本结构。

```python
from typing import TypedDict
from langgraph.graph import StateGraph, END

# 定义状态结构
class State(TypedDict):
    input: str
    output: str

# 工作Agent节点函数：处理输入
def worker_agent(state: State) -> State:
    processed_text = state['input'].upper()  # 简单处理：转为大写
    return {'output': processed_text}  # 返回更新部分

# 构建图
graph = StateGraph(State)
graph.add_node('worker', worker_agent)  # 添加工作Agent节点
graph.set_entry_point('worker')  # 设置入口
graph.add_edge('worker', END)  # 连接至结束

compiled_graph = graph.compile()  # 编译图

# 运行图
if __name__ == '__main__':
    result = compiled_graph.invoke({'input': 'hello world'})
    print(result)  # 输出: {'input': 'hello world', 'output': 'HELLO WORLD'}
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 集成LangChain Tools
工作Agent可以使用LangChain工具（如网络搜索）执行具体任务，增强实用性。以下示例使用模拟工具避免外部API依赖。

```python
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain.agents import Tool

# 模拟一个工具函数：避免真实API调用
def mock_search(query: str) -> str:
    return f"Search results for: {query}"

# 定义工具
tools = [
    Tool(
        name="MockSearch",
        func=mock_search,
        description="A mock search tool for demonstration"
    )
]

# 定义状态
class State(TypedDict):
    query: str
    result: str

# 工作Agent使用工具
def research_agent(state: State) -> State:
    tool_result = tools[0].run(state['query'])  # 调用工具
    return {'result': tool_result}  # 更新状态

# 构建图
graph = StateGraph(State)
graph.add_node('researcher', research_agent)
graph.set_entry_point('researcher')
graph.add_edge('researcher', END)

compiled_graph = graph.compile()

# 运行
if __name__ == '__main__':
    result = compiled_graph.invoke({'query': 'What is LangGraph?'})
    print(result)  # 输出: {'query': 'What is LangGraph?', 'result': 'Search results for: What is LangGraph?'}
```

#### 特性2: 状态共享与任务处理
工作Agent可以处理共享状态中的任务列表，演示如何读取和更新列表字段，适用于多任务场景。

```python
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

# 定义状态 with task list
class State(TypedDict):
    tasks: List[str]
    results: List[str]

# 工作Agent处理第一个任务
def worker_agent(state: State) -> State:
    if state['tasks']:
        task = state['tasks'][0]
        processed = f"Processed: {task.upper()}"
        new_tasks = state['tasks'][1:]  # 移除已处理任务
        new_results = state['results'] + [processed]  # 添加结果
        return {'tasks': new_tasks, 'results': new_results}
    return state  # 无任务时返回原状态

# 构建图
graph = StateGraph(State)
graph.add_node('worker', worker_agent)
graph.set_entry_point('worker')
graph.add_edge('worker', END)

compiled_graph = graph.compile()

# 运行
if __name__ == '__main__':
    initial_state = {'tasks': ['research topic', 'write summary'], 'results': []}
    result = compiled_graph.invoke(initial_state)
    print(result)  # 输出: {'tasks': ['write summary'], 'results': ['Processed: RESEARCH TOPIC']}
```

### 🔍 Level 3: 对比学习（避免陷阱）
常见错误是直接修改传入状态而不返回更新，或返回整个状态降低效率。以下展示正确与错误用法。

```python
from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    data: str

# 错误用法：修改状态但不返回更新（或返回整个状态）
def bad_worker(state: State) -> State:
    state['data'] = state['data'] + " modified"  # 直接修改，可能不会触发更新
    return state  # 返回整个状态，不高效

# 正确用法：返回仅更新