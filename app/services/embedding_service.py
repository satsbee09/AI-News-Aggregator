import numpy as np
from typing import List, Optional
from fastembed import TextEmbedding

class EmbeddingService:
    _instance: Optional["EmbeddingService"] = None
    _model: Optional[TextEmbedding] = None

    def __new__(cls) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            try:
                # Lightweight 384-dimensional ONNX embedding model (zero cost, local CPU execution)
                cls._model = TextEmbedding("BAAI/bge-small-en-v1.5")
            except Exception as e:
                print(f"[EMBEDDING INIT ERROR] Failed to load FastEmbed model: {e}")
                cls._model = None
        return cls._instance

    @property
    def dimensions(self) -> int:
        return 384

    def embed_text(self, text: str) -> List[float]:
        """Generates a normalized 384-dimensional float vector for single text snippet."""
        if not text or not text.strip():
            return [0.0] * self.dimensions

        if self._model is None:
            self._model = TextEmbedding("BAAI/bge-small-en-v1.5")

        try:
            embeddings = list(self._model.embed([text]))
            if embeddings:
                return [float(x) for x in embeddings[0]]
            return [0.0] * self.dimensions
        except Exception as e:
            print(f"[EMBEDDING ERROR] Failed to embed text: {e}")
            return [0.0] * self.dimensions

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a batch of strings."""
        if not texts:
            return []

        if self._model is None:
            self._model = TextEmbedding("BAAI/bge-small-en-v1.5")

        try:
            embeddings = list(self._model.embed(texts))
            return [[float(x) for x in emb] for emb in embeddings]
        except Exception as e:
            print(f"[EMBEDDING ERROR] Failed batch embedding: {e}")
            return [[0.0] * self.dimensions for _ in texts]

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """Computes cosine similarity between two float vectors."""
        a = np.array(v1, dtype=np.float32)
        b = np.array(v2, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

embedding_service = EmbeddingService()
