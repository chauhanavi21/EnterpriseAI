"""
Unit tests for the ingestion pipeline: TextExtractor, TextChunker, EmbeddingService.
"""
import pytest
from unittest.mock import AsyncMock, patch
from app.services.ingestion_service import TextExtractor, TextChunker, EmbeddingService


class TestTextExtractor:
    """Test text extraction from various file types."""

    @pytest.mark.unit
    def test_extract_plain_text(self):
        content = b"Hello, this is a plain text file"
        text = TextExtractor.extract(content, "txt")
        assert text == "Hello, this is a plain text file"

    @pytest.mark.unit
    def test_extract_markdown(self):
        content = b"# Title\n\nSome **bold** text"
        text = TextExtractor.extract(content, "md")
        assert "Title" in text
        assert "bold" in text

    @pytest.mark.unit
    def test_extract_csv(self):
        content = b"name,age\nAlice,30\nBob,25"
        text = TextExtractor.extract(content, "csv")
        assert "Alice" in text
        assert "Bob" in text

    @pytest.mark.unit
    def test_extract_json(self):
        content = b'{"key": "value", "items": [1, 2, 3]}'
        text = TextExtractor.extract(content, "json")
        assert "key" in text
        assert "value" in text

    @pytest.mark.unit
    def test_extract_html(self):
        content = b"<html><body><p>Hello World</p></body></html>"
        text = TextExtractor.extract(content, "html")
        assert "Hello World" in text

    @pytest.mark.edge
    def test_extract_empty_content(self):
        text = TextExtractor.extract(b"", "txt")
        assert text == ""

    @pytest.mark.edge
    def test_extract_unsupported_type(self):
        with pytest.raises(Exception):
            TextExtractor.extract(b"data", "exe")

    @pytest.mark.edge
    def test_extract_binary_as_txt(self):
        """Binary data read as txt should not crash."""
        content = b"\x00\x01\x02\x03"
        # Should handle gracefully, possibly with errors='replace'
        try:
            text = TextExtractor.extract(content, "txt")
            assert isinstance(text, str)
        except UnicodeDecodeError:
            pass  # acceptable for invalid content


class TestTextChunker:
    """Test text chunking logic."""

    @pytest.mark.unit
    def test_chunk_basic(self):
        text = "Hello world. " * 100  # ~1300 chars
        chunks = TextChunker.chunk(text, chunk_size=200, overlap=50)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 250  # allow some overflow at word boundary

    @pytest.mark.unit
    def test_chunk_short_text(self):
        """Short text should return single chunk."""
        text = "Short text"
        chunks = TextChunker.chunk(text, chunk_size=1000, overlap=50)
        assert len(chunks) == 1
        assert chunks[0] == "Short text"

    @pytest.mark.unit
    def test_chunk_overlap(self):
        """Chunks should overlap."""
        text = "Word " * 200  # 1000 chars
        chunks = TextChunker.chunk(text, chunk_size=100, overlap=30)
        if len(chunks) >= 2:
            # Last part of chunk[0] should appear in beginning of chunk[1]
            end_of_first = chunks[0][-30:]
            assert end_of_first in chunks[1] or chunks[1].startswith(end_of_first[:10])

    @pytest.mark.edge
    def test_chunk_empty_text(self):
        chunks = TextChunker.chunk("", chunk_size=100, overlap=20)
        assert len(chunks) == 0 or (len(chunks) == 1 and chunks[0] == "")

    @pytest.mark.edge
    def test_chunk_size_larger_than_text(self):
        text = "Small"
        chunks = TextChunker.chunk(text, chunk_size=10000, overlap=100)
        assert len(chunks) == 1
        assert chunks[0] == "Small"

    @pytest.mark.edge
    def test_chunk_no_overlap(self):
        text = "A B C D E F G H I J K L M N"
        chunks = TextChunker.chunk(text, chunk_size=10, overlap=0)
        assert len(chunks) >= 1

    @pytest.mark.edge
    def test_chunk_preserves_all_content(self):
        """All words from original should appear in at least one chunk."""
        words = ["word" + str(i) for i in range(50)]
        text = " ".join(words)
        chunks = TextChunker.chunk(text, chunk_size=100, overlap=20)
        combined = " ".join(chunks)
        for word in words:
            assert word in combined


class TestEmbeddingService:
    """Test embedding service (with API commented out)."""

    @pytest.mark.unit
    async def test_embed_returns_placeholder(self):
        """With API commented out, should return zero vectors."""
        service = EmbeddingService()
        vectors = await service.embed_texts(["Hello world", "Test text"])
        assert len(vectors) == 2
        # Each vector should be a list of floats
        for v in vectors:
            assert isinstance(v, list)
            assert all(isinstance(x, (int, float)) for x in v)
