"""
Integration tests for Evaluation (EvalOps) API routes.
"""
import pytest
from httpx import AsyncClient


class TestDatasets:
    """Test /api/v1/eval/datasets endpoints."""

    @pytest.mark.integration
    async def test_create_dataset(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/api/v1/eval/datasets",
            json={"name": "test-dataset", "description": "A test eval dataset"},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["name"] == "test-dataset"
        assert "id" in data

    @pytest.mark.integration
    async def test_list_datasets(self, client: AsyncClient, auth_headers: dict):
        # Create one
        await client.post(
            "/api/v1/eval/datasets",
            json={"name": "list-test"},
            headers=auth_headers,
        )
        resp = await client.get("/api/v1/eval/datasets", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert len(data["items"]) >= 1

    @pytest.mark.integration
    async def test_add_dataset_item(self, client: AsyncClient, auth_headers: dict):
        # Create dataset
        ds_resp = await client.post(
            "/api/v1/eval/datasets",
            json={"name": "item-test"},
            headers=auth_headers,
        )
        ds_id = ds_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/eval/datasets/{ds_id}/items",
            json={
                "question": "What is RAG?",
                "ground_truth": "Retrieval Augmented Generation",
                "context": ["RAG combines retrieval with generation"],
            },
            headers=auth_headers,
        )
        assert resp.status_code in (200, 201)

    @pytest.mark.edge
    async def test_create_dataset_missing_name(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/api/v1/eval/datasets",
            json={},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    @pytest.mark.edge
    async def test_get_nonexistent_dataset(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get(
            "/api/v1/eval/datasets/00000000-0000-0000-0000-999999999999",
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestExperiments:
    """Test /api/v1/eval/experiments endpoints."""

    @pytest.mark.integration
    async def test_create_experiment(self, client: AsyncClient, auth_headers: dict):
        # Create dataset first
        ds_resp = await client.post(
            "/api/v1/eval/datasets",
            json={"name": "exp-dataset"},
            headers=auth_headers,
        )
        ds_id = ds_resp.json()["id"]

        resp = await client.post(
            "/api/v1/eval/experiments",
            json={"name": "baseline-experiment", "dataset_id": ds_id},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["name"] == "baseline-experiment"
        assert data["status"] in ("pending", "running")

    @pytest.mark.integration
    async def test_list_experiments(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/eval/experiments", headers=auth_headers)
        assert resp.status_code == 200
        assert "items" in resp.json()

    @pytest.mark.integration
    async def test_run_experiment(self, client: AsyncClient, auth_headers: dict):
        # Create dataset + experiment
        ds_resp = await client.post(
            "/api/v1/eval/datasets",
            json={"name": "run-dataset"},
            headers=auth_headers,
        )
        ds_id = ds_resp.json()["id"]

        exp_resp = await client.post(
            "/api/v1/eval/experiments",
            json={"name": "run-exp", "dataset_id": ds_id},
            headers=auth_headers,
        )
        exp_id = exp_resp.json()["id"]

        resp = await client.post(
            "/api/v1/eval/experiments/run",
            json={"experiment_id": exp_id},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 202)

    @pytest.mark.edge
    async def test_create_experiment_invalid_dataset(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/api/v1/eval/experiments",
            json={
                "name": "bad-exp",
                "dataset_id": "00000000-0000-0000-0000-999999999999",
            },
            headers=auth_headers,
        )
        assert resp.status_code in (404, 400)


class TestPrompts:
    """Test /api/v1/prompts endpoints."""

    @pytest.mark.integration
    async def test_create_template(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/api/v1/prompts/templates",
            json={"name": "test-prompt", "description": "Test prompt template"},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["name"] == "test-prompt"

    @pytest.mark.integration
    async def test_create_version(self, client: AsyncClient, auth_headers: dict):
        # Create template
        t_resp = await client.post(
            "/api/v1/prompts/templates",
            json={"name": "version-test"},
            headers=auth_headers,
        )
        t_id = t_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/prompts/templates/{t_id}/versions",
            json={
                "content": "Answer the question: {{question}}\nContext: {{context}}",
                "system_prompt": "You are a helpful assistant.",
            },
            headers=auth_headers,
        )
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["version_number"] == 1

    @pytest.mark.integration
    async def test_promote_version(self, client: AsyncClient, auth_headers: dict):
        t_resp = await client.post(
            "/api/v1/prompts/templates",
            json={"name": "promote-test"},
            headers=auth_headers,
        )
        t_id = t_resp.json()["id"]

        v_resp = await client.post(
            f"/api/v1/prompts/templates/{t_id}/versions",
            json={"content": "Test content"},
            headers=auth_headers,
        )
        v_id = v_resp.json()["id"]

        resp = await client.patch(
            f"/api/v1/prompts/versions/{v_id}/label",
            json={"label": "production"},
            headers=auth_headers,
        )
        assert resp.status_code == 200


class TestTraces:
    """Test /api/v1/traces endpoints."""

    @pytest.mark.integration
    async def test_list_traces(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/traces/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data

    @pytest.mark.edge
    async def test_get_nonexistent_trace(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get(
            "/api/v1/traces/00000000-0000-0000-0000-999999999999",
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestFeedback:
    """Test /api/v1/feedback endpoints."""

    @pytest.mark.integration
    async def test_feedback_stats(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/feedback/stats", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "thumbs_up" in data
        assert "thumbs_down" in data

    @pytest.mark.integration
    async def test_list_feedback(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/feedback/", headers=auth_headers)
        assert resp.status_code == 200
        assert "items" in resp.json()


class TestHealthCheck:
    """Test health endpoint."""

    @pytest.mark.unit
    async def test_health(self, client: AsyncClient):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
