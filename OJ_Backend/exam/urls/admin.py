from django.conf.urls import url

from ..views.admin import (
    ExamAnswerFileAPI, ExamDeskAPI, ExamDownloadAnswersAPI, ExamDownloadScoresAPI,
    ExamProblemAPI, ExamSessionAPI, ExamStudentSessionAPI, ExamSubmissionAPI, ExamTestCaseAPI,
    ResetStudentPasswordAPI,
)

urlpatterns = [
    url(r"^exam/desk/?$", ExamDeskAPI.as_view(), name="exam_desk_api"),
    url(r"^exam/session/?$", ExamSessionAPI.as_view(), name="exam_session_api"),
    url(r"^exam/problem/?$", ExamProblemAPI.as_view(), name="exam_problem_api"),
    url(r"^exam/testcase/?$", ExamTestCaseAPI.as_view(), name="exam_testcase_api"),
    url(r"^exam/submission/?$", ExamSubmissionAPI.as_view(), name="exam_submission_api"),
    url(r"^exam/student_session/?$", ExamStudentSessionAPI.as_view(), name="exam_student_session_api"),
    url(r"^exam/student/reset_password/?$", ResetStudentPasswordAPI.as_view(), name="reset_student_password_api"),
    url(r"^exam/answer_file/?$", ExamAnswerFileAPI.as_view(), name="exam_answer_file_api"),
    url(r"^exam/download/answers/?$", ExamDownloadAnswersAPI.as_view(), name="exam_download_answers_api"),
    url(r"^exam/download/scores/?$", ExamDownloadScoresAPI.as_view(), name="exam_download_scores_api"),
]
