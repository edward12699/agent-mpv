from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_agent
from app.api.main import app


class SuccessAgent:
    """模拟正常运行的 Agent。"""

    async def run(self, question: str) -> dict[str, Any]:
        return {
            "question": question,
            "steps": [
                {
                    "tool": "search_contract",
                    "args": {
                        "year": "2023",
                    },
                    "result": [
                        {
                            "id": 1,
                            "year": "2023",
                            "amount": 100000,
                        }
                    ],
                }
            ],
            "answer": "找到 1 条 2023 年合同",
        }


class ErrorAgent:
    """模拟 Agent 发生普通异常。"""

    async def run(self, question: str) -> dict[str, Any]:
        raise RuntimeError("模拟模型服务异常")


class TimeoutAgent:
    """模拟 Agent 整体执行超时。"""

    async def run(self, question: str) -> dict[str, Any]:
        raise TimeoutError("模拟 Agent 超时")


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_dependency_overrides() -> Generator[None, None, None]:
    """
    每条测试前后清理依赖覆盖，避免测试之间互相污染。
    """
    app.dependency_overrides.clear()

    yield

    app.dependency_overrides.clear()


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }



def test_chat_success(client: TestClient) -> None:
    # Arrange：用假 Agent 替换正式 Agent
    app.dependency_overrides[get_agent] = lambda: SuccessAgent()

    # Act：发送请求
    response = client.post(
        "/api/agent/chat",
        json={
            "question": "找2023年的合同",
        },
    )

    # Assert：验证结果
    assert response.status_code == 200

    assert response.json() == {
        "question": "找2023年的合同",
        "steps": [
            {
                "tool": "search_contract",
                "args": {
                    "year": "2023",
                },
                "result": [
                    {
                        "id": 1,
                        "year": "2023",
                        "amount": 100000,
                    }
                ],
            }
        ],
        "answer": "找到 1 条 2023 年合同",
    }


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {
            "question": "",
        },
        {
            "question": "x" * 2001,
        },
    ],
)
def test_chat_validation_error(
    client: TestClient,
    payload: dict[str, Any],
) -> None:
    app.dependency_overrides[get_agent] = lambda: SuccessAgent()

    response = client.post(
        "/api/agent/chat",
        json=payload,
    )

    assert response.status_code == 422
    assert "detail" in response.json()



def test_chat_agent_error(client: TestClient) -> None:
    app.dependency_overrides[get_agent] = lambda: ErrorAgent()

    response = client.post(
        "/api/agent/chat",
        json={
            "question": "找金额最大的合同",
        },
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Agent 执行失败，请稍后重试",
    }



def test_chat_agent_timeout(client: TestClient) -> None:
    app.dependency_overrides[get_agent] = lambda: TimeoutAgent()

    response = client.post(
        "/api/agent/chat",
        json={
            "question": "找金额最大的合同",
        },
    )

    assert response.status_code == 504
    assert response.json() == {
        "detail": "Agent 响应超时，请稍后重试",
    }