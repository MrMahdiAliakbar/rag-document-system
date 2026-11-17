
from django.contrib import admin, messages
from django.db import transaction

from .models import Document, DocumentChunk
from .services import process_document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "status",
        "created_at",
        "updated_at",
    )

    list_filter = ("status", "created_at")

    search_fields = ("title", "full_text")

    readonly_fields = (
        "status",
        "full_text",
        "error_message",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Document Information", {
            "fields": ("title", "file", "status")
        }),
        ("Extracted Text", {
            "fields": ("full_text", "error_message")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )

    def save_model(self, request, obj, form, change):
        should_process = (
            not change or "file" in form.changed_data
        )

        old_file_name = None

        if change:
            old_file_name = (
                Document.objects
                .filter(pk=obj.pk)
                .values_list("file", flat=True)
                .first()
            )

        super().save_model(request, obj, form, change)

        if not should_process:
            return

        new_file_name = obj.file.name
        success = process_document(obj)

        if success:
            if old_file_name and old_file_name != new_file_name:
                old_storage = obj.file.storage

                transaction.on_commit(
                    lambda: old_storage.delete(old_file_name)
                )

            self.message_user(
                request,
                "Document processed successfully.",
                level=messages.SUCCESS,
            )
        else:
            if old_file_name and old_file_name != new_file_name:
                new_storage = obj.file.storage
                new_storage.delete(new_file_name)
                obj.file.name = old_file_name
                obj.save(update_fields=["file"])

            self.message_user(
                request,
                f"Document processing failed: {obj.error_message}",
                level=messages.ERROR,
            )

    def delete_model(self, request, obj):
        file_name = obj.file.name
        file_storage = obj.file.storage

        super().delete_model(request, obj)

        if file_name:
            transaction.on_commit(
                lambda: file_storage.delete(file_name)
            )

    def delete_queryset(self, request, queryset):
        files_to_delete = [
            (obj.file.storage, obj.file.name)
            for obj in queryset
            if obj.file
        ]

        super().delete_queryset(request, queryset)

        for file_storage, file_name in files_to_delete:
            transaction.on_commit(
                lambda storage=file_storage, name=file_name: (
                    storage.delete(name)
                )
            )


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "document",
        "chunk_index",
        "created_at",
    )

    list_filter = ("created_at",)

    search_fields = ("document__title", "content")

    readonly_fields = ("embedding", "created_at")

    fields = (
        "document",
        "chunk_index",
        "content",
        "embedding",
        "metadata",
        "created_at",
    )
