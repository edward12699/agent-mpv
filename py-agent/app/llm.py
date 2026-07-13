import json
import re
from dataclasses import dataclass
from typing import Any, Optional
from langchain_openai import ChatOpenAI


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    role: str
    content: Optional[str]
    tool_calls: list[ToolCall]

    def to_message(self):
        message: dict[str, Any] = {
            "role": self.role,
            "content": self.content,
        }
        if self.tool_calls:
            message["tool_calls"] = [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.name,
                        "arguments": json.dumps(call.arguments, ensure_ascii=False),
                    },
                }
                for call in self.tool_calls
            ]
        return message


class OpenAICompatibleLLM:
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        model: str = "qwen-plus",
    ):
        from openai import OpenAI

        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def chat(self, messages, tools):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        message = response.choices[0].message
        tool_calls = []

        for call in message.tool_calls or []:
            tool_calls.append(
                ToolCall(
                    id=call.id,
                    name=call.function.name,
                    arguments=json.loads(call.function.arguments or "{}"),
                )
            )

        return LLMResponse(
            role=message.role,
            content=message.content,
            tool_calls=tool_calls,
        )


class RuleBasedLLM:
    def chat(self, messages, tools):
        last_message = messages[-1]

        if last_message["role"] == "tool":
            result = json.loads(last_message["content"])
            if isinstance(result, list) and self._needs_ranking(messages):
                return LLMResponse(
                    role="assistant",
                    content=None,
                    tool_calls=[
                        ToolCall(
                            id="call_rank_contracts",
                            name="rank_contracts",
                            arguments={"contracts": result, "order": "desc"},
                        )
                    ],
                )

            if isinstance(result, dict) and "topContract" in result:
                top_contract = result["topContract"]
                answer = (
                    f"最高金额合同 ID {top_contract['id']}"
                    if top_contract
                    else "未找到可排序合同"
                )
                return LLMResponse(role="assistant", content=answer, tool_calls=[])

            if isinstance(result, list):
                return LLMResponse(
                    role="assistant",
                    content=f"找到 {len(result)} 条合同",
                    tool_calls=[],
                )

        question = self._last_user_question(messages)
        return LLMResponse(
            role="assistant",
            content=None,
            tool_calls=[
                ToolCall(
                    id="call_search_contract",
                    name="search_contract",
                    arguments=self._search_arguments(question),
                )
            ],
        )

    def _last_user_question(self, messages):
        for message in reversed(messages):
            if message["role"] == "user":
                return message["content"]
        return ""

    def _needs_ranking(self, messages):
        question = self._last_user_question(messages)
        return "最大" in question or "最高" in question

    def _search_arguments(self, question):
        arguments: dict[str, Any] = {}

        exclude_match = re.search(r"不是\s*(20\d{2})|非\s*(20\d{2})|排除\s*(20\d{2})", question)
        if exclude_match:
            arguments["exclude_year"] = next(group for group in exclude_match.groups() if group)
        else:
            year_match = re.search(r"(20\d{2})", question)
            if year_match:
                arguments["year"] = year_match.group(1)

        min_match = re.search(r"(?:超过|大于|高于)(\d+)\s*万?", question)
        if min_match:
            amount = int(min_match.group(1))
            arguments["min_amount"] = amount * 10000 if "万" in min_match.group(0) else amount

        if "最大" in question or "最高" in question:
            arguments["compare"] = "max"

        if any(keyword in question for keyword in ["金额", "费用", "价款", "合同总价"]):
            arguments["need_amount"] = True

        return arguments


def create_default_llm():
    import os

    if os.environ.get("PY_AGENT_LLM") != "remote":
        return RuleBasedLLM()

    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        return RuleBasedLLM()

    # return OpenAICompatibleLLM(
    #     api_key=api_key,
    #     base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    #     model=os.environ.get("PY_AGENT_MODEL", "qwen-plus"),
    # )

    return ChatOpenAI(
        model=os.environ.get("PY_AGENT_MODEL", "qwen-plus"),
        api_key=api_key,
        api_base="https://dashscope.aliyuncs.com/compatible-mode/v1
    )

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_contract",
            "description": "查询合同数据。当用户问题涉及合同、金额、日期、比较、筛选时必须调用",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {
                        "type": "string",
                        "description": "需要包含的年份，例如 2023",
                    },
                    "exclude_year": {
                        "type": "string",
                        "description": "需要排除的年份，例如 2024",
                    },
                    "need_amount": {
                        "type": "boolean",
                        "description": "是否要求合同中必须包含金额字段",
                    },
                    "compare": {
                        "type": "string",
                        "enum": ["max"],
                        "description": "是否要做比较，例如最大金额",
                    },
                    "min_amount": {
                        "type": "number",
                        "description": "最小金额阈值，例如 200000",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rank_contracts",
            "description": "对已检索到的结构化合同按金额排序，用于找最大金额、最高费用、最高合同价款等问题",
            "parameters": {
                "type": "object",
                "properties": {
                    "contracts": {
                        "type": "array",
                        "description": "结构化合同数组，必须来自上一轮 search_contract 的工具返回结果",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "number"},
                                "amount": {"type": ["number", "null"]},
                                "amountConfidence": {
                                    "type": "string",
                                    "enum": ["exact", "approximate", "unknown"],
                                },
                                "year": {"type": ["string", "null"]},
                                "partyA": {"type": ["string", "null"]},
                                "partyB": {"type": ["string", "null"]},
                                "rawText": {"type": "string"},
                            },
                            "required": ["id", "amount", "amountConfidence", "rawText"],
                        },
                    },
                    "order": {
                        "type": "string",
                        "enum": ["desc", "asc"],
                        "description": "排序方向，找最大金额用 desc",
                    },
                },
                "required": ["contracts", "order"],
            },
        },
    },
]
