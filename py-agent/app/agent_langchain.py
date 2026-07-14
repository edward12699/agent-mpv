import json
import os
from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI

from .tool import rank_contracts, search_contract


SYSTEM_PROMPT = """
你是一个合同分析 Agent。

规则：
1. 涉及合同、金额、日期、筛选、比较的问题，必须先调用 search_contract
2. 如果用户要找最大金额、最高费用、最高价款，必须在 search_contract 之后调用 rank_contracts
3. 不要自己从 rawText 里猜金额，优先使用工具返回的 amount 字段
4. amount 为 null 的合同不能参与金额排序
5. 如果金额相同，amountConfidence=exact 优先于 approximate
6. 最终回答必须基于工具返回结果
7. 严禁在同一轮同时调用 search_contract 和 rank_contracts
8. rank_contracts 的 contracts 参数必须来自上一轮 search_contract 的工具返回结果
9. 如果没有拿到 search_contract 返回结果，不允许调用 rank_contracts
"""


TOOLS = [search_contract, rank_contracts]


def create_default_chat_model():
    api_key = os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("请设置 DASHSCOPE_API_KEY 或 OPENAI_API_KEY 后运行 LangChain Agent")

    model = os.environ.get("PY_AGENT_MODEL", "qwen-plus")
    base_url = os.environ.get("OPENAI_BASE_URL")
    if os.environ.get("DASHSCOPE_API_KEY") and not base_url:
        base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    return ChatOpenAI(model=model, api_key=api_key, base_url=base_url)


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
    def __init__(self, llm=None, debug: bool = False):
        self.llm = llm or create_default_chat_model()
        self.agent = create_agent(
            model=self.llm,
            tools=TOOLS,
            system_prompt=SYSTEM_PROMPT,
            debug=debug,
        )

    def run(self, question: str) -> dict[str, Any]:
        result = self.agent.invoke({"messages": [HumanMessage(content=question)]})
        messages = result["messages"]

        # for msg in messages:
        #     print("================")
        #     print(type(msg))
        #     print(msg)

        return {
            "question": question,
            "steps": extract_steps(messages),
            "finalAnswer": extract_final_answer(messages),
        }


def run(question: str) -> dict[str, Any]:
    return Agent().run(question)
