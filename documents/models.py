from django.db import models
from pgvector.django import VectorField

class Document(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار پردازش"
        PROCESSING = "processing", "در حال پردازش"
        COMPLETED = "completed", "پردازش شده"
        FAILED = "failed", "ناموفق"

    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="documents/%Y/%m/%d/")
    full_text = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class DocumentChunk(models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="chunks"
    )
    content = models.TextField()
    chunk_index = models.PositiveIntegerField()
    embedding = VectorField(
        dimensions=384,
        null=True,
        blank=True
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["document_id", "chunk_index"]
        constraints = [
            models.UniqueConstraint(
                fields=["document", "chunk_index"],
                name="unique_document_chunk_index"
            )
        ]

    def __str__(self):
        return f"{self.document.title} - Chunk {self.chunk_index}"
