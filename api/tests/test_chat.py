"""
Integration tests for Chat API routes.
"""
import pytest
from httpx import AsyncClient


class TestChat:
    """Test POST /api/v1/chat/."""

    @pytest.mark.integration
    async def test_chat_send_message(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/api/v1/chat/",
            json={
                "message": "What is machine learning?",
                "workspace_id": "00000000-0000-0000-0000-000000000001",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "conversation_id" in data
        assert "message_id" in data
        assert "content" in data
        assert isinstance(data["content"], str)
        assert len(data["content"]) > 0

    @pytest.mark.integration
    async def test_chat_continuation(self, client: AsyncClient, auth_headers: dict):
        """Test sending follow-up in same conversation."""
        resp1 = await client.post(
            "/api/v1/chat/",
            json={
                "message": "Hello",
                "workspace_id": "00000000-0000-0000-0000-000000000001",
            },
            headers=auth_headers,
        )
        conv_id = resp1.json()["conversation_id"]

        resp2 = await client.post(
            "/api/v1/chat/",
            json={
                "message": "Follow up question",
                "workspace_id": "00000000-0000-0000-0000-000000000001",
                "conversation_id": conv_id,
            },
            headers=auth_headers,
        )
        assert resp2.status_code == 200
        assert resp2.json()["conversation_id"] == conv_id

    @pytest.mark.integration
    async def test_chat_with_rag(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/api/v1/chat/",
            json={
                "message": "Search my docs",
                "workspace_id": "00000000-0000-0000-0000-000000000001",
                "use_retrieval": True,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "citations" in data

    @pytest.mark.integration
    async def test_chat_with_agent(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/api/v1/chat/",
            json={
                "message": "Calculate 2+2",
                "workspace_id": "00000000-0000-0000-0000-000000000001",
                "use_agent": True,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200

    @pytest.mark.edge
    async def test_chat_unauthenticated(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/chat/",
            json={
                "message": "Hello",
                "workspace_id": "00000000-0000-0000-0000-000000000001",
            },
        )
        assert resp.status_code in (401, 403)

    @pytest.mark.edge
    async def test_chat_empty_message(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/api/v1/chat/",
            json={
                "message": "",
                "workspace_id": "00000000-0000-0000-0000-000000000001",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    @pytest.mark.edge
    async def test_chat_missing_workspace(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/api/v1/chat/",
            json={"message": "Hello"},
            headers=auth_headers,
        )
        assert resp.status_code == 422


class TestConversations:
    """Test GET /api/v1/chat/conversations."""

    @pytest.mark.integration
    async def test_list_conversations(self, client: AsyncClient, auth_headers: dict):
        # Create a conversation
        await client.post(
            "/api/v1/chat/",
            json={
                "message": "Test",
                "workspace_id": "00000000-0000-0000-0000-000000000001",
            },
            headers=auth_headers,
        )
        resp = await client.get(
            "/api/v1/chat/conversations?workspace_id=00000000-0000-0000-0000-000000000001",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.integration
    async def test_get_conversation_detail(self, client: AsyncClient, auth_headers: dict):
        resp1 = await client.post(
            "/api/v1/chat/",
            json={
                "message": "Detail test",
                "workspace_id": "00000000-0000-0000-0000-000000000001",
            },
            headers=auth_headers,
        )
        conv_id = resp1.json()["conversation_id"]

        resp = await client.get(
            f"/api/v1/chat/conversations/{conv_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == conv_id
        assert "messages" in data

    @pytest.mark.edge
    async def test_get_nonexistent_conversation(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get(
            "/api/v1/chat/conversations/00000000-0000-0000-0000-999999999999",
            headers=auth_headers,
        )
        assert resp.status_code == 404
