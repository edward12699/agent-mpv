from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_agent_service
from app.api.main import app


class SuccessAgentService:
    """模拟正常运行的 Agent Service。"""

    async def chat(self, question: str) -> dict[str, Any]:
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


class ErrorAgentService:
    """模拟 Agent Service 发生普通异常。"""

    async def chat(self, question: str) -> dict[str, Any]:
        raise RuntimeError("模拟模型服务异常")


class TimeoutAgentService:
    """模拟 Agent Service 整体执行超时。"""

    async def chat(self, question: str) -> dict[str, Any]:
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
        "version": "0.1.0",
    }



def test_chat_success(client: TestClient) -> None:
    app.dependency_overrides[get_agent_service] = lambda: SuccessAgentService()

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
    app.dependency_overrides[get_agent_service] = lambda: SuccessAgentService()

    response = client.post(
        "/api/agent/chat",
        json=payload,
    )

    assert response.status_code == 422
    assert "detail" in response.json()



def test_chat_agent_error(client: TestClient) -> None:
    app.dependency_overrides[get_agent_service] = lambda: ErrorAgentService()

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
    app.dependency_overrides[get_agent_service] = lambda: TimeoutAgentService()

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

def test_request_id(
    client
):
    response = client.get("/health")

    assert (
        "X-Request-ID"
        in response.headers
    )


def test_cors_preflight(client: TestClient) -> None:
    response = client.options(
        "/api/agent/chat",
        headers={
            "Origin": "http://localhost:3002",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "http://localhost:3002"
    )
