
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase, override_settings

from rest_framework.test import APIClient

from documents.models import Document
from .llm_service import (
    LLMConfigurationError,
    LLMGenerationError,
    generate_answer,
    get_chat_model,
)
from .models import QuestionAnswer
from .rag_service import (
    NO_ANSWER_MESSAGE,
    answer_question,
    build_context,
    build_sources,
)


def create_chunk(
    distance=0.1,
    content="Relevant document content",
    document_id=1,
    title="Test document",
    chunk_index=0,
):
    return SimpleNamespace(
        distance=distance,
        content=content,
        document_id=document_id,
        document=SimpleNamespace(title=title),
        chunk_index=chunk_index,
    )


class SourceBuildingTests(SimpleTestCase):
    def test_build_sources_assigns_source_ids(self):
        chunks = [
            create_chunk(distance=0.1),
            create_chunk(
                distance=0.2,
                content="Second source",
                chunk_index=1,
            ),
        ]

        sources = build_sources(chunks)

        self.assertEqual(len(sources), 2)
        self.assertEqual(sources[0]["source_id"], "S1")
        self.assertEqual(sources[1]["source_id"], "S2")
        self.assertEqual(sources[0]["similarity"], 0.9)
        self.assertEqual(sources[1]["distance"], 0.2)

    def test_build_context_includes_source_information(self):
        sources = [
            {
                "source_id": "S1",
                "document_title": "Test document",
                "chunk_index": 2,
                "content": "Relevant content",
            }
        ]

        context = build_context(sources)

        self.assertIn("[S1]", context)
        self.assertIn("Test document", context)
        self.assertIn("Chunk: 2", context)
        self.assertIn("Relevant content", context)


class RAGServiceTests(TestCase):
    def setUp(self):
        self.chunk = create_chunk()

    @override_settings(
        RAG_TOP_K=5,
        RAG_MAX_COSINE_DISTANCE=0.2,
    )
    @patch("qa.rag_service.generate_answer")
    @patch("qa.rag_service.search_similar_chunks")
    def test_returns_no_answer_when_no_chunks_are_found(
        self,
        mock_search,
        mock_generate,
    ):
        mock_search.return_value = []

        result = answer_question("Unknown question")

        self.assertEqual(
            result["record"].answer,
            NO_ANSWER_MESSAGE,
        )
        self.assertEqual(result["sources"], [])
        self.assertFalse(result["used_llm"])
        mock_generate.assert_not_called()

    @override_settings(
        RAG_TOP_K=5,
        RAG_MAX_COSINE_DISTANCE=0.2,
    )
    @patch("qa.rag_service.generate_answer")
    @patch("qa.rag_service.search_similar_chunks")
    def test_filters_chunks_above_similarity_threshold(
        self,
        mock_search,
        mock_generate,
    ):
        mock_search.return_value = [
            create_chunk(distance=0.3),
        ]

        result = answer_question("Unknown question")

        self.assertEqual(
            result["record"].answer,
            NO_ANSWER_MESSAGE,
        )
        self.assertEqual(result["sources"], [])
        mock_generate.assert_not_called()

    @override_settings(
        RAG_TOP_K=5,
        RAG_MAX_COSINE_DISTANCE=0.2,
    )
    @patch("qa.rag_service.generate_answer")
    @patch("qa.rag_service.search_similar_chunks")
    def test_generates_answer_using_relevant_sources(
        self,
        mock_search,
        mock_generate,
    ):
        mock_search.return_value = [self.chunk]
        mock_generate.return_value = "The document contains the answer."

        result = answer_question(
            "What does the document contain?"
        )

        self.assertEqual(
            result["record"].answer,
            "The document contains the answer.",
        )
        self.assertEqual(len(result["sources"]), 1)
        self.assertTrue(result["used_llm"])

        mock_generate.assert_called_once()

        context = mock_generate.call_args.kwargs["context"]

        self.assertIn("[S1]", context)
        self.assertIn(
            "Relevant document content",
            context,
        )

    @override_settings(
        RAG_TOP_K=5,
        RAG_MAX_COSINE_DISTANCE=0.2,
    )
    @patch("qa.rag_service.generate_answer")
    @patch("qa.rag_service.search_similar_chunks")
    def test_converts_insufficient_context_marker_to_no_answer(
        self,
        mock_search,
        mock_generate,
    ):
        from .prompts import INSUFFICIENT_CONTEXT_MARKER

        mock_search.return_value = [self.chunk]
        mock_generate.return_value = (
            f"{INSUFFICIENT_CONTEXT_MARKER} Additional text"
        )

        result = answer_question("Unknown question")

        self.assertEqual(
            result["record"].answer,
            NO_ANSWER_MESSAGE,
        )
        self.assertTrue(result["used_llm"])

    @override_settings(
        RAG_TOP_K=5,
        RAG_MAX_COSINE_DISTANCE=0.2,
    )
    @patch(
        "qa.rag_service.search_similar_chunks",
        return_value=[],
    )
    def test_saves_question_history_without_sources(
        self,
        mock_search,
    ):
        answer_question("Question without results")

        record = QuestionAnswer.objects.get(
            question="Question without results"
        )

        self.assertEqual(record.answer, NO_ANSWER_MESSAGE)
        self.assertEqual(record.sources, [])

    def test_rejects_empty_question(self):
        with self.assertRaises(ValueError):
            answer_question("   ")

    @override_settings(
        RAG_TOP_K=5,
        RAG_MAX_COSINE_DISTANCE=0.2,
    )
    @patch(
        "qa.rag_service.search_similar_chunks",
        side_effect=ValueError("Invalid search."),
    )
    def test_propagates_search_validation_errors(
        self,
        mock_search,
    ):
        with self.assertRaisesMessage(
            ValueError,
            "Invalid search.",
        ):
            answer_question("Test question")

    @override_settings(
        RAG_TOP_K=5,
        RAG_MAX_COSINE_DISTANCE=3,
    )
    def test_rejects_invalid_similarity_threshold(self):
        with self.assertRaises(ValueError):
            answer_question("Test question")

    @override_settings(
        RAG_TOP_K=5,
        RAG_MAX_COSINE_DISTANCE=0.2,
    )
    @patch("qa.rag_service.generate_answer")
    @patch(
        "qa.rag_service.search_similar_chunks"
    )
    def test_propagates_llm_errors(
        self,
        mock_search,
        mock_generate,
    ):
        mock_search.return_value = [self.chunk]
        mock_generate.side_effect = LLMGenerationError(
            "Model unavailable."
        )

        with self.assertRaises(LLMGenerationError):
            answer_question("Test question")


class LLMServiceTests(SimpleTestCase):
    def tearDown(self):
        get_chat_model.cache_clear()
        super().tearDown()

    def test_rejects_missing_api_key(self):
        get_chat_model.cache_clear()

        with override_settings(
            OPENROUTER_API_KEY="",
            OPENROUTER_MODEL="test-model",
        ):
            with self.assertRaises(LLMConfigurationError):
                get_chat_model()

    def test_rejects_missing_model_name(self):
        get_chat_model.cache_clear()

        with override_settings(
            OPENROUTER_API_KEY="test-key",
            OPENROUTER_MODEL="",
        ):
            with self.assertRaises(LLMConfigurationError):
                get_chat_model()

    @patch("qa.llm_service.ChatOpenRouter")
    def test_creates_chat_model_with_configured_settings(
        self,
        mock_chat,
    ):
        get_chat_model.cache_clear()

        with override_settings(
            OPENROUTER_API_KEY="test-key",
            OPENROUTER_MODEL="test-model",
            RAG_LLM_MAX_TOKENS=512,
            RAG_LLM_TIMEOUT=30000,
        ):
            get_chat_model()

        mock_chat.assert_called_once_with(
            model="test-model",
            api_key="test-key",
            temperature=0,
            max_tokens=512,
            timeout=30000,
            max_retries=1,
        )

    @patch("qa.llm_service.get_chat_model")
    @patch("qa.llm_service.RAG_PROMPT")
    def test_generates_answer(
        self,
        mock_prompt,
        mock_get_model,
    ):
        mock_get_model.return_value = MagicMock()

        mock_chain = MagicMock()
        mock_prompt.__or__.return_value = mock_chain
        mock_chain.__or__.return_value = mock_chain
        mock_chain.invoke.return_value = "Generated answer"

        result = generate_answer(
            question="Test question",
            context="Test context",
        )

        self.assertEqual(result, "Generated answer")
        mock_chain.invoke.assert_called_once_with(
            {
                "question": "Test question",
                "context": "Test context",
            }
        )

    @patch("qa.llm_service.get_chat_model")
    @patch("qa.llm_service.RAG_PROMPT")
    def test_wraps_generation_errors(
        self,
        mock_prompt,
        mock_get_model,
    ):
        mock_get_model.return_value = MagicMock()

        mock_chain = MagicMock()
        mock_prompt.__or__.return_value = mock_chain
        mock_chain.__or__.return_value = mock_chain
        mock_chain.invoke.side_effect = RuntimeError(
            "Connection failed."
        )

        with self.assertRaises(LLMGenerationError):
            generate_answer(
                question="Test question",
                context="Test context",
            )

    @patch("qa.llm_service.get_chat_model")
    @patch("qa.llm_service.RAG_PROMPT")
    def test_rejects_empty_model_response(
        self,
        mock_prompt,
        mock_get_model,
    ):
        mock_get_model.return_value = MagicMock()

        mock_chain = MagicMock()
        mock_prompt.__or__.return_value = mock_chain
        mock_chain.__or__.return_value = mock_chain
        mock_chain.invoke.return_value = "   "

        with self.assertRaises(LLMGenerationError):
            generate_answer(
                question="Test question",
                context="Test context",
            )


class QuestionAnswerAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.ask_url = "/api/qa/ask/"
        self.history_url = "/api/qa/history/"

    def create_record(self, question="Test question"):
        return QuestionAnswer.objects.create(
            question=question,
            answer="Test answer",
            sources=[
                {
                    "source_id": "S1",
                    "content": "Source content",
                }
            ],
        )

    def test_rejects_empty_question(self):
        response = self.client.post(
            self.ask_url,
            {"question": "   "},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_rejects_question_over_maximum_length(self):
        response = self.client.post(
            self.ask_url,
            {"question": "x" * 5001},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_rejects_nonexistent_document_id(self):
        response = self.client.post(
            self.ask_url,
            {
                "question": "Test question",
                "document_id": 99999,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    @patch("qa.views.answer_question")
    def test_ask_question_returns_answer(
        self,
        mock_answer,
    ):
        record = self.create_record()

        mock_answer.return_value = {
            "record": record,
            "sources": record.sources,
            "used_llm": True,
        }

        response = self.client.post(
            self.ask_url,
            {"question": "Test question"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["answer"],
            "Test answer",
        )
        self.assertEqual(response.data["status"], "answered")
        self.assertTrue(response.data["used_llm"])

    @patch(
        "qa.views.answer_question",
        side_effect=ValueError("Invalid question."),
    )
    def test_ask_question_returns_bad_request(
        self,
        mock_answer,
    ):
        response = self.client.post(
            self.ask_url,
            {"question": "Test question"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["detail"],
            "Invalid question.",
        )

    @patch(
        "qa.views.answer_question",
        side_effect=LLMConfigurationError(
            "Missing API key."
        ),
    )
    def test_ask_question_handles_llm_configuration_error(
        self,
        mock_answer,
    ):
        response = self.client.post(
            self.ask_url,
            {"question": "Test question"},
            format="json",
        )

        self.assertEqual(response.status_code, 503)

    @patch(
        "qa.views.answer_question",
        side_effect=LLMGenerationError(
            "Generation failed."
        ),
    )
    def test_ask_question_handles_llm_generation_error(
        self,
        mock_answer,
    ):
        response = self.client.post(
            self.ask_url,
            {"question": "Test question"},
            format="json",
        )

        self.assertEqual(response.status_code, 503)

    def test_history_list_is_paginated(self):
        QuestionAnswer.objects.bulk_create([
            QuestionAnswer(
                question=f"Question {index}",
                answer="Answer",
            )
            for index in range(22)
        ])

        response = self.client.get(
            f"{self.history_url}?page_size=5"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 22)
        self.assertEqual(len(response.data["results"]), 5)
        self.assertIsNotNone(response.data["next"])

        self.assertNotIn(
            "sources",
            response.data["results"][0],
        )

    def test_history_detail_includes_sources(self):
        record = self.create_record()

        response = self.client.get(
            f"{self.history_url}{record.pk}/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["sources"],
            record.sources,
        )

    def test_history_detail_returns_404_for_missing_record(self):
        response = self.client.get(
            f"{self.history_url}99999/"
        )

        self.assertEqual(response.status_code, 404)

    def test_history_status_identifies_no_answer(self):
        record = QuestionAnswer.objects.create(
            question="Unknown question",
            answer=NO_ANSWER_MESSAGE,
            sources=[],
        )

        response = self.client.get(
            f"{self.history_url}{record.pk}/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["status"],
            "no_answer",
        )