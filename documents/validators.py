from django.core.exceptions import ValidationError


MAX_DOCUMENT_SIZE = 10 * 1024 * 1024


def validate_document_size(file):
    if file.size > MAX_DOCUMENT_SIZE:
        raise ValidationError(
            "File size must not exceed 10 MB."
        )