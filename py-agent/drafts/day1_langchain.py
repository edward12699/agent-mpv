import os
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
)
from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[1] / ".env")

api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    raise RuntimeError("请在 py-agent/.env 中设置 DASHSCOPE_API_KEY")


def main() -> None:
    llm = ChatOpenAI(
        model=os.getenv("PY_AGENT_MODEL", "qwen-plus"),
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    messages = [
        SystemMessage(
            content="你是一个合同助手"
        ),
        HumanMessage(
            content="你好，介绍一下自己"
        )
    ]

    response = llm.invoke(messages)

    print(type(response))
    print(response.content)
    print(response)


if __name__ == "__main__":
    main()
