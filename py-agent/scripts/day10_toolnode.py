from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from app.agent_langchain import TOOLS, create_default_chat_model
from app.core.config import get_settings


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


settings = get_settings()

llm = create_default_chat_model(
    settings
)

llm_with_tools = llm.bind_tools(
    TOOLS
)


def call_model(
    state: AgentState,
) -> dict:
    response = llm_with_tools.invoke(
        state["messages"]
    )

    return {
        "messages": [response]
    }


builder = StateGraph(
    AgentState
)

builder.add_node(
    "agent",
    call_model,
)

builder.add_node(
    "tools",
    ToolNode(TOOLS),
)

builder.add_edge(
    START,
    "agent",
)

builder.add_conditional_edges(
    "agent",
    tools_condition,
    {
        "tools": "tools",
        END: END,
    },
)

builder.add_edge(
    "tools",
    "agent",
)

graph = builder.compile()