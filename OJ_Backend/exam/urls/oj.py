from django.conf.urls import url

from ..views.oj import ExamStatusAPI, ExamUnlockAPI, ZipAnswerAPI

urlpatterns = [
    url(r"^exam/status/?$", ExamStatusAPI.as_view(), name="exam_status_api"),
    url(r"^exam/unlock/?$", ExamUnlockAPI.as_view(), name="exam_unlock_api"),
    url(r"^exam/answer/?$", ZipAnswerAPI.as_view(), name="exam_zip_answer_api"),
]
