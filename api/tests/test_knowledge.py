"""
Integration tests for Knowledge API routes.
"""
import pytest
import io
from httpx import AsyncClient


class TestDocumentUpload:
    """Test POST /api/v1/knowledge/documents/upload."""

    @pytest.mark.integration
    async def test_upload_text_file(self, client: AsyncClient, auth_headers: dict):
        content = b"This is a test document about machine learning."
        files = {
            "file": ("test.txt", io.BytesIO(content), "text/plain"),
        }
        resp = await client.post(
            "/api/v1/knowledge/documents/upload",
            files=files,
            data={"workspace_id": "00000000-0000-0000-0000-000000000001"},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["title"] == "test.txt"
        assert data["status"] in ("pending", "processing", "completed")

    @pytest.mark.integration
    async def test_upload_markdown_file(self, client: AsyncClient, auth_headers: dict):
        content = b"# Title\n\nThis is markdown content.\n\n## Section\n\nMore text here."
        files = {"file": ("doc.md", io.BytesIO(content), "text/markdown")}
        resp = await client.post(
            "/api/v1/knowledge/documents/upload",
            files=files,
            data={"workspace_id": "00000000-0000-0000-0000-000000000001"},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 201)

    @pytest.mark.edge
    async def test_upload_no_file(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/api/v1/knowledge/documents/upload",
            data={"workspace_id": "00000000-0000-0000-0000-000000000001"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    @pytest.mark.edge
    async def test_upload_unauthenticated(self, client: AsyncClient):
        files = {"file": ("test.txt", io.BytesIO(b"test"), "text/plain")}
        resp = await client.post(
            "/api/v1/knowledge/documents/upload",
            files=files,
            data={"workspace_id": "00000000-0000-0000-0000-000000000001"},
        )
        assert resp.status_code in (401, 403)


class TestWebIngest:
    """Test POST /api/v1/knowledge/documents/web."""

    @pytest.mark.integration
    async def test_web_ingest_success(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/api/v1/knowledge/documents/web",
            json={
                "workspace_id": "00000000-0000-0000-0000-000000000001",
                "url": "https://example.com/docs",
                "title": "Example Doc",
            },
            headers=auth_headers,
        )
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["title"] == "Example Doc"
        assert data["source_url"] == "https://example.com/docs"

    @pytest.mark.edge
    async def test_web_ingest_invalid_url(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/api/v1/knowledge/documents/web",
            json={
                "workspace_id": "00000000-0000-0000-0000-000000000001",
                "url": "not-a-url",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422


class TestSearch:
    """Test POST /api/v1/knowledge/search."""

    @pytest.mark.integration
    async def test_search_empty_results(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/api/v1/knowledge/search",
            json={
                "query": "nonexistent topic xyz",
                "workspace_id": "00000000-0000-0000-0000-000000000001",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert isinstance(data["results"], list)

    @pytest.mark.edge
    async def test_search_empty_query(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/api/v1/knowledge/search",
            json={
                "query": "",
                "workspace_id": "00000000-0000-0000-0000-000000000001",
            },
            headers=auth_headers,
        )
        assert resp.status_code in (200, 422)

    @pytest.mark.edge
    async def test_search_very_long_query(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/api/v1/knowledge/search",
            json={
                "query": "x" * 5000,
                "workspace_id": "00000000-0000-0000-0000-000000000001",
                "top_k": 5,
            },
            headers=auth_headers,
        )
        assert resp.status_code in (200, 422)


class TestDocumentList:
    """Test GET /api/v1/knowledge/documents."""

    @pytest.mark.integration
    async def test_list_documents(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get(
            "/api/v1/knowledge/documents?workspace_id=00000000-0000-0000-0000-000000000001",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

    @pytest.mark.edge
    async def test_list_documents_invalid_page(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get(
            "/api/v1/knowledge/documents?workspace_id=00000000-0000-0000-0000-000000000001&page=-1",
            headers=auth_headers,
        )
        assert resp.status_code in (200, 422)
