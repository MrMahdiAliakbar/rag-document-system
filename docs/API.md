**🇬🇧 English** \| [🇮🇷 فارسی](API.fa.md)

# 🔌 API Documentation

This document describes the REST API endpoints of the RAG Document System, including request formats, response structures, validation rules, and error handling.

## 📑 Table of Contents

- [Overview](#-overview)
- [API Endpoints](#-api-endpoints)
  - [Documents](#documents)
  - [Question Answering](#question-answering)
  - [Question History](#question-history)
- [Request and Response Examples](#-request-and-response-examples)
- [Validation Rules](#-validation-rules)
- [HTTP Status Codes](#-http-status-codes)
- [Interactive API Documentation](#-interactive-api-documentation)
- [Authentication](#-authentication)

---

## 🌐 Overview

The API is built with Django REST Framework and provides endpoints for document management, question answering, and question history.

**Base URL:**

```text
http://localhost:8000/api/
```

**Supported content types:**

- `application/json` for JSON requests.
- `multipart/form-data` for document uploads and file replacement.

---

## 📡 API Endpoints

### Documents

Documents are uploaded as DOCX files, processed, divided into chunks, and stored for retrieval.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/documents/` | Retrieve all documents |
| POST | `/api/documents/` | Upload a new document |
| GET | `/api/documents/{id}/` | Retrieve a specific document |
| PUT | `/api/documents/{id}/` | Update a document |
| PATCH | `/api/documents/{id}/` | Partially update a document |
| DELETE | `/api/documents/{id}/` | Delete a document |

**Upload a document**

`POST /api/documents/`

Request content type: `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | String | Yes | Document title |
| `file` | File | Yes | DOCX document |

**Update a document**

`PUT /api/documents/{id}/`

A PUT request updates a document using the supplied fields. The `title` field is required for a full update. A replacement file is optional.

`PATCH /api/documents/{id}/`

A PATCH request partially updates a document. Only the supplied fields are changed.

If a replacement file is uploaded, the document is processed again. If processing fails, the API returns `422 Unprocessable Entity` and restores the previous document state.

### Question Answering

The question-answering endpoint uses the RAG pipeline to retrieve relevant document chunks and generate an answer.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/qa/ask/` | Submit a question and receive an answer |

**Request body**

`POST /api/qa/ask/`

Content type: `application/json`

| Field | Type | Required | Description |
|---|---|---|---|
| `question` | String | Yes | User's question |
| `document_id` | Integer | No | Restrict retrieval to a specific document |

If `document_id` is omitted, retrieval can use the available documents.

The response includes the generated answer, retrieval sources, answer status, and information about whether the LLM was used.

### Question History

The question history endpoints allow users to retrieve previously submitted questions and their answers.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/qa/history/` | Retrieve question history |
| GET | `/api/qa/history/{id}/` | Retrieve a specific history record |

The history list uses page-number pagination. The default page size is 20 records. The `page_size` query parameter can be used to request a different page size, up to a maximum of 100.

Example:

```text
GET /api/qa/history/?page=2&page_size=10
```

The list response contains a summary of each record. The detail endpoint also includes the associated retrieval sources.

---

## 🧾 Request and Response Examples

### Document Upload

Example request fields:

```text
title: Library Guide
file: library_guide.docx
```

Example document response:

```json
{
  "id": 1,
  "title": "Library Guide",
  "file_name": "library_guide.docx",
  "status": "completed",
  "chunk_count": 3,
  "created_at": "2026-11-18T10:30:00Z",
  "updated_at": "2026-11-18T10:30:00Z"
}
```

### Ask a Question

Example request:

```json
{
  "question": "How many books can an undergraduate student borrow?",
  "document_id": 1
}
```

Example response:

```json
{
  "id": 12,
  "question": "How many books can an undergraduate student borrow?",
  "answer": "An undergraduate student can borrow ...",
  "status": "answered",
  "sources": [
    {
      "source_id": "S1",
      "document_id": 1,
      "document_title": "Library Guide",
      "chunk_index": 0,
      "similarity": 0.91,
      "distance": 0.09,
      "content": "..."
    }
  ],
  "used_llm": true,
  "created_at": "2026-11-18T10:30:00Z"
}
```

The values above are illustrative examples. Actual answers and source contents depend on the uploaded documents and the question.

**Response fields**

| Field | Description |
|---|---|
| `id` | Question-answer record ID |
| `question` | Submitted question |
| `answer` | Generated answer or predefined no-answer response |
| `status` | `answered` or `no_answer` |
| `sources` | Retrieved document chunks used as context |
| `used_llm` | Indicates whether the LLM was called |
| `created_at` | Record creation timestamp |

Each object in `sources` contains:

| Field | Description |
|---|---|
| `source_id` | Source reference such as `S1` |
| `document_id` | ID of the source document |
| `document_title` | Title of the source document |
| `chunk_index` | Index of the retrieved chunk |
| `similarity` | Similarity score |
| `distance` | Cosine distance |
| `content` | Retrieved chunk content |

### Question History

Example paginated response:

```json
{
  "count": 25,
  "next": "http://localhost:8000/api/qa/history/?page=2",
  "previous": null,
  "results": [
    {
      "id": 12,
      "question": "How many books can an undergraduate student borrow?",
      "answer": "An undergraduate student can borrow ...",
      "status": "answered",
      "created_at": "2026-11-18T10:30:00Z"
    }
  ]
}
```

The history detail endpoint includes the `sources` field in addition to the fields returned by the list endpoint.

---

## ✅ Validation Rules

### Document Upload and Update

- Only `.docx` files are accepted.
- The maximum file size is 10 MB.
- Empty files are rejected.
- The document title is required and cannot contain only whitespace.
- A replacement file is processed again before the update is considered successful.

### Question Submission

- The `question` field is required.
- Leading and trailing whitespace is removed.
- The maximum question length is 5,000 characters.
- If `document_id` is provided, it must be a valid ID of an existing document.

---

## ⚠️ HTTP Status Codes

| Status Code | Meaning | Common Usage |
|---|---|---|
| `200 OK` | Request successful | Retrieving or updating a resource |
| `201 Created` | Resource created | Successful document upload |
| `204 No Content` | Request successful without response body | Successful document deletion |
| `400 Bad Request` | Invalid request | Validation errors or invalid question input |
| `404 Not Found` | Resource not found | Requested document or history record does not exist |
| `422 Unprocessable Entity` | Processing failed | Replacement document could not be processed; previous document state is restored |
| `503 Service Unavailable` | Service unavailable | LLM configuration or generation failure |

The exact response depends on the endpoint and the type of error.

---

## 📚 Interactive API Documentation

The project provides three API documentation interfaces:

| Interface | URL | Purpose |
|---|---|---|
| Swagger UI | `/api/docs/` | Interactive API testing |
| ReDoc | `/api/redoc/` | Structured API reference |
| OpenAPI Schema | `/api/schema/` | Machine-readable API specification |

Open the following URLs after starting the application:

- Swagger: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`
- OpenAPI Schema: `http://localhost:8000/api/schema/`

---

## 🔐 Authentication

The current project does not implement API authentication or user authorization. The API endpoints are publicly accessible in the development configuration.

This behavior is intended for the current project scope and should not be considered a production-ready security configuration.