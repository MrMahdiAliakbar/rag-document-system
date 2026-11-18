
import tempfile
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings

from docx import Document as WordDocument
from rest_framework.test import APIClient

from .chunking import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    split_text_into_chunks,
)
from .embedding_service import (
    MODEL_DIMENSIONS,
    encode_texts,
    generate_query_embedding,
)
from .models import Document, DocumentChunk
from .search import search_similar_chunks
from .services import extract_document_text, process_document
from .validators import (
    MAX_DOCUMENT_SIZE,
    validate_document_size,
)


def create_docx():
    word_document = WordDocument()
    word_document.add_paragraph("Document introduction.")

    table = word_document.add_table(
        rows=2,
        cols=2,
    )

    table.cell(0, 0).text = "Name"
    table.cell(0, 1).text = "Value"
    table.cell(1, 0).text = "Python"
    table.cell(1, 1).text = "Programming language"

    buffer = BytesIO()
    word_document.save(buffer)

    return buffer.getvalue()


def uploaded_docx(name="document.docx"):
    return SimpleUploadedFile(
        name,
        create_docx(),
        content_type=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
    )


class DocumentValidatorTests(SimpleTestCase):
    def test_accepts_file_within_size_limit(self):
        file = SimpleNamespace(
            size=MAX_DOCUMENT_SIZE
        )

        self.assertIsNone(
            validate_document_size(file)
        )

    def test_rejects_file_over_size_limit(self):
        file = SimpleNamespace(
            size=MAX_DOCUMENT_SIZE + 1
        )

        with self.assertRaises(ValidationError):
            validate_document_size(file)


class DocumentExtractionTests(SimpleTestCase):
    def test_extracts_paragraphs_and_tables(self):
        content = extract_document_text(
            BytesIO(create_docx())
        )

        self.assertIn(
            "Document introduction.",
            content,
        )
        self.assertIn("[TABLE]", content)
        self.assertIn("Name | Value", content)
        self.assertIn(
            "Python | Programming language",
            content,
        )

    def test_rejects_document_without_readable_text(self):
        word_document = WordDocument()
        buffer = BytesIO()
        word_document.save(buffer)
        buffer.seek(0)

        with self.assertRaisesMessage(
            ValueError,
            "No readable text was found in the document.",
        ):
            extract_document_text(buffer)


class FakeTokenizer:
    def encode(self, text, add_special_tokens=False):
        return SimpleNamespace(
            ids=list(range(len(text.split())))
        )

    def decode(self, token_ids, skip_special_tokens=True):
        return " ".join(
            str(token_id)
            for token_id in token_ids
        )


class ChunkingTests(SimpleTestCase):
    @patch("documents.chunking.get_tokenizer")
    def test_returns_empty_list_for_empty_text(self, mock_get):
        mock_get.return_value = FakeTokenizer()

        self.assertEqual(
            split_text_into_chunks(""),
            [],
        )

    @patch("documents.chunking.get_tokenizer")
    def test_splits_text_using_configured_chunk_size(self, mock_get):
        mock_get.return_value = FakeTokenizer()

        text = " ".join(
            f"word{index}"
            for index in range(CHUNK_SIZE + 100)
        )

        chunks = split_text_into_chunks(text)

        self.assertEqual(len(chunks), 2)
        self.assertEqual(
            len(chunks[0].split()),
            CHUNK_SIZE,
        )
        self.assertEqual(
            len(chunks[1].split()),
            100 + CHUNK_OVERLAP,
        )

    @patch("documents.chunking.get_tokenizer")
    def test_chunks_preserve_overlap(self, mock_get):
        mock_get.return_value = FakeTokenizer()

        text = " ".join(
            f"word{index}"
            for index in range(CHUNK_SIZE + 1)
        )

        chunks = split_text_into_chunks(text)

        first_tokens = chunks[0].split()
        second_tokens = chunks[1].split()

        self.assertEqual(
            first_tokens[-CHUNK_OVERLAP:],
            second_tokens[:CHUNK_OVERLAP],
        )


class FakeEmbeddingModel:
    def __init__(self, vectors=None):
        self.vectors = vectors
        self.received_texts = []

    def embed(self, texts, batch_size=16):
        self.received_texts = list(texts)

        if self.vectors is not None:
            return iter(self.vectors)

        return iter([
            [0.1] * MODEL_DIMENSIONS
            for _ in texts
        ])


class EmbeddingTests(SimpleTestCase):
    @patch("documents.embedding_service.get_embedding_model")
    def test_encodes_texts_with_prefix(self, mock_get):
        model = FakeEmbeddingModel()
        mock_get.return_value = model

        vectors = encode_texts(
            ["Example text"],
            "passage",
        )

        self.assertEqual(len(vectors), 1)
        self.assertEqual(
            len(vectors[0]),
            MODEL_DIMENSIONS,
        )
        self.assertEqual(
            model.received_texts,
            ["passage: Example text"],
        )

    @patch("documents.embedding_service.get_embedding_model")
    def test_returns_empty_list_for_empty_input(self, mock_get):
        self.assertEqual(
            encode_texts([], "passage"),
            [],
        )
        mock_get.assert_not_called()

    @patch("documents.embedding_service.get_embedding_model")
    def test_rejects_unexpected_vector_dimensions(self, mock_get):
        mock_get.return_value = FakeEmbeddingModel(
            vectors=[[0.1, 0.2]]
        )

        with self.assertRaises(ValueError):
            encode_texts(
                ["Example"],
                "passage",
            )

    @patch("documents.embedding_service.encode_texts")
    def test_query_embedding_rejects_empty_query(self, mock_encode):
        with self.assertRaises(ValueError):
            generate_query_embedding("   ")

        mock_encode.assert_not_called()


class DocumentDatabaseTestCase(TestCase):
    def setUp(self):
        super().setUp()

        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.enterContext(
            override_settings(
                MEDIA_ROOT=self.temp_dir.name
            )
        )

    def create_document(self, title="Test document"):
        return Document.objects.create(
            title=title,
            file=uploaded_docx(),
        )


class DocumentProcessingTests(DocumentDatabaseTestCase):
    @patch("documents.services.generate_passage_embeddings")
    @patch("documents.services.split_text_into_chunks")
    def test_process_document_saves_text_chunks_and_embeddings(
        self,
        mock_split,
        mock_embeddings,
    ):
        document = self.create_document()

        mock_split.return_value = [
            "First chunk",
            "Second chunk",
        ]
        mock_embeddings.return_value = [
            [0.1] * MODEL_DIMENSIONS,
            [0.2] * MODEL_DIMENSIONS,
        ]

        result = process_document(document)

        document.refresh_from_db()

        self.assertTrue(result)
        self.assertEqual(
            document.status,
            Document.Status.COMPLETED,
        )
        self.assertIn(
            "Document introduction.",
            document.full_text,
        )
        self.assertEqual(
            document.chunks.count(),
            2,
        )
        self.assertEqual(
            document.chunks.get(chunk_index=0).content,
            "First chunk",
        )

    @patch(
        "documents.services.generate_passage_embeddings",
        side_effect=RuntimeError("Embedding failed."),
    )
    @patch(
        "documents.services.split_text_into_chunks",
        return_value=["New chunk"],
    )
    def test_processing_failure_marks_document_as_failed(
        self,
        mock_split,
        mock_embeddings,
    ):
        document = self.create_document()

        result = process_document(document)

        document.refresh_from_db()

        self.assertFalse(result)
        self.assertEqual(
            document.status,
            Document.Status.FAILED,
        )
        self.assertIn(
            "Embedding failed.",
            document.error_message,
        )

    @patch(
        "documents.services.generate_passage_embeddings",
        side_effect=RuntimeError("Embedding failed."),
    )
    @patch(
        "documents.services.split_text_into_chunks",
        return_value=["New chunk"],
    )
    def test_processing_failure_preserves_existing_chunks(
        self,
        mock_split,
        mock_embeddings,
    ):
        document = self.create_document()

        DocumentChunk.objects.create(
            document=document,
            content="Existing chunk",
            chunk_index=0,
            embedding=[0.1] * MODEL_DIMENSIONS,
        )

        process_document(document)

        self.assertEqual(
            document.chunks.count(),
            1,
        )
        self.assertEqual(
            document.chunks.first().content,
            "Existing chunk",
        )


class DocumentSearchTests(DocumentDatabaseTestCase):
    def setUp(self):
        super().setUp()

        self.completed_document = self.create_document(
            "Completed document"
        )
        self.completed_document.status = Document.Status.COMPLETED
        self.completed_document.save(
            update_fields=["status"]
        )

        self.pending_document = self.create_document(
            "Pending document"
        )

        self.vector = [1.0] + [0.0] * (
            MODEL_DIMENSIONS - 1
        )

    @patch(
        "documents.search.generate_query_embedding"
    )
    def test_search_returns_nearest_completed_chunks(
        self,
        mock_embedding,
    ):
        mock_embedding.return_value = self.vector

        nearest = DocumentChunk.objects.create(
            document=self.completed_document,
            content="Nearest result",
            chunk_index=0,
            embedding=self.vector,
        )

        DocumentChunk.objects.create(
            document=self.completed_document,
            content="Different vector",
            chunk_index=1,
            embedding=[0.0, 1.0] + [0.0] * (
                MODEL_DIMENSIONS - 2
            ),
        )

        DocumentChunk.objects.create(
            document=self.pending_document,
            content="Pending result",
            chunk_index=0,
            embedding=self.vector,
        )

        results = search_similar_chunks(
            "test query",
            top_k=5,
        )

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].pk, nearest.pk)

    @patch(
        "documents.search.generate_query_embedding"
    )
    def test_search_filters_by_document_id(
        self,
        mock_embedding,
    ):
        mock_embedding.return_value = self.vector

        another_document = self.create_document(
            "Another completed document"
        )
        another_document.status = Document.Status.COMPLETED
        another_document.save(
            update_fields=["status"]
        )

        DocumentChunk.objects.create(
            document=self.completed_document,
            content="First document result",
            chunk_index=0,
            embedding=self.vector,
        )

        DocumentChunk.objects.create(
            document=another_document,
            content="Second document result",
            chunk_index=0,
            embedding=self.vector,
        )

        results = search_similar_chunks(
            "test query",
            document_id=another_document.pk,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0].document_id,
            another_document.pk,
        )

        results = search_similar_chunks(
            "test query",
            document_id=self.pending_document.pk,
        )

        self.assertEqual(results, [])

    def test_search_rejects_empty_query(self):
        with self.assertRaises(ValueError):
            search_similar_chunks("   ")

    def test_search_rejects_invalid_top_k(self):
        with self.assertRaises(ValueError):
            search_similar_chunks(
                "test query",
                top_k=0,
            )


class DocumentAPITests(DocumentDatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.list_url = "/api/documents/"

    @patch("documents.views.process_document")
    def test_upload_document(self, mock_process):
        def complete_document(document):
            document.status = Document.Status.COMPLETED
            document.save(update_fields=["status"])
            return True

        mock_process.side_effect = complete_document

        response = self.client.post(
            self.list_url,
            {
                "title": "API document",
                "file": uploaded_docx(),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.data["title"],
            "API document",
        )
        self.assertEqual(
            response.data["status"],
            Document.Status.COMPLETED,
        )
        self.assertIn("chunk_count", response.data)

    def test_put_updates_document_title(self):
        document = self.create_document()

        response = self.client.put(
            f"{self.list_url}{document.pk}/",
            {"title": "Replaced title"},
            format="multipart",
        )

        document.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(document.title, "Replaced title")

    def test_upload_rejects_non_docx_file(self):
        response = self.client.post(
            self.list_url,
            {
                "title": "Invalid document",
                "file": SimpleUploadedFile(
                    "document.txt",
                    b"Invalid content",
                ),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Document.objects.count(), 0)

    def test_upload_rejects_empty_file(self):
        response = self.client.post(
            self.list_url,
            {
                "title": "Empty document",
                "file": SimpleUploadedFile(
                    "empty.docx",
                    b"",
                ),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)

    def test_upload_rejects_empty_title(self):
        response = self.client.post(
            self.list_url,
            {
                "title": "   ",
                "file": uploaded_docx(),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)

    def test_list_documents(self):
        self.create_document()

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_document(self):
        document = self.create_document()

        response = self.client.get(
            f"{self.list_url}{document.pk}/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["title"],
            document.title,
        )
        self.assertNotIn("full_text", response.data)
        self.assertNotIn("error_message", response.data)

    def test_patch_updates_title_without_reprocessing(self):
        document = self.create_document()

        with patch(
            "documents.views.process_document"
        ) as mock_process:
            response = self.client.patch(
                f"{self.list_url}{document.pk}/",
                {"title": "Updated title"},
                format="multipart",
            )

        document.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(document.title, "Updated title")
        mock_process.assert_not_called()

    @patch("documents.views.process_document")
    def test_patch_replaces_file_and_reprocesses(
        self,
        mock_process,
    ):
        def complete_document(document):
            document.status = Document.Status.COMPLETED
            document.full_text = "Updated content"
            document.save(
                update_fields=["status", "full_text"]
            )
            return True

        mock_process.side_effect = complete_document

        document = self.create_document()
        old_file_name = document.file.name

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.patch(
                f"{self.list_url}{document.pk}/",
                {"file": uploaded_docx("replacement.docx")},
                format="multipart",
            )

        document.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(
            document.file.name,
            old_file_name,
        )
        self.assertEqual(
            document.full_text,
            "Updated content",
        )
        mock_process.assert_called_once()

        self.assertFalse(
            Path(self.temp_dir.name, old_file_name).exists()
        )

    @patch(
        "documents.views.process_document",
        return_value=False,
    )
    def test_failed_file_replacement_restores_old_document(
        self,
        mock_process,
    ):
        document = self.create_document()
        old_file_name = document.file.name
        old_title = document.title

        response = self.client.patch(
            f"{self.list_url}{document.pk}/",
            {
                "title": "New title",
                "file": uploaded_docx("replacement.docx"),
            },
            format="multipart",
        )

        document.refresh_from_db()

        self.assertEqual(response.status_code, 422)
        self.assertEqual(document.file.name, old_file_name)
        self.assertEqual(document.title, old_title)
        self.assertTrue(
            Path(self.temp_dir.name, old_file_name).exists()
        )

    def test_delete_document_removes_record_and_file(self):
        document = self.create_document()
        file_path = Path(
            self.temp_dir.name,
            document.file.name,
        )

        self.assertTrue(file_path.exists())

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.delete(
                f"{self.list_url}{document.pk}/"
            )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            Document.objects.filter(pk=document.pk).exists()
        )
        self.assertFalse(file_path.exists())

    def test_retrieve_missing_document_returns_404(self):
        response = self.client.get(
            f"{self.list_url}99999/"
        )

        self.assertEqual(response.status_code, 404)