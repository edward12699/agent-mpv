"""兼容层：LLM 工厂、TOOLS 导出，以及基于 LangGraph 的 Agent 入口。"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AIMessage, ToolMessage

from app.core.config import Settings, get_settings
from app.llm_factory import create_default_chat_model
from app.services.agent_service import AgentService
from app.tools.contract_tools import rank_contracts, search_contract
from app.tools.document_tools import search_documents

SYSTEM_PROMPT = """
你是一个合同分析 Agent。

规则：

1. 如果用户询问合同列表、年份、金额、筛选、排序等结构化信息，
   优先调用 search_contract。

2. 如果用户询问合同条款、违约责任、付款方式、合同正文内容，
   调用 search_documents。

3. 如果用户要找金额最大、最高费用、最高价款：
   必须先 search_contract，再 rank_contracts。

4. 不要自己猜测合同内容。

5. 最终回答必须基于工具返回的数据。

6. 如果 search_documents 没有找到可靠内容，
   明确回答“根据当前资料无法确定”。

7. 不允许编造不存在的合同条款。

8. 如果答案来自 search_documents，
   最终回答必须引用 source 或 chunk_id。

9. 如果问题与合同无关（例如天气），不要调用任何合同工具，
    直接说明只能处理合同相关问题。
"""

TOOLS = [search_contract, rank_contracts, search_documents]


def json_loads(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def extract_steps(messages: list[Any]) -> list[dict[str, Any]]:
    tool_calls_by_id: dict[str, dict[str, Any]] = {}
    steps: list[dict[str, Any]] = []

    for message in messages:
        if isinstance(message, AIMessage):
            for call in message.tool_calls:
                tool_calls_by_id[call["id"]] = {
                    "tool": call["name"],
                    "args": call.get("args", {}),
                }
        elif isinstance(message, ToolMessage):
            call = tool_calls_by_id.get(message.tool_call_id)
            if call:
                steps.append(
                    {
                        "tool": call["tool"],
                        "args": call["args"],
                        "result": json_loads(message.content),
                    }
                )

    return steps


def extract_final_answer(messages: list[Any]) -> str:
    for message in reversed(messages):
        if isinstance(message, AIMessage) and not message.tool_calls:
            return str(message.content or "")
    return ""


class Agent:
    """v2：内部走 LangGraph Contract Agent。"""

    def __init__(
        self,
        llm=None,
        settings: Settings | None = None,
        debug: bool | None = None,
        service: AgentService | None = None,
    ):
        self.settings = settings or get_settings()
        self.llm = llm or create_default_chat_model(self.settings)
        self.debug = self.settings.debug if debug is None else debug
        self.service = service or AgentService(settings=self.settings)

    async def run(
        self,
        question: str,
        thread_id: str = "default",
    ) -> dict[str, Any]:
        return await self.service.chat(
            question=question,
            thread_id=thread_id,
            stream_debug=self.debug,
        )


async def run(question: str, thread_id: str = "default") -> dict[str, Any]:
    return await Agent().run(question, thread_id=thread_id)
