import json
import logging
import os

import numpy as np

from src.config import config

logger = logging.getLogger(__name__)


class VectorStore:
    """In-memory vector store with NumPy-based cosine similarity search.

    Vectors and their associated metadata (text chunks) are kept in memory
    and can optionally be persisted to disk as NumPy / JSON files.
    """

    def __init__(self, store_path: str | None = None):
        self.store_path = store_path or config.VECTOR_STORE_PATH
        self.vectors: np.ndarray | None = None  # (N, D) float32
        self.documents: list[dict] = []  # [{text, metadata}, ...]
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_documents(self, texts: list[str], embeddings: list[list[float]], metadata: list[dict] | None = None) -> None:
        """Add document chunks with their embeddings to the store.

        Args:
            texts: The raw text chunks.
            embeddings: Corresponding embedding vectors.
            metadata: Optional per-chunk metadata dicts.
        """
        new_vectors = np.array(embeddings, dtype=np.float32)
        if self.vectors is None:
            self.vectors = new_vectors
        else:
            self.vectors = np.vstack([self.vectors, new_vectors])

        for i, text in enumerate(texts):
            self.documents.append({
                "text": text,
                "metadata": metadata[i] if metadata else {},
            })

        self._save()
        logger.info("Added %d document chunks (total: %d)", len(texts), len(self.documents))

    def add_vector(self, vector: list[float]) -> None:
        """Add a single vector (legacy helper)."""
        self.add_documents(texts=[""], embeddings=[vector])

    def find_similar(self, query_vector: list[float], top_k: int = 5) -> list[dict]:
        """Find the *top_k* most similar documents using cosine similarity.

        Args:
            query_vector: The query embedding.
            top_k: Number of results to return.

        Returns:
            A list of dicts with keys ``text``, ``metadata``, and ``score``.
        """
        if self.vectors is None or len(self.documents) == 0:
            return []

        qv = np.array(query_vector, dtype=np.float32)
        # Cosine similarity
        norms = np.linalg.norm(self.vectors, axis=1)
        qv_norm = np.linalg.norm(qv)
        # Avoid division by zero
        safe_norms = np.where(norms == 0, 1.0, norms)
        safe_qv_norm = qv_norm if qv_norm != 0 else 1.0
        similarities = (self.vectors @ qv) / (safe_norms * safe_qv_norm)

        top_k = min(top_k, len(self.documents))
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append({
                "text": self.documents[idx]["text"],
                "metadata": self.documents[idx]["metadata"],
                "score": float(similarities[idx]),
            })
        return results

    @property
    def size(self) -> int:
        return len(self.documents)

    def clear(self) -> None:
        """Remove all documents and vectors."""
        self.vectors = None
        self.documents = []
        self._save()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _save(self) -> None:
        os.makedirs(self.store_path, exist_ok=True)
        if self.vectors is not None:
            np.save(os.path.join(self.store_path, "vectors.npy"), self.vectors)
        docs_path = os.path.join(self.store_path, "documents.json")
        with open(docs_path, "w", encoding="utf-8") as fh:
            json.dump(self.documents, fh, ensure_ascii=False)

    def _load(self) -> None:
        vec_path = os.path.join(self.store_path, "vectors.npy")
        docs_path = os.path.join(self.store_path, "documents.json")
        if os.path.exists(vec_path) and os.path.exists(docs_path):
            self.vectors = np.load(vec_path)
            with open(docs_path, encoding="utf-8") as fh:
                self.documents = json.load(fh)
            logger.info("Loaded %d documents from %s", len(self.documents), self.store_path)
