
from django.db import transaction
from docx import Document as WordDocument
from docx.document import Document as DocxDocument
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph
import tiktoken

from .models import Document, DocumentChunk


CHUNK_SIZE = 600
CHUNK_OVERLAP = 80


def iter_block_items(parent):
    if isinstance(parent, DocxDocument):
        parent_element = parent.element.body
    elif isinstance(parent, _Cell):
        parent_element = parent._tc
    else:
        raise TypeError("Unsupported document container.")

    for child in parent_element.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def extract_document_text(file):
    word_document = WordDocument(file)
    content_blocks = []

    for block in iter_block_items(word_document):
        if isinstance(block, Paragraph):
            text = block.text.strip()

            if text:
                content_blocks.append(text)

        elif isinstance(block, Table):
            rows = []

            for row in block.rows:
                cells = [
                    cell.text.strip()
                    for cell in row.cells
                ]

                row_text = " | ".join(
                    cell for cell in cells if cell
                )

                if row_text:
                    rows.append(row_text)

            if rows:
                content_blocks.append(
                    "[TABLE]\n" + "\n".join(rows)
                )

    full_text = "\n\n".join(content_blocks).strip()

    if not full_text:
        raise ValueError(
            "No readable text was found in the document."
        )

    return full_text


def split_text_into_chunks(text):
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)

    if not tokens:
        return []

    chunks = []
    step = CHUNK_SIZE - CHUNK_OVERLAP

    for start in range(0, len(tokens), step):
        end = start + CHUNK_SIZE
        chunk_tokens = tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens).strip()

        if chunk_text:
            chunks.append(chunk_text)

        if end >= len(tokens):
            break

    return chunks


def process_document(document):
    document.status = Document.Status.PROCESSING
    document.error_message = ""

    document.save(
        update_fields=[
            "status",
            "error_message",
            "updated_at",
        ]
    )

    try:
        document.file.open("rb")

        try:
            full_text = extract_document_text(document.file)
        finally:
            document.file.close()

        chunks = split_text_into_chunks(full_text)

        if not chunks:
            raise ValueError(
                "Document could not be divided into chunks."
            )

        with transaction.atomic():
            current_document = (
                Document.objects
                .select_for_update()
                .get(pk=document.pk)
            )

            current_document.chunks.all().delete()

            DocumentChunk.objects.bulk_create([
                DocumentChunk(
                    document=current_document,
                    content=chunk,
                    chunk_index=index,
                    metadata={
                        "source_file": current_document.file.name,
                        "chunk_index": index,
                    },
                )
                for index, chunk in enumerate(chunks)
            ])

            current_document.full_text = full_text
            current_document.status = Document.Status.COMPLETED
            current_document.error_message = ""

            current_document.save(
                update_fields=[
                    "full_text",
                    "status",
                    "error_message",
                    "updated_at",
                ]
            )

        document.full_text = full_text
        document.status = Document.Status.COMPLETED
        document.error_message = ""

        return True

    except Exception as error:
        document.status = Document.Status.FAILED
        document.error_message = str(error)

        document.save(
            update_fields=[
                "status",
                "error_message",
                "updated_at",
            ]
        )

        return False
