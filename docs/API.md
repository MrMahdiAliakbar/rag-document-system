
# API Documentation

## Base URL

```text
http://localhost:8000
```

All API endpoints use the `/api/` prefix.

## Interactive API Documentation

The project provides interactive API documentation through the following endpoints:

| Documentation | Endpoint |
|---|---|
| Swagger UI | `/api/docs/` |
| ReDoc | `/api/redoc/` |
| OpenAPI Schema | `/api/schema/` |

## 1. Document Management API

Base path: `/api/documents/`

### 1.1 List Documents

**Endpoint:**

`GET /api/documents/`

Returns a list of uploaded documents, ordered from newest to oldest.

**Successful response:** `200 OK`

### 1.2 Upload a Document

**Endpoint:**

`POST /api/documents/`

**Content-Type:** `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | string | Yes | Document title |
| `file` | file | Yes | DOCX document |

**Validation rules:**

- Only DOCX files are accepted.
- Empty files are rejected.
- The document title cannot be empty.
- The maximum file size is 10 MB.

**Successful response:** `201 Created`

The response includes the created document information and its processing status.

### 1.3 Retrieve a Document

**Endpoint:**

`GET /api/documents/{id}/`

Returns the information of a specific document.

**Successful response:** `200 OK`

Returns `404 Not Found` if the document does not exist.

### 1.4 Update a Document

**Endpoint:**

`PUT /api/documents/{id}/`

**Content-Type:** `multipart/form-data`

Replaces the document information.

The title is required. A replacement file can also be provided.

When a new file is uploaded, the document is processed again.

**Successful response:** `200 OK`

### 1.5 Partially Update a Document

**Endpoint:**

`PATCH /api/documents/{id}/`

**Content-Type:** `multipart/form-data`

Updates only the provided fields.

Available fields:

- `title`
- `file`

Changing only the title does not require document reprocessing.

**Successful response:** `200 OK`

### 1.6 Delete a Document

**Endpoint:**

`DELETE /api/documents/{id}/`

Deletes the selected document and its associated data.

**Successful response:** `204 No Content`

## 2. Question Answering API

Base path: `/api/qa/`

### 2.1 Ask a Question

**Endpoint:**

`POST /api/qa/ask/`

**Content-Type:** `application/json`

**Request body:**

```json
{
  "question": "How many books can an undergraduate student borrow?",
  "document_id": 1
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `question` | string | Yes | User question |
| `document_id` | integer | No | Optional document ID to restrict retrieval |

If `document_id` is omitted, the system searches across all completed documents.

**Successful response:** `200 OK`

The response includes:

- `id`: Question history record ID
- `question`: Submitted question
- `answer`: Generated answer
- `status`: Answer status
- `sources`: Retrieved document chunks
- `used_llm`: Indicates whether the language model was called
- `created_at`: Creation timestamp

The status can be:

- `answered`
- `no_answer`

When relevant information is not found, the system returns the standard no-answer message and does not call the language model.

## 3. Question History API

### 3.1 List Question History

**Endpoint:**

`GET /api/qa/history/`

Returns previous questions and their answers, ordered from newest to oldest.

**Successful response:** `200 OK`

The endpoint supports page-number pagination.

| Parameter | Description |
|---|---|
| `page` | Page number |
| `page_size` | Number of records per page |

Default page size: `20`

Maximum page size: `100`

**Example:**

`GET /api/qa/history/?page=1&page_size=10`

The list response includes the question, answer, status, and creation timestamp.

### 3.2 Retrieve a History Record

**Endpoint:**

`GET /api/qa/history/{id}/`

Returns the details of a specific question-answer record, including its source information.

**Successful response:** `200 OK`

Returns `404 Not Found` if the record does not exist.

## 4. Common HTTP Status Codes

| Status Code | Description |
|---|---|
| `200 OK` | Request completed successfully |
| `201 Created` | Resource created successfully |
| `204 No Content` | Resource deleted successfully |
| `400 Bad Request` | Invalid request data |
| `404 Not Found` | Requested resource does not exist |
| `422 Unprocessable Entity` | Document processing failed |
| `503 Service Unavailable` | Language model service is unavailable |

## 5. Important Notes

- The current API does not require authentication.
- Document uploads are limited to DOCX files.
- Document processing includes text extraction, chunking, and embedding generation.
- Question answering uses retrieved document chunks as context.
- Answers can include source identifiers to indicate the retrieved information.
- The system avoids generating answers when relevant context is insufficient.
- The `status` returned by the question-answering API is calculated from the answer content and is not a separate database field.
