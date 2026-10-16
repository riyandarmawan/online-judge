import os
import zipfile

from django.conf import settings
from django.db import IntegrityError

from account.decorators import login_required
from problem.models import Problem
from utils.api import APIView

from ..access import (
    remember_unlock, student_can_manage, unlocked_session_ids, _resolve_answer_filename,
    check_answer_filename,
)
from ..models import ExamMode, ExamSession, ExamStudentSession, ZipSubmission


class ExamStatusAPI(APIView):
    def get(self, request):
        sessions = []
        found = {item.id: item for item in ExamSession.objects.filter(id__in=unlocked_session_ids(request))}
        for session_id in unlocked_session_ids(request):
            session = found.get(session_id)
            if not session:
                continue
            sessions.append({
                "id": session.id,
                "slot": session.slot,
                "title": session.title,
                "mode": session.mode,
                "can_view": session.can_view,
                "can_submit": session.can_submit,
            })
        return self.success({
            "authenticated": request.user.is_authenticated,
            "is_dosen": student_can_manage(request),
            "unlocked": sessions,
        })


class ExamUnlockAPI(APIView):
    def post(self, request):
        code = str(request.data.get("access_code") or "").strip()
        if not code:
            return self.error("Kode akses wajib diisi.")
        try:
            session = ExamSession.objects.get(access_code=code)
        except ExamSession.DoesNotExist:
            return self.error("Kode akses salah.")

        user = getattr(request, "user", None)
        is_auth = bool(user and user.is_authenticated)

        if not is_auth:
            if session.mode == ExamMode.JUDGE:
                return self.error("Untuk sesi Algoritma dan Pemrograman (C), Anda wajib Masuk (Login) terlebih dahulu.")
        else:
            if not user.is_admin_role():
                existing = ExamStudentSession.objects.filter(user=user).select_related("session").first()
                if existing:
                    if existing.session_id != session.id:
                        existing.session = session
                        existing.save()
                else:
                    ExamStudentSession.objects.create(user=user, session=session)

        remember_unlock(request, session.id)

        if not session.can_view:
            msg = "Kode akses diterima, namun akses melihat soal saat ini sedang ditutup."
        else:
            msg = "Berhasil masuk ke sesi '%s'." % session.title

        return self.success({
            "session_id": session.id,
            "title": session.title,
            "mode": session.mode,
            "can_view": session.can_view,
            "can_submit": session.can_submit,
            "message": msg,
        })


class ZipAnswerAPI(APIView):
    request_parsers = ()

    def get(self, request):
        problem_id = request.GET.get("problem_id")
        if not problem_id:
            return self.error("problem_id wajib diisi.")
        if request.user.is_authenticated:
            answers = ZipSubmission.objects.filter(problem_id=problem_id, user=request.user)
            return self.success([{
                "id": item.id,
                "original_name": item.original_name,
                "create_time": item.create_time.isoformat(),
            } for item in answers])
        else:
            nim = request.GET.get("nim")
            if nim:
                answers = ZipSubmission.objects.filter(problem_id=problem_id, user__username=nim)
                return self.success([{
                    "id": item.id,
                    "original_name": item.original_name,
                    "create_time": item.create_time.isoformat(),
                } for item in answers])
            cached = request.session.get("my_zip_" + str(problem_id))
            if cached:
                return self.success([cached])
            return self.success([])

    def post(self, request):
        problem_id = request.POST.get("problem_id")
        uploaded = request.FILES.get("file")
        if not problem_id or not uploaded:
            return self.error("Soal dan berkas zip wajib diisi.")
        try:
            problem = Problem.objects.select_related("exam_session").get(id=problem_id, visible=True)
        except (Problem.DoesNotExist, ValueError):
            return self.error("Soal tidak ditemukan.")
        session = problem.exam_session
        if not session or session.mode != ExamMode.ARCHIVE:
            return self.error("Soal ini tidak menerima berkas zip.")
        if not student_can_manage(request):
            if session.id not in unlocked_session_ids(request):
                return self.error("Masukkan kode akses sebelum mengumpulkan jawaban.")
            if not session.can_view:
                return self.error("Akses melihat soal sedang ditutup.")
            if not session.can_submit:
                return self.error("Akses pengumpulan jawaban sedang ditutup.")

        nim = ""
        student_name = ""
        if request.user.is_authenticated:
            nim = request.user.username
            profile = getattr(request.user, "userprofile", None)
            student_name = profile.real_name if profile else ""

        client_nim = str(request.POST.get("nim") or "").strip()
        client_name = str(request.POST.get("name") or request.POST.get("student_name") or "").strip()
        if client_nim:
            nim = client_nim
        if client_name:
            student_name = client_name

        original = os.path.basename(uploaded.name).strip()

        if not nim or not student_name:
            import re
            base = os.path.splitext(original)[0]
            parts = base.split("_")
            if len(parts) >= 2 and re.match(r"^\d+$", parts[0]):
                if not nim:
                    nim = parts[0]
                if not student_name:
                    student_name = parts[1].replace("-", " ")

        if not nim:
            return self.error("NIM mahasiswa wajib diisi.")
        if not student_name:
            return self.error("Nama lengkap mahasiswa wajib diisi.")

        expected_raw = (problem.answer_filename or "").strip()
        valid, msg = check_answer_filename(original, expected_raw, nim, student_name)
        if not valid:
            return self.error(msg)

        if uploaded.size > 50 * 1024 * 1024:
            return self.error("Ukuran berkas maksimal 50 MB.")
        if not zipfile.is_zipfile(uploaded):
            return self.error("Berkas zip rusak atau bukan arsip zip.")
        uploaded.seek(0)

        directory = os.path.join(settings.DATA_DIR, "exam_answer")
        os.makedirs(directory, exist_ok=True)
        from utils.shortcuts import rand_str
        stored_name = rand_str() + ".zip"
        stored_path = os.path.join(directory, stored_name)
        with open(stored_path, "wb") as output:
            for chunk in uploaded.chunks():
                output.write(chunk)

        from account.models import User, AdminType, UserProfile
        user, _ = User.objects.get_or_create(
            username=nim,
            defaults={
                "email": None,
                "admin_type": AdminType.REGULAR_USER,
            }
        )
        profile, _ = UserProfile.objects.get_or_create(user=user)
        if student_name and profile.real_name != student_name:
            profile.real_name = student_name
            profile.save(update_fields=["real_name"])

        try:
            answer = ZipSubmission.objects.create(
                user=user,
                problem=problem,
                session=session,
                original_name=original,
                stored_path=stored_path,
            )
        except IntegrityError:
            return self.error("Jawaban gagal disimpan.")

        ret_data = {
            "id": answer.id,
            "original_name": answer.original_name,
            "create_time": answer.create_time.isoformat(),
            "student_info": f"{nim} - {student_name}",
        }
        request.session["my_zip_" + str(problem.id)] = ret_data

        return self.success(ret_data)
