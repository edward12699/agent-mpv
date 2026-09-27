"""合同 Agent Graph 节点。"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage

from app.core.config import get_settings
from app.graph.state import ContractAgentState
from app.rag.retriever import get_retriever
from app.tools.contract_tools import rank_contracts, search_contract


def analyze_node(state: ContractAgentState) -> dict[str, Any]:
    """规则版路由：先把 Graph 架构搭稳，再换成 LLM Router。"""
    question = state["question"]

    need_rank = "最大" in question or "最高" in question

    if any(
        keyword in question
        for keyword in ["违约", "付款方式", "条款", "责任", "正文"]
    ):
        route = "document"
    elif any(
        keyword in question
        for keyword in ["合同", "金额", "年份", "最大", "最高"]
    ):
        route = "structured"
    else:
        route = "unsupported"

    return {
        "route": route,
        "need_rank": need_rank,
    }


def search_node(state: ContractAgentState) -> dict[str, Any]:
    # Day 14：先跑通架构，年份/主体条件提取后续再补
    contracts = search_contract.invoke({})
    return {
        "contracts": [
            contract if isinstance(contract, dict) else contract.to_dict()
            for contract in contracts
        ]
    }


def rank_node(state: ContractAgentState) -> dict[str, Any]:
    result = rank_contracts.invoke(
        {
            "contracts": state["contracts"],
            "order": "desc",
        }
    )
    return {"ranked_result": result}


def retrieve_node(state: ContractAgentState) -> dict[str, Any]:
    docs = get_retriever().invoke(state["question"])
    return {
        "retrieved_docs": [
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source"),
                "chunk_id": doc.metadata.get("chunk_id"),
            }
            for doc in docs
        ]
    }


async def answer_node(state: ContractAgentState) -> dict[str, Any]:
    """LLM 只负责基于已准备好的业务数据生成答案，不负责流程决策。"""
    question = state["question"]
    route = state["route"]

    if route == "unsupported":
        return {"answer": "我当前只能处理合同相关问题。"}

    if route == "structured":
        context = {
            "contracts": state.get("contracts") or [],
            "ranked_result": state.get("ranked_result"),
            "need_rank": state.get("need_rank", False),
        }
    elif route == "document":
        context = {
            "documents": state.get("retrieved_docs") or [],
        }
    else:
        return {"answer": "我当前只能处理合同相关问题。"}

    from app.llm_factory import create_default_chat_model

    llm = create_default_chat_model(get_settings())
    context_text = json.dumps(context, ensure_ascii=False, indent=2)
    response = await llm.ainvoke(
        [
            HumanMessage(
                content=f"""你是合同分析助手。

用户问题：
{question}

系统已经完成了查询，下面是可靠的业务数据：

{context_text}

请仅根据这些数据回答。
不要编造不存在的信息。
如果资料不足，请明确说明无法确定。
如果数据来自 documents，请引用 source 或 chunk_id。
"""
            )
        ]
    )
    return {"answer": str(response.content)}
