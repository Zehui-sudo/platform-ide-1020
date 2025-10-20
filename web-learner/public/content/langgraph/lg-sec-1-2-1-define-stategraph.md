```markdown
# 定义 StateGraph

## 🎯 核心概念
StateGraph 是 LangGraph 中构建有状态工作流的核心骨架，它通过统一的状态管理机制解决了多步骤 Agent 流程中的状态传递和共享问题，是构建复杂 AI 应用的关键基础。

## 💡 使用方式
StateGraph 的核心 API 是通过 `StateGraph` 类来创建图实例，需要指定状态 Schema 来定义工作流中传递的数据结构。

```python
from langgraph.graph import StateGraph
from typing import TypedDict

# 定义状态结构
class AgentState(TypedDict):
    input: str
    processed_data: str

# 创建 StateGraph 实例
graph = StateGraph(AgentState)
```

## 📚 Level 1: 基础认知（30秒理解）
最基本的 StateGraph 定义和运行示例，展示如何创建一个最小可工作的工作流。

```python
from langgraph.graph import StateGraph
from typing import TypedDict

# 1. 定义状态结构
class SimpleState(TypedDict):
    message: str

# 2. 定义节点函数
def start_node(state: SimpleState):
    return {"message": "Hello from StateGraph!"}

# 3. 创建并配置图
graph = StateGraph(SimpleState)
graph.add_node("start", start_node)
graph.set_entry_point("start")
graph.set_finish_point("start")

# 4. 编译并运行
app = graph.compile()
result = app.invoke({"message": ""})
print(result["message"])  # 输出: Hello from StateGraph!
```

## 📈 Level 2: 核心特性（深入理解）

### 特性1: 状态更新与传递
StateGraph 的核心能力是状态在各个节点间的自动传递和更新。

```python
from langgraph.graph import StateGraph
from typing import TypedDict

class ProcessingState(TypedDict):
    input_text: str
    processed_text: str
    step_count: int

def preprocess_node(state: ProcessingState):
    # 处理输入文本
    processed = state["input_text"].upper()
    return {"processed_text": processed, "step_count": 1}

def count_node(state: ProcessingState):
    # 统计字符数
    char_count = len(state["processed_text"])
    return {"processed_text": f"{state['processed_text']} ({char_count} chars)", 
            "step_count": state["step_count"] + 1}

# 构建工作流
graph = StateGraph(ProcessingState)
graph.add_node("preprocess", preprocess_node)
graph.add_node("count", count_node)

graph.set_entry_point("preprocess")
graph.add_edge("preprocess", "count")
graph.set_finish_point("count")

app = graph.compile()
result = app.invoke({"input_text": "hello world", "processed_text": "", "step_count": 0})
print(result)  # 输出处理后的状态
```

### 特性2: 条件边与动态流程
StateGraph 支持基于状态的条件分支，实现动态工作流。

```python
from langgraph.graph import StateGraph
from typing import TypedDict, Literal

class RoutingState(TypedDict):
    input_type: Literal["text", "number", "other"]
    data: str
    result: str

def classify_node(state: RoutingState):
    if state["data"].isdigit():
        return {"input_type": "number"}
    elif state["data"].isalpha():
        return {"input_type": "text"}
    else:
        return {"input_type": "other"}

def process_text(state: RoutingState):
    return {"result": f"Text processed: {state['data'].upper()}"}

def process_number(state: RoutingState):
    return {"result": f"Number squared: {int(state['data'])**2}"}

def process_other(state: RoutingState):
    return {"result": f"Other input: {state['data']}"}

graph = StateGraph(RoutingState)
graph.add_node("classify", classify_node)
graph.add_node("process_text", process_text)
graph.add_node("process_number", process_number)
graph.add_node("process_other", process_other)

graph.set_entry_point("classify")

# 添加条件边
graph.add_conditional_edges(
    "classify",
    lambda state: state["input_type"],
    {
        "text": "process_text",
        "number": "process_number", 
        "other": "process_other"
    }
)

graph.set_finish_point("process_text")
graph.set_finish_point("process_number")
graph.set_finish_point("process_other")

app = graph.compile()

# 测试不同类型输入
print(app.invoke({"data": "hello", "input_type": "", "result": ""}))
print(app.invoke({"data": "42", "input_type": "", "result": ""}))
print(app.invoke({"data": "hello123", "input_type": "", "result": ""}))
```

## 🔍 Level 3: 对比学习（避免陷阱）

### 状态更新方式对比
错误用法：直接修改状态对象 vs 正确用法：返回更新字典

```python
# ❌ 错误用法：直接修改状态（不会生效）
def wrong_node(state):
    state["value"] = "modified"  # 这不会更新状态
    return state

# ✅ 正确用法：返回更新字典
def correct_node(state):
    return {"value": "modified"}  # 返回要更新的字段

# 验证差异
from langgraph.graph import StateGraph
from typing import TypedDict

class TestState(TypedDict):
    value: str

graph = StateGraph(TestState)
graph.add_node("test", correct_node)  # 改为 wrong_node 测试错误情况
graph.set_entry_point("test")
graph.set_finish_point("test")

app = graph.compile()
result = app.invoke({"value": "original"})
print(result["value"])  # 正确输出: modified
```

## 🚀 Level 4: 实战应用（真实场景）
构建一个简单的文档处理流水线，包含文本清理、关键词提取和摘要生成。

```python
from langgraph.graph import StateGraph
from typing import TypedDict, List
import re

class DocumentState(TypedDict):
    raw_text: str
    cleaned_text: str
    keywords: List[str]
    summary: str

def clean_text_node(state: DocumentState):
    # 简单的文本清理
    cleaned = re.sub(r'\s+', ' ', state["raw_text"]).strip()
    return {"cleaned_text": cleaned}

def extract_keywords_node(state: DocumentState):
    # 提取关键词（简单实现）
    words = state["cleaned_text"].split()
    keywords = [word for word in words if len(word) > 5][:3]  # 取长度大于5的前3个词
    return {"keywords": keywords}

def generate_summary_node(state: DocumentState):
    # 生成简单摘要
    sentences = state["cleaned_text"].split('. ')
    summary = '. '.join(sentences[:2]) + '.'  # 取前两句作为摘要
    return {"summary": summary}

# 构建文档处理流水线
graph = StateGraph(DocumentState)
graph.add_node("clean", clean_text_node)
graph.add_node("extract_keywords", extract_keywords_node)
graph.add_node("generate_summary", generate_summary_node)

graph.set_entry_point("clean")
graph.add_edge("clean", "extract_keywords")
graph.add_edge("extract_keywords", "generate_summary")
graph.set_finish_point("generate_summary")

app = graph.compile()

# 处理示例文档
document = """
LangGraph is a powerful library for building stateful, multi-step AI applications. 
It provides a clean abstraction for managing complex workflows with memory and state. 
The library is particularly useful for building agentic systems that require 
sequential processing and conditional logic. With its intuitive API, developers 
can quickly create sophisticated AI pipelines.
"""

result = app.invoke({
    "raw_text": document,
    "cleaned_text": "",
    "keywords": [],
    "summary": ""
})

print("Cleaned Text:", result["cleaned_text"])
print("Keywords:", result["keywords"])
print("Summary:", result["summary"])
```

## 💡 记忆要点
- StateGraph 是构建有状态工作流的骨架，需要明确定义状态结构
- 节点函数通过返回字典来更新状态，而不是直接修改输入状态
- 状态在节点间自动传递，确保工作流的连贯性
- 条件边允许基于状态值实现动态分支逻辑
- 合理的状态设计是构建复杂 Agent 系统的关键基础
```