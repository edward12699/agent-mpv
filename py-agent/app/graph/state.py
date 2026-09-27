from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ContractAgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    question: str
    route: str
    contracts: list[dict]
    need_rank: bool
    ranked_result: dict | None
    retrieved_docs: list[dict]
    answer: str
    # 预留：未来 delete/update/send 等写操作可走 approval → interrupt → resume
    pending_approval: str | None
