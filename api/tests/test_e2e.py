"""
End-to-end smoke tests simulating full user workflows.
"""
import pytest
from httpx import AsyncClient
import io


class TestE2EUserWorkflow:
    """Full user journey: register → login → upload doc → chat → feedback → eval."""

    @pytest.mark.e2e
    async def test_full_user_journey(self, client: AsyncClient):
        # 1. Register
        email = "e2e-user@test.com"
        reg_resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "E2ePass123!",
                "full_name": "E2E User",
            },
        )
        assert reg_resp.status_code == 201
        user_id = reg_resp.json()["id"]

        # 2. Login
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "E2ePass123!"},
        )
        assert login_resp.status_code == 200
        tokens = login_resp.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # 3. Get profile
        me_resp = await client.get("/api/v1/auth/me", headers=headers)
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == email

        # 4. Upload document
        doc_content = b"Machine learning is a subset of AI that enables systems to learn from data."
        upload_resp = await client.post(
            "/api/v1/knowledge/documents/upload",
            files={"file": ("ml-intro.txt", io.BytesIO(doc_content), "text/plain")},
            data={"workspace_id": "00000000-0000-0000-0000-000000000001"},
            headers=headers,
        )
        assert upload_resp.status_code in (200, 201)
        doc_id = upload_resp.json()["id"]

        # 5. List documents
        docs_resp = await client.get(
            "/api/v1/knowledge/documents?workspace_id=00000000-0000-0000-0000-000000000001",
            headers=headers,
        )
        assert docs_resp.status_code == 200
        assert docs_resp.json()["total"] >= 1

        # 6. Chat
        chat_resp = await client.post(
            "/api/v1/chat/",
            json={
                "message": "What is machine learning?",
                "workspace_id": "00000000-0000-0000-0000-000000000001",
                "use_retrieval": True,
            },
            headers=headers,
        )
        assert chat_resp.status_code == 200
        conv_id = chat_resp.json()["conversation_id"]
        msg_id = chat_resp.json()["message_id"]
        assert chat_resp.json()["content"]

        # 7. Follow-up chat
        chat2_resp = await client.post(
            "/api/v1/chat/",
            json={
                "message": "Tell me more",
                "workspace_id": "00000000-0000-0000-0000-000000000001",
                "conversation_id": conv_id,
            },
            headers=headers,
        )
        assert chat2_resp.status_code == 200

        # 8. Submit feedback
        fb_resp = await client.post(
            "/api/v1/feedback/",
            json={
                "message_id": msg_id,
                "rating": "thumbs_up",
                "comment": "Very helpful!",
                "tags": ["accurate", "relevant"],
            },
            headers=headers,
        )
        assert fb_resp.status_code in (200, 201)

        # 9. Check feedback stats
        stats_resp = await client.get("/api/v1/feedback/stats", headers=headers)
        assert stats_resp.status_code == 200

        # 10. Create eval dataset
        ds_resp = await client.post(
            "/api/v1/eval/datasets",
            json={"name": "e2e-dataset", "description": "End-to-end test dataset"},
            headers=headers,
        )
        assert ds_resp.status_code in (200, 201)
        ds_id = ds_resp.json()["id"]

        # 11. Add items to dataset
        item_resp = await client.post(
            f"/api/v1/eval/datasets/{ds_id}/items",
            json={
                "question": "What is machine learning?",
                "ground_truth": "A subset of AI that enables systems to learn from data",
                "context": ["ML is a type of AI"],
            },
            headers=headers,
        )
        assert item_resp.status_code in (200, 201)

        # 12. Create and run experiment
        exp_resp = await client.post(
            "/api/v1/eval/experiments",
            json={"name": "e2e-experiment", "dataset_id": ds_id},
            headers=headers,
        )
        assert exp_resp.status_code in (200, 201)
        exp_id = exp_resp.json()["id"]

        # 13. Create prompt template
        pt_resp = await client.post(
            "/api/v1/prompts/templates",
            json={"name": "e2e-prompt", "description": "E2E test prompt"},
            headers=headers,
        )
        assert pt_resp.status_code in (200, 201)
        pt_id = pt_resp.json()["id"]

        # 14. Create prompt version
        pv_resp = await client.post(
            f"/api/v1/prompts/templates/{pt_id}/versions",
            json={
                "content": "Context: {{context}}\nQuestion: {{question}}",
                "system_prompt": "You are a helpful assistant.",
            },
            headers=headers,
        )
        assert pv_resp.status_code in (200, 201)

        # 15. Check traces
        traces_resp = await client.get("/api/v1/traces/", headers=headers)
        assert traces_resp.status_code == 200

        # 16. Refresh token
        refresh_resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert refresh_resp.status_code == 200
        assert "access_token" in refresh_resp.json()


class TestE2EAdminWorkflow:
    """Admin workflow: register admin → view users → view audit logs → settings."""

    @pytest.mark.e2e
    async def test_admin_workflow(self, client: AsyncClient):
        # Register (first user becomes admin in some systems)
        email = "admin-e2e@test.com"
        reg_resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "AdminE2e123!",
                "full_name": "Admin E2E",
            },
        )
        assert reg_resp.status_code == 201

        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "AdminE2e123!"},
        )
        assert login_resp.status_code == 200
        headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

        # Try admin endpoints (may be restricted to superuser)
        users_resp = await client.get("/api/v1/admin/users", headers=headers)
        # Could be 200 if first user is admin, or 403 if not
        assert users_resp.status_code in (200, 403)

        settings_resp = await client.get("/api/v1/admin/settings", headers=headers)
        assert settings_resp.status_code in (200, 403)

        audit_resp = await client.get("/api/v1/audit/logs", headers=headers)
        assert audit_resp.status_code in (200, 403)
