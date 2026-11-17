from functools import lru_cache
from tokenizers import Tokenizer


MODEL_NAME = "intfloat/multilingual-e5-small"

CHUNK_SIZE = 450
CHUNK_OVERLAP = 60


@lru_cache(maxsize=1)
def get_tokenizer():
    return Tokenizer.from_pretrained(MODEL_NAME)


def split_text_into_chunks(text):
    tokenizer = get_tokenizer()

    token_ids = tokenizer.encode(
        text,
        add_special_tokens=False,
    ).ids

    if not token_ids:
        return []

    chunks = []
    step = CHUNK_SIZE - CHUNK_OVERLAP

    for start in range(0, len(token_ids), step):
        end = min(start + CHUNK_SIZE, len(token_ids))

        chunk_text = tokenizer.decode(
            token_ids[start:end],
            skip_special_tokens=True,
        ).strip()

        if chunk_text:
            chunks.append(chunk_text)

        if end >= len(token_ids):
            break

    return chunks
