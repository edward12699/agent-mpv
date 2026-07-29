import asyncio
import time

import httpx


URL = "http://127.0.0.1:8000/api/agent/chat"


async def ask(
    client: httpx.AsyncClient,
    question: str,
) -> None:
    started_at = time.perf_counter()

    response = await client.post(
        URL,
        json={"question": question},
    )

    elapsed = time.perf_counter() - started_at

    print(
        question,
        response.status_code,
        f"{elapsed:.2f}s",
    )


async def main() -> None:
    started_at = time.perf_counter()

    async with httpx.AsyncClient(timeout=90) as client:
        await asyncio.gather(
            ask(client, "找2023年的合同"),
            ask(client, "找金额最大的合同"),
        )

    total = time.perf_counter() - started_at
    print(f"总耗时：{total:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())