"""
Ingestion pipeline: text extraction, chunking, embedding.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import List, Optional

from app.core.config import get_settings


class TextExtractor:
    """Extract text from various file formats."""

    @staticmethod
    def extract(file_path: str, file_type: str) -> str:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if file_type in (".txt", ".md"):
            return path.read_text(encoding="utf-8", errors="replace")

        elif file_type == ".html":
            content = path.read_text(encoding="utf-8", errors="replace")
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content, "html.parser")
                # Remove scripts, styles
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()
                return soup.get_text(separator="\n", strip=True)
            except ImportError:
                # Fallback: strip HTML tags with regex
                return re.sub(r"<[^>]+>", "", content)

        elif file_type == ".pdf":
            try:
                from pypdf import PdfReader
                reader = PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                return text
            except ImportError:
                raise RuntimeError("pypdf not installed for PDF extraction")

        elif file_type == ".docx":
            try:
                from docx import Document as DocxDoc
                doc = DocxDoc(file_path)
                return "\n".join([p.text for p in doc.paragraphs])
            except ImportError:
                raise RuntimeError("python-docx not installed for DOCX extraction")

        elif file_type == ".csv":
            return path.read_text(encoding="utf-8", errors="replace")

        elif file_type == ".json":
            return path.read_text(encoding="utf-8", errors="replace")

        else:
            return path.read_text(encoding="utf-8", errors="replace")


class TextChunker:
    """Split text into overlapping chunks for embedding."""

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        separators: Optional[List[str]] = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def chunk(self, text: str) -> List[dict]:
        """Split text into chunks with metadata."""
        if not text.strip():
            return []

        chunks = self._recursive_split(text, self.separators)
        result = []
        for i, chunk_text in enumerate(chunks):
            if chunk_text.strip():
                result.append({
                    "content": chunk_text.strip(),
                    "token_count": self._estimate_tokens(chunk_text),
                    "metadata": {
                        "chunk_index": i,
                        "char_start": text.find(chunk_text),
                    },
                })
        return result

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        if not separators:
            # Base case: split by characters
            return self._split_by_size(text)

        separator = separators[0]
        if separator:
            parts = text.split(separator)
        else:
            return self._split_by_size(text)

        chunks = []
        current_chunk = ""

        for part in parts:
            candidate = (current_chunk + separator + part).strip() if current_chunk else part.strip()

            if self._estimate_tokens(candidate) <= self.chunk_size:
                current_chunk = candidate
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                # If the single part is too large, recurse with next separator
                if self._estimate_tokens(part) > self.chunk_size:
                    sub_chunks = self._recursive_split(part, separators[1:])
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = part.strip()

        if current_chunk:
            chunks.append(current_chunk)

        # Add overlap
        if self.chunk_overlap > 0 and len(chunks) > 1:
            chunks = self._add_overlap(chunks)

        return chunks

    def _split_by_size(self, text: str) -> List[str]:
        """Fallback: split by approximate token count."""
        words = text.split()
        chunks = []
        current = []
        current_tokens = 0

        for word in words:
            word_tokens = max(1, len(word) // 4)
            if current_tokens + word_tokens > self.chunk_size and current:
                chunks.append(" ".join(current))
                # Keep overlap
                overlap_words = current[-self.chunk_overlap:] if self.chunk_overlap else []
                current = overlap_words
                current_tokens = sum(max(1, len(w) // 4) for w in current)
            current.append(word)
            current_tokens += word_tokens

        if current:
            chunks.append(" ".join(current))
        return chunks

    def _add_overlap(self, chunks: List[str]) -> List[str]:
        """Add overlap between consecutive chunks."""
        if not chunks:
            return chunks

        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_words = chunks[i - 1].split()
            overlap_text = " ".join(prev_words[-min(self.chunk_overlap, len(prev_words)):])
            overlapped.append(overlap_text + " " + chunks[i])
        return overlapped

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Approximate token count (avg 4 chars per token for English)."""
        return max(1, len(text) // 4)


class EmbeddingService:
    """Generate embeddings for text chunks."""

    def __init__(self):
        self.settings = get_settings()

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        COMMENTED OUT: Requires OPENAI_API_KEY.
        Returns zero vectors as placeholder.
        """
        # ────────────────────────────────────────────────────
        # COMMENTED OUT: Actual embedding call
        # ────────────────────────────────────────────────────
        # from openai import AsyncOpenAI
        # client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        # response = await client.embeddings.create(
        #     model=self.settings.openai_embedding_model,
        #     input=texts,
        # )
        # return [item.embedding for item in response.data]
        # ────────────────────────────────────────────────────

        # Placeholder: return None (no embeddings)
        return [None] * len(texts)

    async def embed_single(self, text: str) -> Optional[List[float]]:
        results = await self.embed_texts([text])
        return results[0] if results else None
