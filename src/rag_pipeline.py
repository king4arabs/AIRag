"""RAG (Retrieval-Augmented Generation) pipeline.

Orchestrates document ingestion, chunking, embedding, and query-time
retrieval + LLM generation.
"""

import logging
import os
import re

import pandas as pd

from src.config import config
from src.financial_analyzer import FinancialAnalyzer
from src.llm_provider import LLMProvider
from src.vector_store import VectorStore

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are AIRag, a helpful AI financial assistant. "
    "Answer the user's question using ONLY the context provided below. "
    "If the context does not contain enough information, say so clearly.\n\n"
    "Context:\n{context}"
)


class RAGPipeline:
    """End-to-end RAG pipeline for financial document Q&A."""

    def __init__(self) -> None:
        self.llm = LLMProvider()
        self.vector_store = VectorStore()

    # ------------------------------------------------------------------
    # Document ingestion
    # ------------------------------------------------------------------

    def ingest_text(self, text: str, metadata: dict | None = None) -> int:
        """Chunk plain text, embed, and store in the vector store.

        Returns:
            Number of chunks created.
        """
        chunks = self._chunk_text(text)
        if not chunks:
            return 0

        embeddings = self.llm.generate_embeddings(chunks)
        meta_list = [metadata or {} for _ in chunks]
        self.vector_store.add_documents(chunks, embeddings, meta_list)
        return len(chunks)

    def ingest_csv(self, filepath: str) -> dict:
        """Ingest a CSV file: store chunks for RAG and run financial analysis.

        Returns:
            A dict with ``chunks`` count and ``analysis`` summary.
        """
        df = pd.read_csv(filepath)
        analyzer = FinancialAnalyzer(df)
        analysis = analyzer.get_results()
        summary_text = analyzer.get_summary_text()

        # Also ingest the textual representation for RAG retrieval
        text_repr = df.to_string(index=False)
        chunks_count = self.ingest_text(
            text_repr,
            metadata={"source": os.path.basename(filepath), "type": "csv"},
        )

        # Ingest the analysis summary as a searchable chunk too
        self.ingest_text(
            summary_text,
            metadata={"source": os.path.basename(filepath), "type": "analysis"},
        )

        return {"chunks": chunks_count, "analysis": analysis}

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query(self, question: str, top_k: int = 5) -> dict:
        """Answer a question using the RAG pipeline.

        Returns:
            A dict with ``answer`` and ``sources``.
        """
        if self.vector_store.size == 0:
            return {
                "answer": "No documents have been ingested yet. Please upload a document first.",
                "sources": [],
            }

        query_embedding = self.llm.generate_embeddings([question])[0]
        results = self.vector_store.find_similar(query_embedding, top_k=top_k)

        context = "\n---\n".join(r["text"] for r in results if r["text"])
        system = SYSTEM_PROMPT.format(context=context)
        answer = self.llm.generate_response(question, system_prompt=system)

        sources = [
            {"text": r["text"][:200], "score": r["score"], "metadata": r["metadata"]}
            for r in results
        ]
        return {"answer": answer, "sources": sources}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _chunk_text(text: str) -> list[str]:
        """Split text into overlapping chunks."""
        chunk_size = config.CHUNK_SIZE
        overlap = config.CHUNK_OVERLAP
        # Split on sentence boundaries where possible
        sentences = re.split(r"(?<=[.!?])\s+", text)

        chunks: list[str] = []
        current_chunk: list[str] = []
        current_len = 0

        for sentence in sentences:
            sentence_len = len(sentence)
            if current_len + sentence_len > chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                # Keep overlap
                overlap_sentences: list[str] = []
                overlap_len = 0
                for s in reversed(current_chunk):
                    if overlap_len + len(s) > overlap:
                        break
                    overlap_sentences.insert(0, s)
                    overlap_len += len(s)
                current_chunk = overlap_sentences
                current_len = overlap_len
            current_chunk.append(sentence)
            current_len += sentence_len

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks
