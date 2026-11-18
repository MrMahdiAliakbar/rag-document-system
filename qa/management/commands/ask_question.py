from django.core.management.base import BaseCommand, CommandError

from qa.llm_service import (
    LLMConfigurationError,
    LLMGenerationError,
)
from qa.rag_service import (
    NO_ANSWER_MESSAGE,
    answer_question,
)


class Command(BaseCommand):
    help = "Ask a question using retrieval-augmented generation."

    def add_arguments(self, parser):
        parser.add_argument(
            "question",
            nargs="+",
        )

        parser.add_argument(
            "--limit",
            type=int,
            default=None,
        )

        parser.add_argument(
            "--document-id",
            type=int,
            default=None,
        )

    def handle(self, *args, **options):
        question = " ".join(options["question"])

        try:
            result = answer_question(
                question=question,
                top_k=options["limit"],
                document_id=options["document_id"],
            )
        except (
            ValueError,
            LLMConfigurationError,
            LLMGenerationError,
        ) as error:
            raise CommandError(str(error)) from error

        record = result["record"]
        sources = result["sources"]

        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("QUESTION")
        self.stdout.write(question)

        self.stdout.write("\nANSWER")
        self.stdout.write(record.answer)

        if record.answer == NO_ANSWER_MESSAGE:
            self.stdout.write(
                self.style.WARNING(
                    "\nNo answer could be generated from the available evidence."
                )
            )
        elif result["used_llm"]:
            self.stdout.write(
                self.style.SUCCESS(
                    "\nAnswer generated successfully."
                )
            )

        self.stdout.write("\nSOURCES")

        if not sources:
            self.stdout.write("No sources found.")
        else:
            for source in sources:
                self.stdout.write(
                    f"\n[{source['source_id']}]"
                    f" Document: {source['document_title']}"
                    f" | Chunk: {source['chunk_index']}"
                    f" | Similarity: {source['similarity']:.4f}"
                )

        self.stdout.write(
            f"\nHistory ID: {record.id}"
        )

        self.stdout.write("=" * 70)
