from langchain_core.messages import HumanMessage

from app.agent_langchain import create_default_chat_model
from app.core.config import get_settings
from app.models import ContractAnswer


settings = get_settings()

llm = create_default_chat_model(settings)

structured_llm = llm.with_structured_output(
    ContractAnswer
)

result = structured_llm.invoke(
    [
        HumanMessage(
            content="""
            合同ID是3，
            合同金额是500000元。

            请分析这份合同。
            """
        )
    ]
)

print(type(result))
print(result)
print(result.model_dump())