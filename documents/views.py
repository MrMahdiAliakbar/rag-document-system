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
        responses={201: DocumentSerializer}
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