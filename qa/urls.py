from django.urls import path

from .views import (
    AskQuestionView,
    QuestionHistoryDetailView,
    QuestionHistoryListView,
)


urlpatterns = [
    path(
        "ask/",
        AskQuestionView.as_view(),
        name="ask-question",
    ),
    path(
        "history/",
        QuestionHistoryListView.as_view(),
        name="question-history-list",
    ),
    path(
        "history/<int:pk>/",
        QuestionHistoryDetailView.as_view(),
        name="question-history-detail",
    ),
]