
from pathlib import Path

from rest_framework import serializers

from .models import Document
from .validators import MAX_DOCUMENT_SIZE


class DocumentUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField()

    class Meta:
        model = Document
        fields = ["title", "file"]

    def validate_title(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Document title cannot be empty."
            )

        return value

    def validate_file(self, value):
        extension = Path(value.name).suffix.lower()

        if extension != ".docx":
            raise serializers.ValidationError(
                "Only DOCX files are allowed."
            )

        if value.size > MAX_DOCUMENT_SIZE:
            raise serializers.ValidationError(
                "File size must not exceed 10 MB."
            )

        if value.size == 0:
            raise serializers.ValidationError(
                "Uploaded file cannot be empty."
            )

        return value


class DocumentUpdateSerializer(DocumentUploadSerializer):
    file = serializers.FileField(required=False)

    class Meta(DocumentUploadSerializer.Meta):
        extra_kwargs = {
            "file": {"required": False},
        }


class DocumentSerializer(serializers.ModelSerializer):
    chunk_count = serializers.IntegerField(read_only=True)
    file_name = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "file_name",
            "status",
            "chunk_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_file_name(self, obj) -> str | None:
        if not obj.file:
            return None

        return Path(obj.file.name).name