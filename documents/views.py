
import logging

from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema

from .models import Document
from .serializers import (
    DocumentSerializer,
    DocumentUpdateSerializer,
    DocumentUploadSerializer,
)
from .services import process_document


logger = logging.getLogger(__name__)


def get_document_queryset():
    return Document.objects.annotate(
        chunk_count=Count("chunks")
    )


def delete_stored_file(storage, file_name):
    try:
        storage.delete(file_name)
    except Exception:
        logger.exception(
            "Failed to delete stored document file: %s",
            file_name,
        )


class DocumentListCreateView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        tags=["Documents"],
        summary="List documents",
        responses={200: DocumentSerializer(many=True)},
    )
    def get(self, request):
        documents = get_document_queryset()

        serializer = DocumentSerializer(
            documents,
            many=True,
        )

        return Response(serializer.data)

    @extend_schema(
        tags=["Documents"],
        summary="Upload and process a DOCX document",
        request={
            "multipart/form-data": DocumentUploadSerializer
        },
        responses={201: DocumentSerializer},
    )
    def post(self, request):
        serializer = DocumentUploadSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        document = serializer.save()

        process_document(document)

        document = get_document_queryset().get(pk=document.pk)
        response_serializer = DocumentSerializer(document)

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class DocumentDetailView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self, pk):
        return get_object_or_404(
            get_document_queryset(),
            pk=pk,
        )

    @extend_schema(
        tags=["Documents"],
        summary="Retrieve document details",
        responses={200: DocumentSerializer},
    )
    def get(self, request, pk):
        document = self.get_object(pk)

        serializer = DocumentSerializer(document)

        return Response(serializer.data)

    @extend_schema(
        tags=["Documents"],
        summary="Replace or update a document",
        request={
            "multipart/form-data": DocumentUpdateSerializer
        },
        responses={
            200: DocumentSerializer,
            422: None,
        },
    )
    def put(self, request, pk):
        return self.update_document(
            request,
            pk,
            partial=False,
        )

    @extend_schema(
        tags=["Documents"],
        summary="Partially update a document",
        request={
            "multipart/form-data": DocumentUpdateSerializer
        },
        responses={
            200: DocumentSerializer,
            422: None,
        },
    )
    def patch(self, request, pk):
        return self.update_document(
            request,
            pk,
            partial=True,
        )

    def update_document(self, request, pk, partial):
        document = self.get_object(pk)

        old_file_name = document.file.name
        old_storage = document.file.storage

        old_values = {
            "title": document.title,
            "full_text": document.full_text,
            "status": document.status,
            "error_message": document.error_message,
        }

        serializer = DocumentUpdateSerializer(
            document,
            data=request.data,
            partial=partial,
        )

        serializer.is_valid(raise_exception=True)

        file_changed = "file" in serializer.validated_data

        document = serializer.save()

        if file_changed:
            new_file_name = document.file.name

            if not process_document(document):
                error_message = document.error_message

                if new_file_name != old_file_name:
                    delete_stored_file(
                        document.file.storage,
                        new_file_name,
                    )

                document.file.name = old_file_name
                document.title = old_values["title"]
                document.full_text = old_values["full_text"]
                document.status = old_values["status"]
                document.error_message = old_values["error_message"]

                document.save(
                    update_fields=[
                        "file",
                        "title",
                        "full_text",
                        "status",
                        "error_message",
                        "updated_at",
                    ]
                )

                return Response(
                    {
                        "detail": "Document processing failed.",
                        "error": error_message,
                    },
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            if old_file_name and old_file_name != new_file_name:
                transaction.on_commit(
                    lambda: delete_stored_file(
                        old_storage,
                        old_file_name,
                    )
                )

        document = get_document_queryset().get(pk=document.pk)

        response_serializer = DocumentSerializer(document)

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Documents"],
        summary="Delete a document and its stored file",
        responses={204: None},
    )
    def delete(self, request, pk):
        document = self.get_object(pk)

        storage = document.file.storage
        file_name = document.file.name

        with transaction.atomic():
            document.delete()

            if file_name:
                transaction.on_commit(
                    lambda: delete_stored_file(
                        storage,
                        file_name,
                    )
                )

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )