```markdown
# 并行执行多个节点

### 🎯 核心概念
并行执行允许同时运行多个独立节点，显著提升复杂Agent流程的效率，是构建高性能多任务处理系统的关键能力。

### 💡 使用方式
使用 `add_node` 添加多个节点后，通过条件边或并行边实现并发执行。核心API包括：
- `StateGraph.add_node()`: 添加节点
- 条件边配置实现并行分支

### 📚 Level 1: 基础认知（30秒理解）
最简单的并行执行示例：同时处理两个独立任务

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
import asyncio

# 定义状态
class ParallelState(TypedDict):
    tasks: List[str]
    results: List[str]

# 定义节点函数
def process_task_1(state: ParallelState):
    print("执行任务1...")
    return {"results": [*state.get("results", []), "任务1完成"]}

def process_task_2(state: ParallelState):
    print("执行任务2...")
    return {"results": [*state.get("results", []), "任务2完成"]}

# 构建图
builder = StateGraph(ParallelState)
builder.add_node("task1", process_task_1)
builder.add_node("task2", process_task_2)

# 设置并行执行
builder.set_entry_point("task1")
builder.add_edge("task1", "task2")
builder.add_edge("task2", END)

# 编译和执行
graph = builder.compile()
result = graph.invoke({"tasks": ["task1", "task2"], "results": []})
print("最终结果:", result["results"])
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 动态并行选择
根据输入状态动态决定并行执行哪些节点

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class DynamicState(TypedDict):
    selected_tasks: List[str]
    outputs: dict

def task_a(state: DynamicState):
    return {"outputs": {**state.get("outputs", {}), "A": "完成A任务"}}

def task_b(state: DynamicState):
    return {"outputs": {**state.get("outputs", {}), "B": "完成B任务"}}

def task_c(state: DynamicState):
    return {"outputs": {**state.get("outputs", {}), "C": "完成C任务"}}

def route_tasks(state: DynamicState):
    # 根据输入动态选择要执行的任务
    return state["selected_tasks"]

builder = StateGraph(DynamicState)
builder.add_node("task_a", task_a)
builder.add_node("task_b", task_b)
builder.add_node("task_c", task_c)

builder.set_entry_point("route")
builder.add_conditional_edges("route", route_tasks)
builder.add_edge("task_a", END)
builder.add_edge("task_b", END)
builder.add_edge("task_c", END)

graph = builder.compile()

# 测试动态选择
result1 = graph.invoke({"selected_tasks": ["task_a", "task_b"]})
print("执行A和B:", result1["outputs"])

result2 = graph.invoke({"selected_tasks": ["task_c"]})
print("只执行C:", result2["outputs"])
```

#### 特性2: 并行结果聚合
多个并行节点执行后聚合结果

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
import random

class AggregationState(TypedDict):
    data: str
    processed_results: List[str]
    final_result: str

def processor_1(state: AggregationState):
    result = f"处理1: {state['data'].upper()}"
    return {"processed_results": [*state.get("processed_results", []), result]}

def processor_2(state: AggregationState):
    result = f"处理2: {state['data'].lower()}"
    return {"processed_results": [*state.get("processed_results", []), result]}

def processor_3(state: AggregationState):
    result = f"处理3: {state['data'][::-1]}"
    return {"processed_results": [*state.get("processed_results", []), result]}

def aggregate_results(state: AggregationState):
    results = state["processed_results"]
    final = " | ".join(results)
    return {"final_result": final}

builder = StateGraph(AggregationState)
builder.add_node("process1", processor_1)
builder.add_node("process2", processor_2)
builder.add_node("process3", processor_3)
builder.add_node("aggregate", aggregate_results)

# 并行执行三个处理器，然后聚合
builder.set_entry_point("process1")
builder.add_edge("process1", "process2")
builder.add_edge("process2", "process3")
builder.add_edge("process3", "aggregate")
builder.add_edge("aggregate", END)

graph = builder.compile()
result = graph.invoke({"data": "HelloWorld", "processed_results": []})
print("聚合结果:", result["final_result"])
```

### 🔍 Level 3: 对比学习（避免陷阱）

```python
# 错误用法：错误的并行设计导致状态冲突
def bad_parallel_design():
    class ConflictState(TypedDict):
        value: int
    
    def increment_1(state: ConflictState):
        return {"value": state["value"] + 1}  # 可能与其他节点冲突
    
    def increment_2(state: ConflictState):
        return {"value": state["value"] + 2}  # 状态写入冲突
    
    # 这种设计会导致不可预测的结果

# 正确用法：使用独立状态字段或结果聚合
class SafeState(TypedDict):
    input_value: int
    result1: int
    result2: int
    final_result: int

def safe_increment_1(state: SafeState):
    return {"result1": state["input_value"] + 1}  # 写入独立字段

def safe_increment_2(state: SafeState):
    return {"result2": state["input_value"] + 2}  # 写入独立字段

def combine_results(state: SafeState):
    return {"final_result": state["result1"] + state["result2"]}
```

### 🚀 Level 4: 实战应用（真实场景）
构建内容生成流水线：并行执行摘要生成、情感分析和关键词提取

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional
import time

class ContentAnalysisState(TypedDict):
    content: str
    summary: Optional[str]
    sentiment: Optional[str]
    keywords: Optional[List[str]]
    final_report: Optional[str]

def simulate_llm_call(task_name, content):
    """模拟LLM调用延迟"""
    time.sleep(0.1)  # 模拟网络延迟
    if task_name == "summarize":
        return f"摘要: {content[:50]}..."
    elif task_name == "sentiment":
        return "积极" if len(content) > 100 else "中性"
    elif task_name == "keywords":
        return ["关键词1", "关键词2", "关键词3"]
    return None

def generate_summary(state: ContentAnalysisState):
    summary = simulate_llm_call("summarize", state["content"])
    return {"summary": summary}

def analyze_sentiment(state: ContentAnalysisState):
    sentiment = simulate_llm_call("sentiment", state["content"])
    return {"sentiment": sentiment}

def extract_keywords(state: ContentAnalysisState):
    keywords = simulate_llm_call("keywords", state["content"])
    return {"keywords": keywords}

def generate_final_report(state: ContentAnalysisState):
    report = f"""
    内容分析报告:
    - 摘要: {state['summary']}
    - 情感: {state['sentiment']}
    - 关键词: {', '.join(state['keywords'])}
    """
    return {"final_report": report}

# 构建并行处理流水线
builder = StateGraph(ContentAnalysisState)
builder.add_node("summarize", generate_summary)
builder.add_node("sentiment", analyze_sentiment)
builder.add_node("keywords", extract_keywords)
builder.add_node("report", generate_final_report)

# 设置并行执行流程
builder.set_entry_point("summarize")
builder.add_edge("summarize", "sentiment")
builder.add_edge("sentiment", "keywords")
builder.add_edge("keywords", "report")
builder.add_edge("report", END)

# 执行分析
graph = builder.compile()
sample_content = "这是一段示例文本内容，用于演示LangGraph的并行执行能力。通过同时运行多个分析任务，我们可以显著提升处理效率。"

result = graph.invoke({
    "content": sample_content,
    "summary": None,
    "sentiment": None,
    "keywords": None,
    "final_report": None
})

print("最终分析报告:")
print(result["final_report"])
```

### 💡 记忆要点
- 并行执行通过同时运行独立节点大幅提升处理效率
- 确保并行节点之间没有状态写入冲突，使用独立字段存储结果
- 合理设计聚合节点来收集和处理并行执行的结果
- 考虑任务之间的依赖关系，避免不必要的并行带来的复杂度
```