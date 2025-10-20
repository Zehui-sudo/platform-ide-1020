"""
This script is for quick experiments with the OpenAI API.
Before running, ensure you have set the OPENAI_API_KEY environment variable.
Example:
export OPENAI_API_KEY="your_api_key_here"
python scripts/experiments/chatgpt-quick.py
"""

from openai import OpenAI
client = OpenAI()

response = client.responses.create(
    model="gpt-4.1",
    tools=[{"type": "web_search"}],
    input='''
      "title": "Pattern Recognition and Machine Learning",
      "authors": [
        "Christopher M. Bishop"
      ] 
      这本书的完整目录是什么？
      输出时务必按照类似以下格式进行输出，具体到每个章节下的小节，保留原有层级与顺序：
## 第1章：LangGraph入门
### 1.1 核心概念
#### 1.1.1 什么是 LangGraph? (解决什么问题)
#### 1.1.2 State (状态): 图的记忆
#### 1.1.3 Nodes (节点): 工作单元
#### 1.1.4 Edges (边): 连接流程
### 1.2 第一个 LangGraph 应用
#### 1.2.1 定义 StateGraph
#### 1.2.2 添加节点 (Nodes)
#### 1.2.3 设置入口和出口 (Entry/Finish Point)
#### 1.2.4 编译与运行 (compile, stream)

## 第2章：构建动态流程 
### 2.1 条件分支
#### 2.1.1 条件边的使用
#### 2.1.2 实现一个简单的路由 Agent
### 2.2 循环与迭代
#### 2.2.1 在图中创建循环
#### 2.2.2 案例: 多轮问答或自我修正
      '''
)

print(response.output_text)

# from openai import OpenAI
# import os
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# response = client.responses.create(
#     model="gpt-4.1",  # or another supported model
#     input='''{
#       "title": "Pattern Recognition and Machine Learning",
#       "authors": [
#         "Christopher M. Bishop"
#       ] 这本书的完整目录是什么？（必须包含章节与每个章节下的小节，保留原有层级与顺序）''',
#     tools=[
#         {
#             "type": "web_search"
#         }
#     ]
# )

# import json
# print(json.dumps(response.output, default=lambda o: o.__dict__, indent=2))
