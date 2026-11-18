from rest_framework import serializers

from documents.models import Document

from .models import QuestionAnswer
from .rag_service import NO_ANSWER_MESSAGE


class AskQuestionSerializer(serializers.Serializer):
    question = serializers.CharField(
        max_length=5000,
        trim_whitespace=True,
    )

    document_id = serializers.IntegerField(
        required=False,
        min_value=1,
    )

    def validate_document_id(self, value):
        if not Document.objects.filter(pk=value).exists():
            raise serializers.ValidationError(
                "Document does not exist."
            )

        return value


class AskQuestionResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    question = serializers.CharField()
    answer = serializers.CharField()
    status = serializers.ChoiceField(
        choices=["answered", "no_answer"]
    )
    sources = serializers.JSONField()
    used_llm = serializers.BooleanField()
    created_at = serializers.DateTimeField()


class QuestionHistoryListSerializer(
    serializers.ModelSerializer
):
    status = serializers.SerializerMethodField()

    class Meta:
        model = QuestionAnswer
        fields = [
            "id",
            "question",
            "answer",
            "status",
            "created_at",
        ]
        read_only_fields = fields

    def get_status(self, obj) -> str:
        if obj.answer == NO_ANSWER_MESSAGE:
            return "no_answer"

        return "answered"


class QuestionHistoryDetailSerializer(
    serializers.ModelSerializer
):
    status = serializers.SerializerMethodField()

    class Meta:
        model = QuestionAnswer
        fields = [
            "id",
            "question",
            "answer",
            "status",
            "sources",
            "created_at",
        ]
        read_only_fields = fields

    def get_status(self, obj) -> str:
        if obj.answer == NO_ANSWER_MESSAGE:
            return "no_answer"

        return "answered"