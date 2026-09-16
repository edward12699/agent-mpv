import json

from app.agent_langchain import (
    SYSTEM_PROMPT,
    TOOLS,
    create_default_chat_model,
)
from app.tool import (search_contract,to_jsonable,rank_contracts)
from langchain_core.messages import HumanMessage, SystemMessage
from app.core.config import get_settings
from app.models import ContractAnswer


def inspect_model_decision(question: str) -> None:
    settings = get_settings()
    model = create_default_chat_model(settings)

    model_with_tools = model.bind_tools(TOOLS)

    response = model_with_tools.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=question),
        ]
    )

    print("=" * 80)
    print("问题：", question)
    print("普通文字：", response.content)
    print("工具调用：")

    for call in response.tool_calls:
        print(
            {
                "id": call["id"],
                "name": call["name"],
                "args": call["args"],
            }
        )

def execute_first_tool_call(
    question: str,
) -> None:
    settings = get_settings()
    model = create_default_chat_model(settings)
    model_with_tools = model.bind_tools(TOOLS)

    response = model_with_tools.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=question),
        ]
    )

    tool_map = {
        current_tool.name: current_tool
        for current_tool in TOOLS
    }

    if not response.tool_calls:
        print("模型没有选择工具：", response.content)
        return

    for call in response.tool_calls:
        tool_name = call["name"]
        tool_args = call["args"]

        selected_tool = tool_map.get(tool_name)

        if selected_tool is None:
            raise ValueError(
                f"未知工具：{tool_name}"
            )

        result: Any = selected_tool.invoke(
            tool_args
        )

        print("工具：", tool_name)
        print("参数：", tool_args)
        print(
            "结果：",
            json.dumps(
                to_jsonable(result),
                ensure_ascii=False,
                indent=2,
            ),
        )

def inspect_tools() -> None:
    for current_tool in TOOLS:
        print("=" * 80)
        print("name:")
        print(current_tool.name)

        print("\ndescription:")
        print(current_tool.description)

        print("\ninput schema:")
        schema = current_tool.get_input_schema().model_json_schema()
        print(
            json.dumps(
                schema,
                ensure_ascii=False,
                indent=2,
            )
        )



def invoke_tool_directly() -> None:
    result = search_contract.invoke(
        {
            "year": "2023",
        }
    )

    print(result)

questions = [
    "你好，介绍一下你自己",
    "找2023年的合同",
    "找金额最高的合同",
    "删除ID为3的合同",
]


if __name__ == "__main__":
    # inspect_tools()
    # invoke_tool_directly()
    # inspect_model_decision(
    #     "找2023年的合同"
    # )

    for question in questions:
        inspect_model_decision(question)
