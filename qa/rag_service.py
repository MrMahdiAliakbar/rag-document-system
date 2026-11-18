from django.conf import settings

from documents.search import search_similar_chunks

from .llm_service import (
    LLMConfigurationError,
    LLMGenerationError,
    generate_answer,
)
from .models import QuestionAnswer
from .prompts import INSUFFICIENT_CONTEXT_MARKER


NO_ANSWER_MESSAGE = (
    "No relevant information was found in the provided documents."
)


def build_sources(chunks):
    sources = []

    for rank, chunk in enumerate(chunks, start=1):
        distance = float(chunk.distance)

        sources.append(
            {
                "source_id": f"S{rank}",
                "document_id": chunk.document_id,
                "document_title": chunk.document.title,
                "chunk_index": chunk.chunk_index,
                "similarity": round(1 - distance, 4),
                "distance": round(distance, 4),
                "content": chunk.content,
            }
        )

    return sources


def build_context(sources):
    context_parts = []

    for source in sources:
        context_parts.append(
            (
                f"[{source['source_id']}]\n"
                f"Document: {source['document_title']}\n"
                f"Chunk: {source['chunk_index']}\n"
                f"Content:\n{source['content']}"
            )
        )

    return "\n\n".join(context_parts)


def answer_question(question, top_k=None, document_id=None):
    question = question.strip()

    if not question:
        raise ValueError("Question cannot be empty.")

    if top_k is None:
        top_k = settings.RAG_TOP_K

    if top_k < 1:
        raise ValueError("Top-K must be at least 1.")

    threshold = settings.RAG_MAX_COSINE_DISTANCE

    if not 0 <= threshold <= 2:
        raise ValueError(
            "Cosine distance threshold must be between 0 and 2."
        )

    retrieved_chunks = search_similar_chunks(
        query=question,
        top_k=top_k,
        document_id=document_id,
    )

    relevant_chunks = [
        chunk
        for chunk in retrieved_chunks
        if float(chunk.distance) <= threshold
    ]

    if not relevant_chunks:
        record = QuestionAnswer.objects.create(
            question=question,
            answer=NO_ANSWER_MESSAGE,
            sources=[],
        )

        return {
            "record": record,
            "sources": [],
            "used_llm": False,
        }

    sources = build_sources(relevant_chunks)

    context = build_context(sources)

    try:
        answer = generate_answer(
            question=question,
            context=context,
        )
    except (
        LLMConfigurationError,
        LLMGenerationError,
    ):
        raise

    if INSUFFICIENT_CONTEXT_MARKER in answer:
        answer = NO_ANSWER_MESSAGE

    record = QuestionAnswer.objects.create(
        question=question,
        answer=answer,
        sources=sources,
    )

    return {
        "record": record,
        "sources": sources,
        "used_llm": True,
    }
