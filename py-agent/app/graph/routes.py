"""Graph 路由函数。"""

from app.graph.state import ContractAgentState


def route_after_analyze(state: ContractAgentState) -> str:
    return state["route"]


def route_after_search(state: ContractAgentState) -> str:
    if state["need_rank"]:
        return "rank"
    return "answer"
