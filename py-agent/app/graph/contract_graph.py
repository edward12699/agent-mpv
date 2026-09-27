"""合同 Agent LangGraph：可控 workflow。"""

from __future__ import annotations

from functools import lru_cache

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    analyze_node,
    answer_node,
    rank_node,
    retrieve_node,
    search_node,
)
from app.graph.routes import route_after_analyze, route_after_search
from app.graph.state import ContractAgentState


def build_contract_graph(checkpointer: InMemorySaver | None = None):
    builder = StateGraph(ContractAgentState)

    builder.add_node("analyze", analyze_node)
    builder.add_node("search", search_node)
    builder.add_node("rank", rank_node)
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("answer", answer_node)

    builder.add_edge(START, "analyze")
    builder.add_conditional_edges(
        "analyze",
        route_after_analyze,
        {
            "structured": "search",
            "document": "retrieve",
            "unsupported": "answer",
        },
    )
    builder.add_conditional_edges(
        "search",
        route_after_search,
        {
            "rank": "rank",
            "answer": "answer",
        },
    )
    builder.add_edge("rank", "answer")
    builder.add_edge("retrieve", "answer")
    builder.add_edge("answer", END)

    # 写操作（delete/update/send）未来可在此接入 interrupt/approval；
    # search / retrieve / rank 不需要审批。
    return builder.compile(checkpointer=checkpointer or InMemorySaver())


@lru_cache
def get_contract_graph():
    return build_contract_graph()


def initial_state(question: str) -> ContractAgentState:
    return {
        "messages": [],
        "question": question,
        "route": "",
        "contracts": [],
        "need_rank": False,
        "ranked_result": None,
        "retrieved_docs": [],
        "answer": "",
        "pending_approval": None,
    }
