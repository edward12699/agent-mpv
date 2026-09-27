"""
Week 2 / Day 14：合同 Agent v2 总重构验收。

验证：
1. 规则路由是否正确
2. Graph 节点流是否符合预期
3. AgentService 端到端回答
"""

from __future__ import annotations

import asyncio

from app.graph.contract_graph import get_contract_graph, initial_state
from app.graph.nodes import analyze_node
from app.services.agent_service import AgentService


CASES = [
    {
        "question": "找一下所有合同",
        "expected_route": "structured",
        "expected_nodes": ["analyze", "search", "answer"],
        "expected_need_rank": False,
    },
    {
        "question": "找金额最高的合同",
        "expected_route": "structured",
        "expected_nodes": ["analyze", "search", "rank", "answer"],
        "expected_need_rank": True,
    },
    {
        "question": "合同违约责任是什么？",
        "expected_route": "document",
        "expected_nodes": ["analyze", "retrieve", "answer"],
        "expected_need_rank": False,
    },
    {
        "question": "付款方式是什么？",
        "expected_route": "document",
        "expected_nodes": ["analyze", "retrieve", "answer"],
        "expected_need_rank": False,
    },
    {
        "question": "今天天气怎么样？",
        "expected_route": "unsupported",
        "expected_nodes": ["analyze", "answer"],
        "expected_need_rank": False,
    },
]


def check_analyze() -> None:
    print("#" * 60)
    print("1) analyze_node 路由检查")
    print("#" * 60)
    for case in CASES:
        result = analyze_node(
            {
                "messages": [],
                "question": case["question"],
                "route": "",
                "contracts": [],
                "need_rank": False,
                "ranked_result": None,
                "retrieved_docs": [],
                "answer": "",
                "pending_approval": None,
            }
        )
        ok = (
            result["route"] == case["expected_route"]
            and result["need_rank"] == case["expected_need_rank"]
        )
        mark = "OK" if ok else "FAIL"
        print(
            f"[{mark}] {case['question']} -> "
            f"route={result['route']} need_rank={result['need_rank']}"
        )


async def check_stream_paths() -> None:
    print("\n" + "#" * 60)
    print("2) Graph astream 节点路径")
    print("#" * 60)
    graph = get_contract_graph()

    for index, case in enumerate(CASES, start=1):
        question = case["question"]
        config = {"configurable": {"thread_id": f"day14-stream-{index}"}}
        nodes: list[str] = []

        # unsupported / structured 的 analyze→search/rank 不依赖 LLM；
        # document/structured 的 answer 会调 LLM。这里只收集节点名。
        async for event in graph.astream(
            initial_state(question),
            config=config,
            stream_mode="updates",
        ):
            nodes.extend(event.keys())

        expected = case["expected_nodes"]
        ok = nodes == expected
        mark = "OK" if ok else "FAIL"
        print(f"[{mark}] {question}")
        print(f"  expected: {expected}")
        print(f"  actual:   {nodes}")


async def check_service() -> None:
    print("\n" + "#" * 60)
    print("3) AgentService 端到端")
    print("#" * 60)
    service = AgentService()

    for index, case in enumerate(CASES, start=1):
        result = await service.chat(
            case["question"],
            thread_id=f"day14-chat-{index}",
            stream_debug=False,
        )
        print("-" * 50)
        print("Q:", case["question"])
        print("route:", result.get("route"))
        print("steps:", [step["tool"] for step in result["steps"]])
        print("A:", result["answer"][:200])


async def main() -> None:
    check_analyze()
    await check_stream_paths()
    await check_service()
    print("\n" + "#" * 60)
    print("Day 14 验收脚本跑完")
    print("#" * 60)


if __name__ == "__main__":
    asyncio.run(main())
