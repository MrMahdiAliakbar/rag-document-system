from django.core.management.base import BaseCommand, CommandError

from documents.search import search_similar_chunks


class Command(BaseCommand):
    help = "Search document chunks using semantic similarity."

    def add_arguments(self, parser):
        parser.add_argument(
            "query",
            nargs="+",
        )

        parser.add_argument(
            "--limit",
            type=int,
            default=5,
        )

    def handle(self, *args, **options):
        query = " ".join(options["query"])
        limit = options["limit"]

        try:
            results = search_similar_chunks(
                query,
                top_k=limit,
            )
        except ValueError as error:
            raise CommandError(str(error))

        if not results:
            self.stdout.write(
                self.style.WARNING(
                    "No matching chunks were found."
                )
            )
            return

        for rank, chunk in enumerate(results, start=1):
            similarity = 1 - float(chunk.distance)

            self.stdout.write(
                f"\nRank: {rank}"
                f" | Document: {chunk.document.title}"
                f" | Chunk: {chunk.chunk_index}"
                f" | Similarity: {similarity:.4f}"
            )

            self.stdout.write(chunk.content)

            self.stdout.write("-" * 60)
