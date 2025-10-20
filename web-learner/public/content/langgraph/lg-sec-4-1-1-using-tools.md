```markdown
## 在节点中调用 Tool

### 🎯 核心概念
在节点中调用 Tool 是将 LangChain 工具能力集成到 LangGraph 工作流的核心方式，它让 Agent 能够执行外部操作（如网络请求、数据库查询、文件操作等），从而构建真正实用的智能应用。

### 💡 使用方式
通过 `ToolNode` 或自定义节点函数调用 `tool.run()` 方法来执行工具。关键 API：
- `ToolNode(tools)`: 创建预配置的工具节点
- `tool.run(input)`: 执行工具并返回结果

### 📚 Level 1: 基础认知（30秒理解）
最简单的工具调用示例：创建一个计算字符串长度的工具并在图中使用。

```python
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from typing import TypedDict

# 定义状态
class AgentState(TypedDict):
    input: str
    output: str

# 创建简单工具
@tool
def string_length(text: str) -> int:
    """返回字符串长度"""
    return len(text)

# 定义工具调用节点
def tool_node(state: AgentState):
    result = string_length.run(state["input"])
    return {"output": f"字符串长度为: {result}"}

# 构建图
builder = StateGraph(AgentState)
builder.add_node("calculate_length", tool_node)
builder.set_entry_point("calculate_length")
builder.add_edge("calculate_length", END)
graph = builder.compile()

# 执行
result = graph.invoke({"input": "Hello LangGraph"})
print(result["output"])
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 多工具集成与自动选择
```python
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from typing import TypedDict
import math

# 定义状态
class AgentState(TypedDict):
    input: str
    output: str
    selected_tool: str

# 创建多个工具
@tool
def calculate_square(n: float) -> float:
    """计算数字的平方"""
    return n * n

@tool
def calculate_sqrt(n: float) -> float:
    """计算数字的平方根"""
    return math.sqrt(n)

# 工具调用节点
def tool_node(state: AgentState):
    if "square" in state["input"].lower():
        result = calculate_square.run(4)  # 示例输入
        return {"output": f"平方结果: {result}", "selected_tool": "square"}
    else:
        result = calculate_sqrt.run(16)   # 示例输入
        return {"output": f"平方根结果: {result}", "selected_tool": "sqrt"}

# 构建图
builder = StateGraph(AgentState)
builder.add_node("select_and_run_tool", tool_node)
builder.set_entry_point("select_and_run_tool")
builder.add_edge("select_and_run_tool", END)
graph = builder.compile()

# 执行不同输入
result1 = graph.invoke({"input": "计算平方"})
result2 = graph.invoke({"input": "计算根号"})
print(f"结果1: {result1}")
print(f"结果2: {result2}")
```

#### 特性2: 工具异常处理
```python
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from typing import TypedDict

class AgentState(TypedDict):
    input: str
    output: str
    error: str

@tool
def divide_numbers(a: float, b: float) -> float:
    """除法计算"""
    if b == 0:
        raise ValueError("除数不能为零")
    return a / b

def safe_tool_node(state: AgentState):
    try:
        # 模拟从输入中提取参数
        result = divide_numbers.run(10, 2)  # 正常情况
        # result = divide_numbers.run(10, 0)  # 异常情况
        return {"output": f"结果: {result}", "error": ""}
    except Exception as e:
        return {"output": "", "error": f"工具执行错误: {str(e)}"}

builder = StateGraph(AgentState)
builder.add_node("safe_calculation", safe_tool_node)
builder.set_entry_point("safe_calculation")
builder.add_edge("safe_calculation", END)
graph = builder.compile()

# 测试异常处理
result = graph.invoke({"input": "除法计算"})
print(result)
```

### 🔍 Level 3: 对比学习（避免陷阱）

```python
# 错误用法：直接调用工具而不处理状态
def bad_tool_node(state):
    # 错误：直接修改外部状态，不返回正确格式
    result = string_length.run("test")
    state["output"] = result  # 不应该直接修改state

# 正确用法：返回新的状态字典
def correct_tool_node(state: AgentState):
    result = string_length.run(state["input"])
    # 正确：返回包含更新字段的字典
    return {"output": f"处理结果: {result}"}
```

### 🚀 Level 4: 实战应用（真实场景）
构建一个天气查询Agent，集成真实API工具调用。

```python
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from typing import TypedDict
import requests

class WeatherState(TypedDict):
    city: str
    weather_info: str
    temperature: float

# 模拟天气API工具
@tool
def get_weather(city: str) -> dict:
    """获取城市天气信息（模拟API）"""
    # 实际项目中这里会调用真实天气API
    mock_data = {
        "Beijing": {"weather": "晴", "temp": 25},
        "Shanghai": {"weather": "多云", "temp": 28},
        "Guangzhou": {"weather": "雨", "temp": 30}
    }
    return mock_data.get(city, {"weather": "未知", "temp": 0})

def weather_node(state: WeatherState):
    result = get_weather.run(state["city"])
    return {
        "weather_info": result["weather"],
        "temperature": result["temp"]
    }

def format_output_node(state: WeatherState):
    return {
        "weather_info": f"{state['city']}天气: {state['weather_info']}, 温度: {state['temperature']}°C"
    }

# 构建工作流
builder = StateGraph(WeatherState)
builder.add_node("fetch_weather", weather_node)
builder.add_node("format_output", format_output_node)
builder.set_entry_point("fetch_weather")
builder.add_edge("fetch_weather", "format_output")
builder.add_edge("format_output", END)
graph = builder.compile()

# 执行查询
results = []
for city in ["Beijing", "Shanghai", "Guangzhou"]:
    result = graph.invoke({"city": city})
    results.append(result["weather_info"])

for info in results:
    print(info)
```

### 💡 记忆要点
- Tool节点必须返回与State结构兼容的字典
- 使用try-catch处理工具执行中的异常
- 工具输入参数需要从State中提取或解析
- 多个工具可以集成在同一个节点中根据条件选择调用
- 工具执行结果是字符串或可序列化对象，便于状态管理
```