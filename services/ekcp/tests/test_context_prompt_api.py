"""Context and prompt API tests: build context then generate a prompt."""

from __future__ import annotations

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from api.app import create_app
from api.dependencies import build_resources, get_resources
from config.settings import EkcpSettings

_CONTEXT = {
    "user_id": "analyst-1",
    "tenant_id": "tenant-a",
    "classification_clearance": "internal",
}
_KNOWLEDGE = [
    {
        "content": "Remote work is allowed two days per week.",
        "relevance_score": 0.92,
        "citation": {
            "document_id": "d1",
            "chunk_id": "c1",
            "source_path": "/docs/hr.md",
        },
    }
]


def _client(settings: EkcpSettings) -> AsyncClient:
    app = create_app(settings)
    resources = build_resources(settings)
    app.dependency_overrides[get_resources] = lambda: resources
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://ekcp.test")


@pytest.fixture
def settings() -> EkcpSettings:
    return EkcpSettings(_env_file=None)


async def test_build_context_then_generate_prompt(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        build = await client.post(
            "/context/build",
            headers={"X-Tenant-ID": "tenant-a"},
            json={
                "conversation_id": "conv-1",
                "user_intent": "What is the remote work policy?",
                "security_context": _CONTEXT,
                "conversation_history": ["hello", "what is the policy"],
                "knowledge": _KNOWLEDGE,
                "policy_constraints": ["Never disclose salary data."],
            },
        )
        assert build.status_code == httpx.codes.OK
        context_id = build.json()["context_id"]
        assert build.json()["selected_count"] >= 1

        generate = await client.post(
            "/prompt/generate",
            headers={"X-Tenant-ID": "tenant-a"},
            json={"context_id": context_id, "security_context": _CONTEXT},
        )
    assert generate.status_code == httpx.codes.OK
    body = generate.json()
    assert body["prompt_id"].startswith("prm-")
    assert body["validation_status"] == "valid"
    assert "remote work policy" in body["prompt_text"].lower()


async def test_build_context_requires_tenant(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.post(
            "/context/build",
            json={
                "conversation_id": "conv-1",
                "user_intent": "policy",
                "security_context": _CONTEXT,
            },
        )
    assert response.status_code == httpx.codes.BAD_REQUEST


async def test_generate_prompt_denies_tenant_mismatch(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.post(
            "/prompt/generate",
            headers={"X-Tenant-ID": "tenant-a"},
            json={
                "context_id": "ctx-x",
                "security_context": {**_CONTEXT, "tenant_id": "tenant-b"},
            },
        )
    assert response.status_code == httpx.codes.FORBIDDEN


async def test_generate_prompt_unknown_context_404(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.post(
            "/prompt/generate",
            headers={"X-Tenant-ID": "tenant-a"},
            json={"context_id": "ctx-missing", "security_context": _CONTEXT},
        )
    assert response.status_code == httpx.codes.NOT_FOUND
