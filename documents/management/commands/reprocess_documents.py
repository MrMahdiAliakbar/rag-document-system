from django.core.management.base import BaseCommand

from documents.models import Document
from documents.services import process_document


class Command(BaseCommand):
    help = "Reprocess completed documents and generate embeddings."

    def add_arguments(self, parser):
        parser.add_argument(
            "--document-id",
            type=int,
        )

    def handle(self, *args, **options):
        documents = Document.objects.filter(
            status=Document.Status.COMPLETED
        ).order_by("id")

        document_id = options.get("document_id")

        if document_id is not None:
            documents = documents.filter(
                id=document_id
            )

        documents = list(documents)

        if not documents:
            self.stdout.write(
                self.style.WARNING(
                    "No completed documents were found."
                )
            )
            return

        successful = 0
        failed = 0

        for document in documents:
            self.stdout.write(
                f"Processing document {document.id}: {document.title}"
            )

            if process_document(document):
                successful += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Document {document.id} completed."
                    )
                )
            else:
                failed += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"Document {document.id} failed: "
                        f"{document.error_message}"
                    )
                )

        self.stdout.write(
            f"Successful: {successful} | Failed: {failed}"
        )
