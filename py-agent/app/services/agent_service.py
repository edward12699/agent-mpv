from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any

from app.core.config import Settings, get_settings
from app.graph.contract_graph import get_contract_graph, initial_state


logger = logging.getLogger(__name__)


def build_steps_from_state(result: dict[str, Any]) -> list[dict[str, Any]]:
    """把 Graph 执行路径映射成 API 仍使用的 steps 结构。"""
    route = result.get("route") or ""
    question = result.get("question") or ""
    steps: list[dict[str, Any]] = []

    if route == "structured":
        steps.append(
            {
                "tool": "search_contract",
                "args": {},
                "result": result.get("contracts") or [],
            }
        )
        if result.get("need_rank"):
            steps.append(
                {
                    "tool": "rank_contracts",
                    "args": {"order": "desc"},
                    "result": result.get("ranked_result"),
                }
            )
    elif route == "document":
        steps.append(
            {
                "tool": "search_documents",
                "args": {"query": question},
                "result": result.get("retrieved_docs") or [],
            }
        )

    return steps


class AgentService:
    def __init__(
        self,
        graph=None,
        settings: Settings | None = None,
        agent=None,
    ):
        # agent 参数保留给旧 dependencies 注入，可忽略
        self.settings = settings or get_settings()
        self.graph = graph or get_contract_graph()
        self._agent = agent

    async def chat(
        self,
        question: str,
        thread_id: str | None = None,
        stream_debug: bool = False,
    ) -> dict[str, Any]:
        question = question.strip()
        thread_id = thread_id or str(uuid.uuid4())
        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }
        state = initial_state(question)
        start = time.time()
        logger.info(
            {
                "event": "agent_run_start",
                "question": question,
                "thread_id": thread_id,
            }
        )

        async with asyncio.timeout(self.settings.agent_timeout_seconds):
            if stream_debug or self.settings.debug:
                result = None
                async for event in self.graph.astream(
                    state,
                    config=config,
                    stream_mode="updates",
                ):
                    logger.info({"event": "graph_stream", "payload": event})
                    print(event)
                snapshot = await self.graph.aget_state(config)
                result = snapshot.values
            else:
                result = await self.graph.ainvoke(state, config=config)

        duration_ms = (time.time() - start) * 1000
        steps = build_steps_from_state(result)
        logger.info(
            {
                "event": "agent_finished",
                "duration_ms": round(duration_ms, 2),
                "route": result.get("route"),
                "tools": [step["tool"] for step in steps],
            }
        )

        return {
            "question": question,
            "answer": result.get("answer") or "",
            "steps": steps,
            "route": result.get("route"),
            "thread_id": thread_id,
            "need_rank": result.get("need_rank", False),
            "sources": result.get("retrieved_docs") or [],
        }
