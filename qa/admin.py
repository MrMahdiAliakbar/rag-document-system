from django.contrib import admin
from .models import QuestionAnswer

@admin.register(QuestionAnswer)
class QuestionAnswerAdmin(admin.ModelAdmin):
    list_display = (
        "question_preview",
        "created_at",
        "source_count",
    )
    search_fields = ("question", "answer")
    list_filter = ("created_at",)
    readonly_fields = (
        "question",
        "answer",
        "sources",
        "created_at",
    )
    fields = (
        "question",
        "answer",
        "sources",
        "created_at",
    )

    @admin.display(description="سؤال")
    def question_preview(self, obj):
        return obj.question[:80]

    @admin.display(description="تعداد منابع")
    def source_count(self, obj):
        return len(obj.sources)
