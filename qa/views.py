from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema

from .llm_service import (
    LLMConfigurationError,
    LLMGenerationError,
)
from .models import QuestionAnswer
from .rag_service import (
    NO_ANSWER_MESSAGE,
    answer_question,
)
from .serializers import (
    AskQuestionResponseSerializer,
    AskQuestionSerializer,
    QuestionHistoryDetailSerializer,
    QuestionHistoryListSerializer,
)


class AskQuestionView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]

    @extend_schema(
        tags=["Question Answering"],
        summary="Ask a question about documents",
        request=AskQuestionSerializer,
        responses={
            200: AskQuestionResponseSerializer,
        },
    )
    def post(self, request):
        serializer = AskQuestionSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        question = serializer.validated_data["question"]

        document_id = serializer.validated_data.get(
            "document_id"
        )

        try:
            result = answer_question(
                question=question,
                document_id=document_id,
            )

        except ValueError as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except (
            LLMConfigurationError,
            LLMGenerationError,
        ):
            return Response(
                {
                    "detail": (
                        "The question-answering service "
                        "is currently unavailable. "
                        "Please try again later."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        record = result["record"]

        response_data = {
            "id": record.id,
            "question": record.question,
            "answer": record.answer,
            "status": (
                "no_answer"
                if record.answer == NO_ANSWER_MESSAGE
                else "answered"
            ),
            "sources": result["sources"],
            "used_llm": result["used_llm"],
            "created_at": record.created_at,
        }

        return Response(
            response_data,
            status=status.HTTP_200_OK,
        )


class QuestionHistoryPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class QuestionHistoryListView(generics.ListAPIView):
    queryset = QuestionAnswer.objects.all()
    serializer_class = QuestionHistoryListSerializer
    permission_classes = [AllowAny]
    pagination_class = QuestionHistoryPagination

    @extend_schema(
        tags=["Question History"],
        summary="List question history",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class QuestionHistoryDetailView(generics.RetrieveAPIView):
    queryset = QuestionAnswer.objects.all()
    serializer_class = QuestionHistoryDetailSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Question History"],
        summary="Retrieve question history details",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)