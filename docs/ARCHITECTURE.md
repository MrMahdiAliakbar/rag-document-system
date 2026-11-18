**🇬🇧 English** | [🇮🇷 فارسی](ARCHITECTURE.fa.md)

# 🏗️ System Architecture & Technical Documentation

This document explains the architecture, internal components, data flow, processing strategies, and technical decisions of the RAG Document System.

## 📑 Table of Contents

- [Project Overview](#-project-overview)
- [Technology Stack](#-technology-stack)
- [High-Level Architecture](#-high-level-architecture)
- [Document Processing Workflow](#-document-processing-workflow)
- [Text Chunking Strategy](#-text-chunking-strategy)
- [Embedding Strategy](#-embedding-strategy)
- [Vector Search](#-vector-search)
- [Question Answering Workflow](#-question-answering-workflow)
- [Retrieval Configuration](#-retrieval-configuration)
- [Database Design](#-database-design)
- [Error Handling and Reliability](#-error-handling-and-reliability)
- [API Architecture](#-api-architecture)
- [Deployment Architecture](#-deployment-architecture)

---

## 📌 Project Overview

RAG Document System is a document-based question-answering application built using Retrieval-Augmented Generation (RAG).

The system allows users to upload DOCX documents, extract their text, divide the content into smaller chunks, generate vector embeddings, and store them in a PostgreSQL database with pgvector.

Users can then ask questions about the uploaded documents. The system retrieves relevant content and uses a Large Language Model (LLM) to generate answers based on the retrieved information.

The main objective is to provide answers grounded in the uploaded documents rather than relying solely on the language model's general knowledge.

---

## 🧰 Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python 3.13 |
| Backend Framework | Django |
| REST API | Django REST Framework |
| API Documentation | drf-spectacular |
| Database | PostgreSQL |
| Vector Search | pgvector |
| Embedding Model | intfloat/multilingual-e5-small |
| Embedding Library | FastEmbed |
| LLM Integration | LangChain and OpenRouter |
| Document Processing | python-docx |
| Tokenization | Hugging Face Tokenizers |
| Containerization | Docker and Docker Compose |

---

## 🧩 High-Level Architecture

The application consists of several layers that work together to process documents and answer questions.

### 3.1 API Layer

Django REST Framework handles incoming HTTP requests and exposes the application's functionality.

It provides endpoints for:

- Uploading, listing, retrieving, updating, and deleting documents.
- Asking questions about uploaded documents.
- Retrieving question history.

### 3.2 Document Processing Layer

The document processing layer is responsible for transforming uploaded DOCX files into searchable content.

Its responsibilities include:

- Reading DOCX files.
- Extracting paragraph and table content.
- Splitting extracted text into smaller chunks.
- Generating embeddings for each chunk.
- Saving document content and embeddings in the database.

### 3.3 Vector Search Layer

The vector search layer converts user questions into embeddings and searches for the most relevant document chunks using cosine distance.

Only chunks with available embeddings belonging to completed documents are included in retrieval.

### 3.4 RAG Layer

The RAG layer coordinates the question-answering process.

It retrieves relevant chunks, applies the configured distance threshold, builds the context, and sends the question and retrieved context to the language model.

### 3.5 LLM Layer

The LLM layer uses LangChain and OpenRouter to communicate with the configured language model.

The model receives the user's question and retrieved document context and generates an answer based on the provided information.

---

## 📄 Document Processing Workflow

When a document is uploaded, the following steps take place:

1. The API validates the uploaded file.
2. A document record is created in the database.
3. The document status changes to `processing`.
4. The DOCX file is opened.
5. Paragraphs and table contents are extracted.
6. The extracted text is divided into chunks using the token-based chunking strategy.
7. Embeddings are generated for the chunks.
8. The system checks that the number of generated embeddings matches the number of chunks.
9. Existing chunks for the document are replaced with the newly generated chunks inside a database transaction.
10. The extracted full text is saved.
11. The document status changes to `completed`.

If processing a newly uploaded document fails, its status changes to `failed` and the error message is stored.

When an existing document is updated with a replacement file, the previous document information and file are restored if processing the replacement fails.

---

## ✂️ Text Chunking Strategy

The system uses a token-based chunking strategy.

The tokenizer is loaded for the `intfloat/multilingual-e5-small` model.

| Setting | Value |
|---|---|
| Chunk Size | 450 tokens |
| Chunk Overlap | 60 tokens |
| Chunk Step | 390 tokens |

The chunk step is calculated as:

`Chunk Step = Chunk Size - Chunk Overlap`

The overlap preserves some context between neighboring chunks and reduces the risk of losing information at chunk boundaries.

---

## 🧠 Embedding Strategy

The system uses the `intfloat/multilingual-e5-small` embedding model through FastEmbed.

| Setting | Value |
|---|---|
| Model | intfloat/multilingual-e5-small |
| Vector Dimensions | 384 |
| Document Prefix | `passage:` |
| Query Prefix | `query:` |
| Embedding Batch Size | 16 |

Each document chunk is converted into a 384-dimensional vector and stored in PostgreSQL using pgvector.

User questions are converted into vectors using the same embedding model.

The model uses different prefixes for document passages and search queries to support its intended retrieval behavior.

---

## 🔎 Vector Search

The vector search process converts a user's question into an embedding and compares it with the stored document chunk embeddings.

The system uses cosine distance to measure how close the question vector is to each document chunk vector.

The search process:

1. Generates an embedding for the user's question.
2. Selects chunks with non-null embeddings.
3. Includes only chunks belonging to documents with `completed` status.
4. Optionally filters the search by `document_id`.
5. Calculates cosine distance between the query vector and stored vectors.
6. Orders the results by ascending cosine distance.
7. Returns up to the configured Top-K number of chunks.

A lower cosine distance indicates greater similarity.

---

## 💬 Question Answering Workflow

When a user submits a question:

1. The API validates the question and optional document ID.
2. The question is converted into an embedding.
3. The system searches for the most similar document chunks.
4. The search results are ordered by cosine distance.
5. The system keeps only chunks that satisfy the configured maximum cosine distance.
6. If no relevant chunks are found, the system returns a predefined no-answer response without calling the LLM.
7. Otherwise, the retrieved chunks are converted into source records and assembled into a context.
8. The question and context are sent to the language model through OpenRouter.
9. The generated answer is checked for the insufficient-context marker.
10. If the marker is present, the system replaces the generated answer with the predefined no-answer response.
11. The question, answer, and source information are stored in the database.
12. The API returns the answer, source information, and LLM usage status.

The system therefore has two possible no-answer scenarios:

- **No relevant chunks found:** The LLM is not called, and `used_llm` is `false`.
- **Insufficient context identified by the LLM:** The LLM is called, but the final response is replaced with the predefined no-answer message. In this case, `used_llm` is `true`.

---

## ⚙️ Retrieval Configuration

| Setting | Default Value |
|---|---|
| Default Top-K | 5 |
| Maximum Cosine Distance | 0.20 |
| Similarity Calculation | 1 - Cosine Distance |

These settings control how many chunks are retrieved and how relevant they must be to enter the final context.

The similarity threshold prevents unrelated document chunks from being passed to the language model.

---

## 🗄️ Database Design

The system uses three main data models.

### 10.1 Document

Stores uploaded document information.

Important fields:

- `title`: Document title.
- `file`: Uploaded DOCX file.
- `full_text`: Extracted document text.
- `status`: Document processing status.
- `error_message`: Processing error details.
- `created_at`: Record creation timestamp.
- `updated_at`: Last update timestamp.

Document status values:

| Status | Description |
|---|---|
| `pending` | Document created but not yet processed |
| `processing` | Document processing is in progress |
| `completed` | Document processing completed successfully |
| `failed` | Document processing failed |

### 10.2 DocumentChunk

Stores the extracted and divided document content.

Important fields:

- `document`: Reference to the parent document.
- `content`: Text content of the chunk.
- `chunk_index`: Position of the chunk within the document.
- `embedding`: 384-dimensional vector representation.
- `metadata`: Additional chunk information.
- `created_at`: Record creation timestamp.

Each chunk belongs to one document. Deleting a document also deletes its associated chunks.

### 10.3 QuestionAnswer

Stores question-answering history.

Important fields:

- `question`: Submitted question.
- `answer`: Generated or predefined answer.
- `sources`: Retrieved source information stored as JSON.
- `created_at`: Record creation timestamp.

The `answered` or `no_answer` status returned by the API is calculated from the answer content. It is not stored as a separate database field.

---

## 🛡️ Error Handling and Reliability

The system handles several failure scenarios:

- Invalid document uploads are rejected by validation.
- Documents without readable text cannot be processed successfully.
- If processing a newly uploaded document fails, its status changes to `failed` and the error message is stored.
- If processing a replacement file during an update fails, the previous document information and file are restored, and the API returns HTTP `422`.
- Invalid questions are rejected by the API.
- LLM configuration or generation errors return HTTP `503`.
- Questions without relevant document content receive a predefined no-answer response.
- Database operations for replacing document chunks are performed inside a transaction to maintain data consistency.

---

## 🔌 API Architecture

The API is organized around three main functional areas.

| Endpoint | Description |
|---|---|
| `/api/documents/` | Document listing and upload |
| `/api/documents/{id}/` | Document retrieval, update, and deletion |
| `/api/qa/ask/` | Question answering |
| `/api/qa/history/` | Question history |
| `/api/qa/history/{id}/` | Question history details |
| `/api/docs/` | Swagger UI |
| `/api/redoc/` | ReDoc |
| `/api/schema/` | OpenAPI schema |

The document endpoints support document management, while the question-answering endpoints provide RAG functionality and access to previous interactions.

---

## 🐳 Deployment Architecture

The project uses Docker Compose to run its application services.

The current setup includes two main services:

### PostgreSQL Service

- Uses the `pgvector/pgvector` Docker image.
- Provides PostgreSQL database storage and vector search capabilities.
- Stores persistent database data in a Docker volume.
- Exposes the database port on `127.0.0.1:5432`.

### Django Web Service

- Builds the application from the project Dockerfile.
- Runs the Django development server.
- Exposes the application on port `8000`.
- Connects to the PostgreSQL service.
- Uses environment variables for application configuration.
- Uses a Docker volume for embedding model cache data.

The current Docker configuration is intended for development and testing rather than production deployment.