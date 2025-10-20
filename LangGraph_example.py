from langgraph.graph import StateGraph, END
from typing import TypedDict

# 定义状态
class State(TypedDict):
    message: str

# 定义节点函数
def node1(state: State):
    return {"message": state["message"] + " processed by node1"}

def node2(state: State):
    return {"message": state["message"] + " → node2"}

# 构建图
workflow = StateGraph(State)
workflow.add_node("node1", node1)
workflow.add_node("node2", node2)
workflow.set_entry_point("node1")
workflow.add_edge("node1", "node2")
workflow.add_edge("node2", END)

# 编译并可视化
graph = workflow.compile()
print("Mermaid 图表：")
print(graph.get_graph().draw_mermaid())