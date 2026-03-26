"""
Edge case and stress tests for critical service paths.
"""
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestEdgeCasesAuth:
    """Edge cases for authentication flows."""

    @pytest.mark.edge
    async def test_sql_injection_in_email(self, client):
        resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "' OR 1=1 --",
                "password": "whatever",
            },
        )
        # Should fail validation, not SQL injection
        assert resp.status_code in (401, 422)

    @pytest.mark.edge
    async def test_xss_in_full_name(self, client):
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"xss-{uuid.uuid4().hex[:6]}@test.com",
                "password": "ValidPass123!",
                "full_name": "<script>alert('xss')</script>",
            },
        )
        if resp.status_code == 201:
            data = resp.json()
            # Name should be stored raw (sanitization on frontend), but not executed
            assert "script" in data.get("full_name", "").lower() or resp.status_code == 422

    @pytest.mark.edge
    async def test_unicode_bombing_in_password(self, client):
        """Unicode normalization edge case."""
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"unicode-{uuid.uuid4().hex[:6]}@test.com",
                "password": "Password1!" + "\u0000" * 100,
                "full_name": "Null Injector",
            },
        )
        # Should handle gracefully
        assert resp.status_code in (201, 422, 400)

    @pytest.mark.edge
    async def test_concurrent_registration_same_email(self, client):
        """Race condition: register same email twice rapidly."""
        import asyncio

        email = f"race-{uuid.uuid4().hex[:6]}@test.com"
        data = {"email": email, "password": "RacePass123!", "full_name": "Racer"}

        results = await asyncio.gather(
            client.post("/api/v1/auth/register", json=data),
            client.post("/api/v1/auth/register", json=data),
            return_exceptions=True,
        )
        statuses = [r.status_code for r in results if not isinstance(r, Exception)]
        # At least one should succeed, one should conflict
        assert 201 in statuses or 200 in statuses


class TestEdgeCasesKnowledge:
    """Edge cases for knowledge/document operations."""

    @pytest.mark.edge
    async def test_upload_zero_byte_file(self, client, auth_headers):
        import io
        files = {"file": ("empty.txt", io.BytesIO(b""), "text/plain")}
        resp = await client.post(
            "/api/v1/knowledge/documents/upload",
            files=files,
            data={"workspace_id": "00000000-0000-0000-0000-000000000001"},
            headers=auth_headers,
        )
        # Should handle gracefully
        assert resp.status_code in (200, 201, 400, 422)

    @pytest.mark.edge
    async def test_upload_file_with_special_characters_name(self, client, auth_headers):
        import io
        files = {"file": ("résumé (1).txt", io.BytesIO(b"content"), "text/plain")}
        resp = await client.post(
            "/api/v1/knowledge/documents/upload",
            files=files,
            data={"workspace_id": "00000000-0000-0000-0000-000000000001"},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 201)

    @pytest.mark.edge
    async def test_search_with_special_characters(self, client, auth_headers):
        resp = await client.post(
            "/api/v1/knowledge/search",
            json={
                "query": 'SELECT * FROM users; DROP TABLE chunks; --',
                "workspace_id": "00000000-0000-0000-0000-000000000001",
            },
            headers=auth_headers,
        )
        # Should not cause SQL injection
        assert resp.status_code in (200, 422)


class TestEdgeCasesChat:
    """Edge cases for chat operations."""

    @pytest.mark.edge
    async def test_chat_very_long_message(self, client, auth_headers):
        resp = await client.post(
            "/api/v1/chat/",
            json={
                "message": "A" * 50000,
                "workspace_id": "00000000-0000-0000-0000-000000000001",
            },
            headers=auth_headers,
        )
        # Should handle or reject gracefully
        assert resp.status_code in (200, 400, 422, 413)

    @pytest.mark.edge
    async def test_chat_message_with_only_whitespace(self, client, auth_headers):
        resp = await client.post(
            "/api/v1/chat/",
            json={
                "message": "   \n\t  ",
                "workspace_id": "00000000-0000-0000-0000-000000000001",
            },
            headers=auth_headers,
        )
        assert resp.status_code in (200, 422)

    @pytest.mark.edge
    async def test_chat_invalid_conversation_id(self, client, auth_headers):
        resp = await client.post(
            "/api/v1/chat/",
            json={
                "message": "Hello",
                "workspace_id": "00000000-0000-0000-0000-000000000001",
                "conversation_id": "not-a-uuid",
            },
            headers=auth_headers,
        )
        assert resp.status_code in (422, 400, 404)

    @pytest.mark.edge
    async def test_chat_negative_temperature(self, client, auth_headers):
        resp = await client.post(
            "/api/v1/chat/",
            json={
                "message": "Test",
                "workspace_id": "00000000-0000-0000-0000-000000000001",
                "temperature": -1.0,
            },
            headers=auth_headers,
        )
        assert resp.status_code in (200, 422)


class TestEdgeCasesEval:
    """Edge cases for evaluation operations."""

    @pytest.mark.edge
    async def test_create_dataset_very_long_name(self, client, auth_headers):
        resp = await client.post(
            "/api/v1/eval/datasets",
            json={"name": "A" * 1000},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 201, 422, 400)

    @pytest.mark.edge
    async def test_run_experiment_on_empty_dataset(self, client, auth_headers):
        # Create empty dataset
        ds_resp = await client.post(
            "/api/v1/eval/datasets",
            json={"name": "empty-ds"},
            headers=auth_headers,
        )
        ds_id = ds_resp.json()["id"]

        # Create experiment
        exp_resp = await client.post(
            "/api/v1/eval/experiments",
            json={"name": "empty-exp", "dataset_id": ds_id},
            headers=auth_headers,
        )
        exp_id = exp_resp.json()["id"]

        # Run - should handle empty dataset gracefully
        resp = await client.post(
            "/api/v1/eval/experiments/run",
            json={"experiment_id": exp_id},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 202, 400)


class TestEdgeCasesFeedback:
    """Edge cases for feedback operations."""

    @pytest.mark.edge
    async def test_feedback_nonexistent_message(self, client, auth_headers):
        resp = await client.post(
            "/api/v1/feedback/",
            json={
                "message_id": "00000000-0000-0000-0000-999999999999",
                "rating": "thumbs_up",
            },
            headers=auth_headers,
        )
        # May succeed (no FK check) or fail
        assert resp.status_code in (200, 201, 404, 400)

    @pytest.mark.edge
    async def test_feedback_invalid_rating(self, client, auth_headers):
        resp = await client.post(
            "/api/v1/feedback/",
            json={
                "message_id": "00000000-0000-0000-0000-000000000001",
                "rating": "five_stars",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    @pytest.mark.edge
    async def test_feedback_very_long_comment(self, client, auth_headers):
        resp = await client.post(
            "/api/v1/feedback/",
            json={
                "message_id": "00000000-0000-0000-0000-000000000001",
                "rating": "thumbs_down",
                "comment": "x" * 10000,
                "tags": ["tag1"] * 100,
            },
            headers=auth_headers,
        )
        assert resp.status_code in (200, 201, 422, 400)
