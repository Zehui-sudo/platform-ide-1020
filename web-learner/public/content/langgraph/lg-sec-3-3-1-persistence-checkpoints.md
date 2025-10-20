```markdown
# 使用 Checkpointer 保存和恢复图的状态

### 🎯 核心概念
Checkpointer 解决了长时间运行或可能中断的 Agent 流程的状态持久化问题，它能够保存和恢复图的状态，是构建可靠、可恢复的复杂工作流的关键组件。

### 💡 使用方式
核心 API 是通过 `add_checkpointer` 方法为图添加检查点配置，支持内存、文件系统和数据库等多种存储后端。

### 📚 Level 1: 基础认知（30秒理解）
最简单的内存检查点使用示例：

```python
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# 定义状态
class State(TypedDict):
    value: Annotated[int, lambda x, y: x + y]

# 创建节点函数
def add_one(state: State):
    return {"value": 1}

# 构建图
builder = StateGraph(State)
builder.add_node("add_one", add_one)
builder.set_entry_point("add_one")
builder.set_finish_point("add_one")

# 添加内存检查点
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

# 运行并保存状态
config = {"configurable": {"thread_id": "thread-1"}}
result = graph.invoke({"value": 0}, config)
print(f"First run result: {result}")

# 恢复状态继续执行
new_result = graph.invoke(None, config)
print(f"Continue from checkpoint: {new_result}")
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 文件系统检查点持久化
```python
import tempfile
import os
from langgraph.checkpoint.filesystem import FileSaver

# 创建临时目录存储检查点
with tempfile.TemporaryDirectory() as temp_dir:
    # 文件系统检查点
    file_checkpointer = FileSaver(base_dir=temp_dir)
    
    # 使用相同的图定义
    file_graph = builder.compile(checkpointer=file_checkpointer)
    
    # 第一次执行
    config = {"configurable": {"thread_id": "file-thread-1"}}
    result1 = file_graph.invoke({"value": 10}, config)
    print(f"First result: {result1}")
    
    # 检查点文件已创建
    checkpoint_files = os.listdir(temp_dir)
    print(f"Checkpoint files: {checkpoint_files}")
    
    # 从检查点恢复
    result2 = file_graph.invoke(None, config)
    print(f"Continued result: {result2}")
```

#### 特性2: 多会话状态管理
```python
# 使用不同的 thread_id 管理多个独立会话
config1 = {"configurable": {"thread_id": "session-1"}}
config2 = {"configurable": {"thread_id": "session-2"}}

# 两个独立的会话
result1 = graph.invoke({"value": 5}, config1)
result2 = graph.invoke({"value": 10}, config2)

print(f"Session 1: {result1}")
print(f"Session 2: {result2}")

# 分别继续执行
continued1 = graph.invoke(None, config1)
continued2 = graph.invoke(None, config2)

print(f"Session 1 continued: {continued1}")
print(f"Session 2 continued: {continued2}")
```

### 🔍 Level 3: 对比学习（避免陷阱）

```python
# 错误用法：忘记传递 configurable 配置
try:
    # 缺少必要的 thread_id 配置
    graph.invoke({"value": 0}, {})
except Exception as e:
    print(f"错误: {e}")

# 正确用法：始终提供 configurable 配置
correct_config = {"configurable": {"thread_id": "correct-thread"}}
result = graph.invoke({"value": 0}, correct_config)
print(f"正确执行结果: {result}")

# 错误用法：在不同图实例间共享检查点
graph1 = builder.compile(checkpointer=memory)
graph2 = builder.compile(checkpointer=memory)  # 应该使用不同的检查点实例

# 正确用法：为每个图实例创建独立的检查点
memory1 = MemorySaver()
memory2 = MemorySaver()
graph1 = builder.compile(checkpointer=memory1)
graph2 = builder.compile(checkpointer=memory2)
```

### 🚀 Level 4: 实战应用（真实场景）
构建一个带有人工审核的多步骤工作流，支持中断和恢复：

```python
from typing import Literal
from langgraph.graph import MessagesState
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchResults
import os

# 设置环境变量（实际使用时替换为您的API密钥）
os.environ["OPENAI_API_KEY"] = "your-openai-api-key"

# 创建工具和模型
tools = [DuckDuckGoSearchResults(max_results=2)]
model = ChatOpenAI(model="gpt-3.5-turbo")

# 创建带有检查点的Agent
memory = MemorySaver()
agent = create_react_agent(model, tools, checkpointer=memory)

# 模拟长时间运行的研究任务
config = {"configurable": {"thread_id": "research-task-1"}}

# 第一次执行：开始研究
print("=== 开始研究任务 ===")
result1 = agent.invoke(
    {"messages": [("human", "研究一下LangGraph的最新特性")]},
    config
)
print(f"初步研究结果: {result1['messages'][-1].content[:100]}...")

# 模拟任务中断（程序重启）
print("\n=== 模拟程序重启 ===")
print("检查点已保存，程序可以安全重启")

# 恢复任务继续执行
print("\n=== 恢复研究任务 ===")
result2 = agent.invoke(
    {"messages": [("human", "请继续深入研究，特别是检查点功能")]},
    config
)
print(f"深入研究结果: {result2['messages'][-1].content[:100]}...")

# 查看检查点状态
threads = memory.list()
print(f"\n当前保存的会话: {threads}")
```

**预期输出说明**：
1. 第一次执行会开始研究 LangGraph 特性
2. 程序"重启"后，可以从检查点恢复之前的状态
3. 第二次调用会基于之前的研究结果继续深入
4. 最后显示所有保存的会话信息

### 💡 记忆要点
- 检查点通过 `add_checkpointer` 或 `checkpointer` 参数配置
- 必须提供 `configurable.thread_id` 来标识不同的执行会话
- 支持多种存储后端：内存、文件系统、数据库等
- 检查点使长时间运行或可能中断的流程变得可靠
- 不同的图实例应该使用不同的检查点实例以避免状态冲突
```