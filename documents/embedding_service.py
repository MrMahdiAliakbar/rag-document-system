import os
from functools import lru_cache

from fastembed import TextEmbedding
from fastembed.common.model_description import ModelSource, PoolingType


MODEL_NAME = "intfloat/multilingual-e5-small"
MODEL_DIMENSIONS = 384


def register_embedding_model():
    supported_models = TextEmbedding.list_supported_models()

    is_registered = any(
        item["model"].lower() == MODEL_NAME.lower()
        for item in supported_models
    )

    if not is_registered:
        TextEmbedding.add_custom_model(
            model=MODEL_NAME,
            pooling=PoolingType.MEAN,
            normalization=True,
            sources=ModelSource(hf=MODEL_NAME),
            dim=MODEL_DIMENSIONS,
            model_file="onnx/model_O4.onnx",
            description="Multilingual E5 Small Embedding Model",
            license="mit",
            size_in_gb=0.235,
        )


@lru_cache(maxsize=1)
def get_embedding_model():
    register_embedding_model()

    return TextEmbedding(
        model_name=MODEL_NAME,
        cache_dir=os.environ.get("FASTEMBED_CACHE_PATH"),
        threads=2,
    )


def encode_texts(texts, prefix):
    if not texts:
        return []

    model = get_embedding_model()

    prefixed_texts = [
        f"{prefix}: {text.strip()}"
        for text in texts
    ]

    vectors = list(
        model.embed(
            prefixed_texts,
            batch_size=16,
        )
    )

    if len(vectors) != len(texts):
        raise RuntimeError(
            "Embedding count does not match input count."
        )

    results = []

    for vector in vectors:
        if len(vector) != MODEL_DIMENSIONS:
            raise ValueError(
                "The embedding model returned an unexpected vector size."
            )

        results.append([
            float(value)
            for value in vector
        ])

    return results


def generate_passage_embeddings(texts):
    return encode_texts(texts, "passage")


def generate_query_embedding(query):
    query = query.strip()

    if not query:
        raise ValueError("Search query cannot be empty.")

    vectors = encode_texts([query], "query")

    return vectors[0]
