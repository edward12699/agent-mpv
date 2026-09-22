"""
Week 1 / Day 6：Retriever 包装成 Tool，接回 Agent。

Agentic RAG 已经在 app/agent_langchain.py 里：
把 search_documents 放进 TOOLS，交给 create_agent。
模型自己决定要不要检索。这里只观察工具选择，并和普通 RAG 对比。
"""

import asyncio
import importlib.util
import time
from pathlib import Path

from app.agent_langchain import Agent, create_default_chat_model
from app.core.config import get_settings
from app.rag import get_retriever


day5_path = Path(__file__).resolve().parent / "day5_basic_rag.py"
_spec = importlib.util.spec_from_file_location("day5_basic_rag", day5_path)
_day5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_day5)
answer_with_rag = _day5.answer_with_rag


QUESTIONS = [
    "找2023年的合同",
    "找金额最大的合同",
    "合同违约责任是什么？",
    "付款方式是什么？",
    "2023年的合同里，违约责任是什么？",
    "今天天气怎么样？",
]


def print_agent_result(result: dict) -> None:
    print("\n" + "#" * 60)
    print("Question:", result["question"])
    print("#" * 60)
    steps = result["steps"]
    if not steps:
        print("tools: (未调用工具)")
    for index, step in enumerate(steps, start=1):
        print(f"[{index}] {step['tool']} args={step['args']}")
    print("\n--- Answer ---")
    print(result["answer"])


async def run_agent_questions() -> None:
    agent = Agent()
    for question in QUESTIONS:
        started = time.perf_counter()
        result = await agent.run(question)
        elapsed = time.perf_counter() - started
        print_agent_result(result)
        print(f"\n耗时: {elapsed:.1f}s  工具次数: {len(result['steps'])}")


def run_plain_rag(question: str) -> tuple[str, float]:
    llm = create_default_chat_model(get_settings())
    started = time.perf_counter()
    _docs, _context, answer = answer_with_rag(llm, get_retriever(), question)
    return answer, time.perf_counter() - started


async def compare_rag(question: str) -> None:
    print("\n" + "#" * 60)
    print("对比实验:", question)
    print("普通 RAG：固定 Retriever → LLM")
    print("Agentic RAG：同一个 Agent，search_documents 只是可选工具")
    print("#" * 60)

    plain_answer, plain_elapsed = run_plain_rag(question)
    print("\n--- 普通 RAG ---")
    print(plain_answer)
    print(f"耗时: {plain_elapsed:.1f}s  固定 1 次检索 + 1 次生成")

    started = time.perf_counter()
    result = await Agent().run(question)
    agent_elapsed = time.perf_counter() - started
    print("\n--- Agentic RAG ---")
    print("tools:", [step["tool"] for step in result["steps"]])
    print(result["answer"])
    print(f"耗时: {agent_elapsed:.1f}s  工具次数: {len(result['steps'])}")


async def async_main() -> None:
    print("Day 6 Agentic RAG")
    await run_agent_questions()
    await compare_rag("合同违约责任是什么？")
    print("\n" + "#" * 60)
    print("Day 6 完成：search_documents 已作为 Tool 交给 Agent")
    print("#" * 60)


if __name__ == "__main__":
    asyncio.run(async_main())
