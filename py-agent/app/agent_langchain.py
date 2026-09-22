import asyncio
import json
from typing import Any


from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from app.models import ContractAnswer
from .core.config import Settings, get_settings
from .tool import rank_contracts, search_contract, search_documents

import logging
import time


logger = logging.getLogger(__name__)


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
   不要自己从 rawText 里猜金额，优先使用工具返回的 amount 字段。
   amount 为 null 的合同不能参与金额排序。
   如果金额相同，amountConfidence=exact 优先于 approximate。

5. 最终回答必须基于工具返回的数据。

6. 如果 search_documents 没有找到可靠内容，
   明确回答“根据当前资料无法确定”。

7. 不允许编造不存在的合同条款。

8. 如果答案来自 search_documents，
   最终回答必须引用 source 或 chunk_id。

9. 严禁在同一轮同时调用 search_contract 和 rank_contracts。
   rank_contracts 的 contracts 参数必须来自上一轮 search_contract 的工具返回结果。
   如果没有拿到 search_contract 返回结果，不允许调用 rank_contracts。

10. 如果问题与合同无关（例如天气），不要调用任何合同工具，
    直接说明只能处理合同相关问题。
"""


TOOLS = [search_contract, rank_contracts, search_documents]




def create_default_chat_model(settings: Settings) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.agent_model,
        api_key=settings.api_key,
        base_url=settings.base_url,
        timeout=settings.llm_request_timeout_seconds,
        max_retries=settings.llm_max_retries,
    )


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
    def __init__(
        self,
        llm=None,
        settings: Settings | None = None,
        debug: bool | None = None,
    ):
        self.settings = settings or get_settings()
        self.llm = llm or create_default_chat_model(self.settings)
        self.agent = create_agent(
            model=self.llm,
            tools=TOOLS,
            system_prompt=SYSTEM_PROMPT,
            debug=self.settings.debug if debug is None else debug,
        )

    async def run(self, question: str) -> dict[str, Any]:
        start = time.time()
        logger.info({
            "event": "agent_run_start",
            "question": question,
        })
        structured_llm = self.llm.with_structured_output(
            ContractAnswer
        )

        async with asyncio.timeout(self.settings.agent_timeout_seconds):
            result = await self.agent.ainvoke({"messages": [HumanMessage(content=question)]})
            messages = result["messages"]
            duration = (
                time.time() - start
            ) * 1000
            
            logger.info(
                {
                    "event":"agent_finished",
                    "duration_ms":
                    round(duration,2),
                }
            )

            logger.info(
                {
                    "event":
                        "agent_tools",
                    "tools":
                        [
                            step["tool"]
                            for step in extract_steps(messages)
                        ]
                }
            )

            answer = extract_final_answer(messages)

            structured_answer = await structured_llm.ainvoke(
                [
                    HumanMessage(
                        content=f"""
                        用户问题：
                        {question}

                        Agent最终回答：
                        {answer}

                        请把结果转换成结构化合同分析结果。
                        """
                    )
                ]
            )

            return {
                "question": question,
                "steps": extract_steps(messages),
                "answer": answer,
                "structured_answer": structured_answer,
            }


async def run(question: str) -> dict[str, Any]:
    return await Agent().run(question)
