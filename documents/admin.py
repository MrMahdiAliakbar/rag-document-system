from django.contrib import admin
from .models import Document, DocumentChunk


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
        "full_text",
        "error_message",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        ("اطلاعات سند", {
            "fields": ("title", "file", "status")
        }),
        ("متن استخراج‌شده", {
            "fields": ("full_text", "error_message")
        }),
        ("زمان‌بندی", {
            "fields": ("created_at", "updated_at")
        }),
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
