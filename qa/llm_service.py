from functools import lru_cache

from django.conf import settings
from langchain_core.output_parsers import StrOutputParser
from langchain_openrouter import ChatOpenRouter

from .prompts import RAG_PROMPT


class LLMConfigurationError(Exception):
    pass


class LLMGenerationError(Exception):
    pass


@lru_cache(maxsize=1)
def get_chat_model():
    api_key = settings.OPENROUTER_API_KEY
    model_name = settings.OPENROUTER_MODEL

    if not api_key:
        raise LLMConfigurationError(
            "OpenRouter API key is not configured."
        )

    if not model_name:
        raise LLMConfigurationError(
            "OpenRouter model is not configured."
        )

    return ChatOpenRouter(
        model=model_name,
        api_key=api_key,
        temperature=0,
        max_tokens=settings.RAG_LLM_MAX_TOKENS,
        timeout=settings.RAG_LLM_TIMEOUT,
        max_retries=1,
    )


def generate_answer(question, context):
    model = get_chat_model()

    chain = (
        RAG_PROMPT
        | model
        | StrOutputParser()
    )

    try:
        response = chain.invoke(
            {
                "question": question,
                "context": context,
            }
        )
    except Exception as error:
        raise LLMGenerationError(
            "The language model request failed. Check the OpenRouter connection and model availability."
        ) from error

    answer = response.strip()

    if not answer:
        raise LLMGenerationError(
            "The language model returned an empty response."
        )

    return answer
