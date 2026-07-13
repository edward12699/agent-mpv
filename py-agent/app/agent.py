import json

from .llm import TOOLS,llm
from .models import Contract
from .tools import rank_contracts, search_contract

from langchain.agents import creat_agent


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


def to_jsonable(value):
    if isinstance(value, Contract):
        return value.to_dict()
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    return value


class Agent:

    def __init__(self, llm):
        self.llm = llm


    def run(self, question):
        steps = []

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": question
            }
        ]


        for _ in range(5):

            response = self.llm.chat(
                messages=messages,
                tools=TOOLS
            )


            if response.tool_calls:

                messages.append(response.to_message())


                for call in response.tool_calls:

                    if call.name == "search_contract":

                        result = search_contract(
                            **call.arguments
                        )


                    elif call.name == "rank_contracts":

                        if "contracts" in call.arguments:
                            call.arguments["contracts"] = [
                                Contract(
                                    id=contract["id"],
                                    party_a=contract.get("partyA"),
                                    party_b=contract.get("partyB"),
                                    amount=contract.get("amount"),
                                    amount_confidence=contract.get("amountConfidence", "unknown"),
                                    year=contract.get("year"),
                                    raw_text=contract["rawText"],
                                )
                                for contract in call.arguments["contracts"]
                            ]
                        result = rank_contracts(
                            **call.arguments
                        )

                    else:
                        raise ValueError(f"未知工具：{call.name}")

                    jsonable_result = to_jsonable(result)
                    steps.append(
                        {
                            "tool": call.name,
                            "args": to_jsonable(call.arguments),
                            "result": jsonable_result,
                        }
                    )

                    messages.append(
                        {
                            "role":"tool",
                            "tool_call_id": call.id,
                            "content": json.dumps(jsonable_result, ensure_ascii=False)
                        }
                    )

            else:

                return {
                    "question": question,
                    "steps": steps,
                    "finalAnswer": response.content,
                }

        raise RuntimeError("Agent 超过最大工具调用轮数")
