
# System Architecture & Technical Documentation

## 1. Project Overview

RAG Document System is a document-based question-answering application.

The system allows users to upload DOCX documents, extract their text, divide the content into smaller chunks, generate vector embeddings, and store them in a PostgreSQL database with pgvector.

Users can then ask questions about the uploaded documents. The system retrieves relevant content and uses a Large Language Model (LLM) to generate answers based only on the retrieved information.

## 2. Technology Stack

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
| Containerization | Docker and Docker Compose |

## 3. High-Level Architecture

The application consists of the following main components:

### 3.1 API Layer

Django REST Framework handles incoming HTTP requests.

It provides endpoints for:
- Uploading, listing, retrieving, updating, and deleting documents.
- Asking questions about documents.
- Retrieving question history.

### 3.2 Document Processing Layer

The document processing layer is responsible for:
- Reading DOCX files.
- Extracting paragraphs and table content.
- Splitting extracted text into smaller chunks.
- Generating embeddings for each chunk.
- Saving document content and embeddings in the database.

### 3.3 Vector Search Layer

The vector search layer converts user questions into embeddings and searches for the most relevant document chunks using cosine distance.

Only completed documents with available embeddings are included in the search.

### 3.4 RAG Layer

The RAG layer coordinates the question-answering process.

It retrieves relevant chunks, applies the similarity threshold, builds the context, and sends the question and context to the language model.

### 3.5 LLM Layer

The LLM layer uses LangChain and OpenRouter to communicate with the configured language model.

The model receives the user's question and retrieved document context and generates an answer based on the provided information.

## 4. Document Processing Workflow

When a document is uploaded, the following steps take place:

1. The API validates the uploaded file.
2. The document record is created in the database.
3. The document status changes to `processing`.
4. The DOCX file is opened and its paragraphs and tables are extracted.
5. The extracted text is divided into chunks.
6. Embeddings are generated for all chunks.
7. Existing chunks for the document are replaced with the newly generated chunks.
8. The document's full text is saved.
9. The document status changes to `completed`.

If processing fails, the document status changes to `failed` and the error message is stored.

## 5. Text Chunking Strategy

The system uses a token-based chunking strategy.

| Setting | Value |
|---|---|
| Chunk Size | 450 tokens |
| Chunk Overlap | 60 tokens |
| Chunk Step | 390 tokens |

The overlap helps preserve context between neighboring chunks and reduces the risk of losing information at chunk boundaries.

## 6. Embedding Strategy

The system uses the `intfloat/multilingual-e5-small` embedding model through FastEmbed.

| Setting | Value |
|---|---|
| Model | multilingual-e5-small |
| Vector Dimensions | 384 |
| Document Prefix | passage: |
| Query Prefix | query: |

Each document chunk is converted into a 384-dimensional vector and stored in PostgreSQL using pgvector.

The same embedding model is used to convert user questions into vectors.

## 7. Question Answering Workflow

When a user submits a question:

1. The API validates the question and optional document ID.
2. The question is converted into an embedding.
3. The system searches for the most similar document chunks.
4. The search results are ordered by cosine distance.
5. The system keeps only chunks that satisfy the configured similarity threshold.
6. If no relevant chunks are found, the system returns a predefined no-answer response without calling the LLM.
7. Otherwise, the retrieved chunks are assembled into a context.
8. The question and context are sent to the language model through OpenRouter.
9. The generated answer is checked for the insufficient-context marker.
10. The question, answer, and source information are stored in the database.
11. The API returns the answer and its sources.

## 8. Retrieval Configuration

| Setting | Value |
|---|---|
| Default Top-K | 5 |
| Maximum Cosine Distance | 0.20 |
| Similarity Calculation | 1 - Cosine Distance |

A lower cosine distance indicates greater similarity.

The similarity threshold prevents unrelated document chunks from being passed to the language model.

## 9. Database Design

The system uses three main data models.

### 9.1 Document

Stores uploaded document information.

Important fields:
- `title`
- `file`
- `full_text`
- `status`
- `error_message`
- `created_at`
- `updated_at`

### 9.2 DocumentChunk

Stores the extracted and divided document content.

Important fields:
- `document`
- `content`
- `chunk_index`
- `embedding`
- `metadata`
- `created_at`

Each chunk belongs to one document.

### 9.3 QuestionAnswer

Stores question-answering history.

Important fields:
- `question`
- `answer`
- `sources`
- `created_at`

The answer status returned by the API is calculated from the answer content and is not stored as a separate database field.

## 10. Error Handling and Reliability

The system handles several failure scenarios:

- Invalid document uploads are rejected by validation.
- Documents without readable text cannot be processed successfully.
- If processing a newly uploaded document fails, its status changes to `failed`. If processing a replacement file during an update fails, the previous document state is restored.
- Invalid questions are rejected by the API.
- LLM configuration or generation errors return an HTTP 503 response.
- Questions without relevant document content receive a no-answer response.

During document updates, if processing a replacement file fails, the previous document information and file are restored.

## 11. API and Documentation Endpoints

| Endpoint | Description |
|---|---|
| `/api/documents/` | Document list and upload |
| `/api/documents/{id}/` | Document details, update, and deletion |
| `/api/qa/ask/` | Question answering |
| `/api/qa/history/` | Question history |
| `/api/qa/history/{id}/` | Question history details |
| `/api/docs/` | Swagger UI |
| `/api/redoc/` | ReDoc |
| `/api/schema/` | OpenAPI schema |

## 12. Deployment Architecture

The project uses Docker Compose to run its application services.

The application backend runs in a Django container, while PostgreSQL with pgvector provides persistent database storage.

Environment variables are used for configuration, including database connection settings and external LLM credentials.

The current Docker configuration is intended for development and testing rather than production deployment.
