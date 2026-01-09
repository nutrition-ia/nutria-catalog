from typing import List, Optional
from sqlmodel import Session, text
from uuid import UUID
from app.services.embedding_service import EmbeddingService

from app.models.food import Food


class SearchService:
    """
    Service for advanced search operations including semantic search

    Note: Semantic search with pgvector will be implemented in a future phase.
    This service is prepared for that implementation.
    """

    def __init__(self, session: Session):
        self.session = session
        self.embedding_service = EmbeddingService()

    def semantic_search(
        self,
        query: str,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Food]:
        """
        Perform semantic search using vector embeddings

        This is a placeholder for future implementation.
        Requires:
        - Embedding generation (e.g., using sentence-transformers)
        - pgvector distance calculation

        Args:
            query_embedding: Vector embedding of the search query
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            List of Food objects ordered by similarity
        """
        query_embedding = self.embedding_service.generate_embedding(query)

        # Query SQL com pgvector
        # Usa operador <=> para distância de cosseno
        sql = text("""
            SELECT *,
                   1 - (embedding <=> :query_embedding) AS similarity
            FROM foods
            WHERE embedding IS NOT NULL
              AND 1 - (embedding <=> :query_embedding) > :threshold
            ORDER BY embedding <=> :query_embedding
            LIMIT :limit
        """)

        results = self.session.exec(
            sql,
            params={
                "query_embedding": query_embedding,
                "threshold": similarity_threshold,
                "limit": limit
            }
        ).all()

        return list(results)

    def hybrid_search(
        self,
        query: str,
        limit: int = 10,
        semantic_weight: float = 0.6,
        text_weight: float = 0.4
    ) -> List[Food]:
        """
        Busca híbrida: combina busca textual (ILIKE) com busca semântica

        Score final = (semantic_weight * semantic_score) + (text_weight * text_score)
        """
        query_embedding = self.embedding_service.generate_embedding(query)
        search_term = f"%{query.lower()}%"

        sql = text("""
            WITH semantic_scores AS (
                SELECT
                    id,
                    1 - (embedding <=> :query_embedding) AS semantic_score
                FROM foods
                WHERE embedding IS NOT NULL
            ),
            text_scores AS (
                SELECT
                    id,
                    CASE
                        WHEN name_normalized ILIKE :search_term THEN 1.0
                        WHEN name ILIKE :search_term THEN 0.8
                        ELSE 0.0
                    END AS text_score
                FROM foods
            )
            SELECT
                f.*,
                (:semantic_weight * COALESCE(ss.semantic_score, 0) +
                 :text_weight * COALESCE(ts.text_score, 0)) AS final_score
            FROM foods f
            LEFT JOIN semantic_scores ss ON f.id = ss.id
            LEFT JOIN text_scores ts ON f.id = ts.id
            WHERE (ss.semantic_score > 0.5 OR ts.text_score > 0)
            ORDER BY final_score DESC
            LIMIT :limit
        """)

        results = self.session.exec(
            sql,
            params={
                "query_embedding": query_embedding,
                "search_term": search_term,
                "semantic_weight": semantic_weight,
                "text_weight": text_weight,
                "limit": limit
            }
        ).all()

        return list(results)
    def hybrid_search(
        self,
        text_query: str,
        query_embedding: Optional[List[float]] = None,
        limit: int = 10
    ) -> List[Food]:
        """
        Perform hybrid search combining text and semantic search

        This is a placeholder for future implementation.

        Args:
            text_query: Text search query
            query_embedding: Optional vector embedding for semantic search
            limit: Maximum number of results

        Returns:
            List of Food objects ranked by combined relevance
        """
        # TODO: Implement hybrid search
        # Combine text search scores with vector similarity scores

        raise NotImplementedError("Hybrid search will be implemented in Phase 2")
