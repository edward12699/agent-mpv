"""文档检索工具。"""

from __future__ import annotations

from typing import Any

from langchain_core.tools import tool


@tool
def search_documents(query: str) -> list[dict[str, Any]]:
    """查询合同正文和文档内容。

    用于：
    - 违约责任
    - 付款条款
    - 合同义务
    - 正文细节

    不用于金额排序和结构化筛选。
    """
    from app.rag.retriever import get_retriever

    docs = get_retriever().invoke(query)
    return [
        {
            "content": doc.page_content,
            "source": doc.metadata.get("source"),
            "chunk_id": doc.metadata.get("chunk_id"),
        }
        for doc in docs
    ]
