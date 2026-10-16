from django.db import models
from django.utils.timezone import now

from account.models import User
from utils.shortcuts import rand_str


class ExamMode(object):
    JUDGE = "judge"
    ARCHIVE = "archive"


class ExamSession(models.Model):
    slot = models.PositiveSmallIntegerField(unique=True)
    title = models.TextField(default="")
    access_code = models.TextField(unique=True)
    mode = models.TextField(default=ExamMode.JUDGE)
    view_start = models.DateTimeField(null=True, blank=True)
    view_end = models.DateTimeField(null=True, blank=True)
    submit_start = models.DateTimeField(null=True, blank=True)
    submit_end = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "exam_session"
        ordering = ("slot",)

    def _window_open(self, start, end):
        if not start or not end:
            return False
        current = now()
        return start <= current <= end

    @property
    def can_view(self):
        return self._window_open(self.view_start, self.view_end)

    @property
    def can_submit(self):
        return self._window_open(self.submit_start, self.submit_end)


class ZipSubmission(models.Model):
    id = models.TextField(default=rand_str, primary_key=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    problem = models.ForeignKey("problem.Problem", on_delete=models.CASCADE)
    session = models.ForeignKey(ExamSession, on_delete=models.CASCADE)
    original_name = models.TextField()
    stored_path = models.TextField()
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "exam_zip_submission"
        ordering = ("-create_time",)


class ExamStudentSession(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="exam_student_session")
    session = models.ForeignKey(ExamSession, on_delete=models.CASCADE)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "exam_student_session"
        ordering = ("-create_time",)

