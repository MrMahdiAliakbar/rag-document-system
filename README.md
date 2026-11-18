
# RAG Document System

English | [Persian](README.fa.md)

A document-based question-answering system built with Django REST Framework and Retrieval-Augmented Generation (RAG).

The system allows users to upload DOCX documents, retrieve relevant information through semantic search, and ask questions based on the uploaded content. It uses a Large Language Model (LLM) to generate answers grounded in retrieved document content and provides relevant sources alongside the answers.

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [RAG Pipeline](#rag-pipeline)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Getting Started](#getting-started)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Configure Environment Variables](#2-configure-environment-variables)
  - [3. Run with Docker Compose](#3-run-with-docker-compose)
  - [4. Apply Database Migrations](#4-apply-database-migrations)
  - [5. Create a Superuser](#5-create-a-superuser)
- [API Documentation](#api-documentation)
- [API Endpoints](#api-endpoints)
- [Running Tests](#running-tests)
- [Configuration](#configuration)
- [Current Limitations](#current-limitations)

## Overview

RAG Document System is a backend application designed to provide question-answering capabilities over user-uploaded documents.

Instead of relying only on the general knowledge of a language model, the system retrieves relevant passages from uploaded documents and uses them as context for generating answers.

The application provides document management, semantic search, retrieval-augmented question answering, source references, and question history through a RESTful API. It also includes a Django Admin interface for managing application data.

## Key Features

- **Document Upload:** Upload DOCX files for processing and indexing.
- **Document Management:** Retrieve, update, and delete uploaded documents.
- **Text Extraction:** Extract text from document paragraphs and tables.
- **Text Chunking:** Split extracted content into smaller overlapping chunks.
- **Vector Embeddings:** Generate multilingual embeddings for document chunks.
- **Semantic Search:** Retrieve relevant document chunks using vector similarity.
- **RAG-based Question Answering:** Generate answers using retrieved document content as context.
- **Source References:** Return relevant document passages associated with generated answers.
- **Question History:** Store questions, answers, statuses, and retrieved sources.
- **REST API:** Provide application functionality through documented API endpoints.
- **Django Admin:** Manage documents and application records through the administration interface.
- **Docker Support:** Run the application and PostgreSQL database using Docker Compose.

## System Architecture

The application follows a modular Django architecture with separate components for document management and question answering.

### Main Components

- **Django REST Framework:** Exposes the application's functionality through REST API endpoints.
- **Documents App:** Handles document upload, validation, text extraction, chunking, embedding generation, and document management.
- **QA App:** Handles question submission, semantic retrieval, LLM integration, answer generation, and question history.
- **PostgreSQL + pgvector:** Stores application data and vector embeddings.
- **FastEmbed:** Generates vector embeddings from document chunks and user questions.
- **LangChain:** Integrates the retrieval-augmented generation workflow with the language model.
- **OpenRouter:** Provides access to the configured language model.
- **Django Admin:** Provides an administrative interface for managing application data.

## RAG Pipeline

The question-answering process follows these steps:

1. A user uploads a DOCX document.
2. The system validates the uploaded file.
3. Text is extracted from paragraphs and tables.
4. The extracted text is divided into overlapping chunks.
5. FastEmbed generates vector embeddings for the chunks.
6. The document chunks and their embeddings are stored in PostgreSQL with pgvector.
7. A user submits a question through the REST API.
8. The question is converted into a vector embedding.
9. Semantic search retrieves the most relevant document chunks.
10. The retrieved content is provided to the language model as context.
11. The LLM generates an answer based on the retrieved content.
12. The answer, its status, and relevant source references are stored in the question history and returned to the user.

If no sufficiently relevant sources are found, the system does not generate an answer from unrelated document content.

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python 3.13 |
| Backend Framework | Django 6.1 |
| REST API | Django REST Framework 3.18 |
| API Documentation | drf-spectacular |
| Database | PostgreSQL 16 |
| Vector Search | pgvector 0.8.7 |
| Embedding Model | intfloat/multilingual-e5-small |
| Embedding Library | FastEmbed |
| Vector Dimensions | 384 |
| RAG Integration | LangChain |
| LLM Provider | OpenRouter |
| Default LLM Model | qwen/qwen3-32b:free |
| Document Processing | python-docx |
| Containerization | Docker and Docker Compose |

## Project Structure

```text
rag-document-system/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── core/
│
├── documents/
│   ├── management/
│   ├── migrations/
│   ├── admin.py
│   ├── chunking.py
│   ├── embedding_service.py
│   ├── models.py
│   ├── search.py
│   ├── serializers.py
│   ├── services.py
│   ├── tests.py
│   ├── urls.py
│   ├── validators.py
│   └── views.py
│
├── qa/
│   ├── management/
│   ├── migrations/
│   ├── admin.py
│   ├── llm_service.py
│   ├── models.py
│   ├── prompts.py
│   ├── rag_service.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── media/
│   └── documents/
│
├── config/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── manage.py
├── .dockerignore
└── .gitignore
```

## Requirements

To run the project, you need:

- Docker
- Docker Compose
- An OpenRouter API key

The application uses Docker Compose to run the Django application and PostgreSQL database.

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/rag-document-system.git
cd rag-document-system
```

### 2. Configure Environment Variables

Create a `.env` file in the project root directory.

Configure the required environment variables:

```env
DJANGO_SECRET_KEY=replace-with-a-secure-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

DB_NAME=rag_db
DB_USER=rag_user
DB_PASSWORD=change-this-database-password
DB_HOST=db
DB_PORT=5432

OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_MODEL=qwen/qwen3-32b:free

RAG_TOP_K=5
RAG_MAX_COSINE_DISTANCE=0.20
RAG_LLM_MAX_TOKENS=1024
RAG_LLM_TIMEOUT=60000
```

Replace the placeholder values with your own configuration.

Keep your `.env` file private. It contains sensitive credentials and must not be committed to version control.

### 3. Run with Docker Compose

Build the application image and start the containers:

```bash
docker compose up --build -d
```

Check the running containers:

```bash
docker compose ps
```

View application logs:

```bash
docker compose logs -f web
```

The application will be available at:

- Application: http://localhost:8000/
- Django Admin: http://localhost:8000/admin/
- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/

### 4. Apply Database Migrations

Run the database migrations:

```bash
docker compose exec web python manage.py migrate
```

### 5. Create a Superuser

Create an administrator account to access Django Admin:

```bash
docker compose exec web python manage.py createsuperuser
```

Follow the prompts to set the administrator username, email, and password.

## API Documentation

The API documentation is generated using **drf-spectacular** and provides interactive documentation for available endpoints.

Once the application is running, access:

| Documentation | URL |
|---|---|
| Swagger UI | http://localhost:8000/api/docs/ |
| ReDoc | http://localhost:8000/api/redoc/ |
| OpenAPI Schema | http://localhost:8000/api/schema/ |

Swagger UI can be used to explore endpoints, inspect request and response schemas, and send API requests.

## API Endpoints

### Documents

Base URL: `/api/documents/`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/documents/` | List uploaded documents |
| POST | `/api/documents/` | Upload a new document |
| GET | `/api/documents/{id}/` | Retrieve a document |
| PUT | `/api/documents/{id}/` | Update a document |
| PATCH | `/api/documents/{id}/` | Partially update a document |
| DELETE | `/api/documents/{id}/` | Delete a document |

### Question Answering

Base URL: `/api/qa/`

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/qa/ask/` | Submit a question and receive an answer |
| GET | `/api/qa/history/` | Retrieve paginated question history |
| GET | `/api/qa/history/{id}/` | Retrieve a question history entry with its sources |

Question history is ordered from newest to oldest. The list endpoint provides pagination, while the detail endpoint includes the associated source references.

## Running Tests

The project includes automated tests for document management, question answering, and API functionality.

Run the test suite inside the web container:

```bash
docker compose exec web python manage.py test
```

The project completed **58 automated tests** during the testing and verification phase.

## Configuration

The following environment variables can be used to configure the application:

| Variable | Description | Default |
|---|---|---|
| `DJANGO_SECRET_KEY` | Django secret key | Development fallback |
| `DJANGO_DEBUG` | Enables or disables debug mode | `True` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hosts | `localhost,127.0.0.1,0.0.0.0` |
| `DB_NAME` | PostgreSQL database name | `rag_db` |
| `DB_USER` | PostgreSQL username | `rag_user` |
| `DB_PASSWORD` | PostgreSQL password | `rag_password` |
| `DB_HOST` | Database host | `db` |
| `DB_PORT` | Database port | `5432` |
| `OPENROUTER_API_KEY` | OpenRouter API key | Empty |
| `OPENROUTER_MODEL` | Language model identifier | `qwen/qwen3-32b:free` |
| `RAG_TOP_K` | Maximum number of retrieved chunks | `5` |
| `RAG_MAX_COSINE_DISTANCE` | Maximum cosine distance for retrieval | `0.20` |
| `RAG_LLM_MAX_TOKENS` | Maximum generated answer tokens | `1024` |
| `RAG_LLM_TIMEOUT` | LLM request timeout in milliseconds | `60000` |

## Current Limitations

- The current document upload workflow supports DOCX files.
- Answer quality depends on document content, retrieval relevance, and the configured language model.
- Generating answers requires a valid OpenRouter API key and access to the selected model.
- The provided Docker configuration is intended for development and testing, not production deployment.

## License

No license has been specified for this project yet.