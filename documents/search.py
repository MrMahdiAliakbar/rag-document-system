from pgvector.django import CosineDistance

from .embedding_service import generate_query_embedding
from .models import Document, DocumentChunk


def search_similar_chunks(query, top_k=5, document_id=None):
    query = query.strip()

    if not query:
        raise ValueError("Search query cannot be empty.")

    if top_k < 1:
        raise ValueError("Top-K must be at least 1.")

    query_vector = generate_query_embedding(query)

    queryset = DocumentChunk.objects.filter(
        embedding__isnull=False,
        document__status=Document.Status.COMPLETED,
    )

    if document_id is not None:
        queryset = queryset.filter(
            document_id=document_id
        )

    results = (
        queryset
        .annotate(
            distance=CosineDistance(
                "embedding",
                query_vector,
            )
        )
        .select_related("document")
        .order_by("distance")[:top_k]
    )

    return list(results)
