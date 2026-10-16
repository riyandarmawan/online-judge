import csv
import json
import os
import re
from io import BytesIO, StringIO
import zipfile

from django.conf import settings
from django.db import IntegrityError, transaction
from django.http import FileResponse, HttpResponse

from account.decorators import admin_role_required
from problem.models import Problem, ProblemRuleType
from problem.views.admin import TestCaseZipProcessor
from submission.models import Submission
from utils.api import APIError, APIView
from utils.shortcuts import rand_str

from ..access import html_to_plain, parse_dt, plain_to_html
from ..models import ExamMode, ExamSession, ExamStudentSession, ZipSubmission


def _iso(value):
    return value.isoformat() if value else None


def _session_payload(session):
    return {
        "id": session.id,
        "slot": session.slot,
        "title": session.title,
        "access_code": session.access_code,
        "mode": session.mode,
        "view_start": _iso(session.view_start),
        "view_end": _iso(session.view_end),
        "submit_start": _iso(session.submit_start),
        "submit_end": _iso(session.submit_end),
        "can_view": session.can_view,
        "can_submit": session.can_submit,
    }


def _problem_payload(problem):
    case_count = len(problem.test_case_score or []) if problem.exam_session and problem.exam_session.mode == ExamMode.JUDGE else 0
    tpl = problem.template if isinstance(problem.template, dict) else {}
    return {
        "id": problem.id,
        "_id": problem._id,
        "title": problem.title,
        "description": problem.description or "",
        "description_text": html_to_plain(problem.description),
        "input_description": problem.input_description or "",
        "output_description": problem.output_description or "",
        "samples": problem.samples or [],
        "hint": problem.hint or "",
        "session_id": problem.exam_session_id,
        "mode": problem.exam_session.mode if problem.exam_session_id else None,
        "answer_filename": problem.answer_filename or "",
        "time_limit": problem.time_limit,
        "memory_limit": problem.memory_limit,
        "test_case_id": problem.test_case_id,
        "test_case_count": case_count,
        "test_case_score": problem.test_case_score or [],
        "pdf_url": tpl.get("pdf_url", ""),
        "pdf_name": tpl.get("pdf_name", ""),
    }


def _clean_filename(name):
    cleaned = (name or "").strip()
    if not cleaned or "/" in cleaned or "\\" in cleaned or cleaned != os.path.basename(cleaned):
        raise APIError("Nama berkas tidak valid.")
    if not cleaned.lower().endswith(".zip"):
        raise APIError("Nama berkas jawaban harus berakhiran .zip.")
    return cleaned


class ExamDeskAPI(APIView):
    @admin_role_required
    def get(self, request):
        existing_slots = set(ExamSession.objects.values_list("slot", flat=True))
        for slot in range(1, 11):
            if slot not in existing_slots:
                mode = ExamMode.JUDGE if slot <= 5 else ExamMode.ARCHIVE
                title = "Algoritma dan Pemrograman %d" % slot if mode == ExamMode.JUDGE else "Pemrograman Lanjut %d" % (slot - 5)
                ExamSession.objects.create(
                    slot=slot,
                    title=title,
                    access_code=rand_str(8),
                    mode=mode,
                )
        sessions = [_session_payload(item) for item in ExamSession.objects.all()]
        problems = Problem.objects.select_related("exam_session").filter(exam_session__isnull=False, visible=True)
        return self.success({
            "sessions": sessions,
            "problems": [_problem_payload(item) for item in problems],
        })


class ExamSessionAPI(APIView):
    @admin_role_required
    def post(self, request):
        mode = request.data.get("mode") or ExamMode.JUDGE
        if mode not in (ExamMode.JUDGE, ExamMode.ARCHIVE):
            return self.error("Mode sesi tidak valid.")
        if ExamSession.objects.filter(mode=mode).count() >= 5:
            mode_label = "Algoritma dan Pemrograman" if mode == ExamMode.JUDGE else "Pemrograman Lanjut"
            return self.error("Maksimal 5 sesi %s sudah tercapai." % mode_label)

        used_slots = set(ExamSession.objects.values_list("slot", flat=True))
        slot = next((value for value in range(1, 11) if value not in used_slots), None)
        if slot is None:
            return self.error("Maksimal 10 sesi ujian sudah tercapai.")

        title = str(request.data.get("title") or "").strip()
        code = str(request.data.get("access_code") or "").strip()
        if not title:
            return self.error("Nama sesi wajib diisi.")
        if not code:
            return self.error("Kode akses wajib diisi.")
        try:
            session = ExamSession.objects.create(
                slot=slot,
                title=title,
                access_code=code,
                mode=mode,
            )
        except IntegrityError:
            return self.error("Kode akses sudah dipakai sesi lain.")
        return self.success(_session_payload(session))

    @admin_role_required
    def put(self, request):
        try:
            session = ExamSession.objects.get(id=request.data.get("id"))
        except (ExamSession.DoesNotExist, ValueError, TypeError):
            return self.error("Sesi tidak ditemukan.")
        title = str(request.data.get("title") or "").strip()
        code = str(request.data.get("access_code") or "").strip()
        mode = request.data.get("mode")
        if not title:
            return self.error("Nama sesi wajib diisi.")
        if not code:
            return self.error("Kode akses wajib diisi.")
        if mode not in (ExamMode.JUDGE, ExamMode.ARCHIVE):
            return self.error("Mode sesi tidak valid.")
        try:
            view_start = parse_dt(request.data.get("view_start"))
            view_end = parse_dt(request.data.get("view_end"))
            submit_start = parse_dt(request.data.get("submit_start"))
            submit_end = parse_dt(request.data.get("submit_end"))
        except APIError as exc:
            return self.error(exc.msg)
        if view_start and view_end and view_end <= view_start:
            return self.error("Waktu tutup lihat soal harus setelah waktu buka.")
        if submit_start and submit_end and submit_end <= submit_start:
            return self.error("Waktu tutup pengumpulan harus setelah waktu buka.")
        if (view_start is None) ^ (view_end is None):
            return self.error("Waktu buka dan tutup untuk melihat soal harus diisi bersamaan.")
        if (submit_start is None) ^ (submit_end is None):
            return self.error("Waktu buka dan tutup untuk mengumpulkan jawaban harus diisi bersamaan.")
        session.title = title
        session.access_code = code
        session.mode = mode
        session.view_start = view_start
        session.view_end = view_end
        session.submit_start = submit_start
        session.submit_end = submit_end
        try:
            session.save()
        except IntegrityError:
            return self.error("Kode akses sudah dipakai sesi lain.")
        return self.success(_session_payload(session))


class ExamProblemAPI(APIView):
    @admin_role_required
    def post(self, request):
        return self._save(request, creating=True)

    @admin_role_required
    def put(self, request):
        return self._save(request, creating=False)

    def _save(self, request, creating):
        data = request.data
        try:
            session = ExamSession.objects.get(id=data.get("session_id"))
        except (ExamSession.DoesNotExist, ValueError, TypeError):
            return self.error("Sesi tidak ditemukan.")
        title = str(data.get("title") or "").strip()
        description = str(data.get("description") or "").strip()
        pdf_url = str(data.get("pdf_url") or "").strip()
        pdf_name = str(data.get("pdf_name") or "").strip()

        if session.mode == ExamMode.ARCHIVE:
            if not pdf_url and description:
                m_url = re.search(r'href=["\']([^"\']+\.pdf)["\']', description, re.IGNORECASE) or \
                        re.search(r'(/public/upload/[a-zA-Z0-9_\-]+\.pdf)', description, re.IGNORECASE)
                if m_url:
                    pdf_url = m_url.group(1)
                m_name = re.search(r'>([^<]+\.pdf)</a>', description, re.IGNORECASE)
                if m_name:
                    pdf_name = m_name.group(1)
                elif "uts_perpustakaan" in description.lower():
                    pdf_url = "/public/upload/85441fca5e.pdf"
                    pdf_name = "uts_perpustakaan-digital-kampus.pdf"

            if not pdf_name and pdf_url:
                pdf_name = os.path.basename(pdf_url)

            if not title and pdf_name:
                title = os.path.splitext(pdf_name)[0].replace("_", " ").replace("-", " ")

        if not title:
            return self.error("Judul soal wajib diisi.")
        if session.mode == ExamMode.JUDGE and not description:
            return self.error("Deskripsi soal wajib diisi.")

        display_id = str(data.get("_id") or "").strip()
        input_description = str(data.get("input_description") or "").strip()
        output_description = str(data.get("output_description") or "").strip()
        hint = str(data.get("hint") or "").strip()
        if session.mode == ExamMode.ARCHIVE and hint:
            hint = re.sub(r'<[^>]*>', '', hint).strip()

        raw_samples = data.get("samples") or []
        samples = []
        if isinstance(raw_samples, list):
            for s in raw_samples:
                if isinstance(s, dict):
                    samples.append({
                        "input": str(s.get("input") or ""),
                        "output": str(s.get("output") or "")
                    })

        answer_filename = None
        test_case_id = str(data.get("test_case_id") or "").strip()
        test_case_score = []
        if session.mode == ExamMode.ARCHIVE:
            if not pdf_url and not description:
                return self.error("Berkas soal PDF wajib diunggah.")
            try:
                raw_answer_name = re.sub(r'<[^>]*>', '', str(data.get("answer_filename") or "")).strip()
                answer_filename = _clean_filename(raw_answer_name)
            except APIError as exc:
                return self.error(exc.msg)
            test_case_id = test_case_id or "none"
            if not description and pdf_url:
                description = f'<p>Dokumen soal tersedia dalam berkas PDF: <a href="{pdf_url}" target="_blank">{pdf_name or "Lihat PDF Soal"}</a></p>'
            if not input_description:
                input_description = "<p>-</p>"
            if not output_description:
                output_description = "<p>-</p>"
        else:
            if not test_case_id or test_case_id == "none":
                return self.error("Soal judge membutuhkan test case. Unggah berkas zip test case.")
            info_path = os.path.join(settings.TEST_CASE_DIR, test_case_id, "info")
            if not os.path.exists(info_path):
                return self.error("Test case tidak ditemukan. Unggah ulang berkas zip test case.")
            with open(info_path, "r", encoding="utf-8") as info_file:
                info = json.load(info_file)
            cases = list(info.get("test_cases", {}).values())
            if not cases:
                return self.error("Zip test case kosong.")

            client_scores = data.get("test_case_score")
            if isinstance(client_scores, list) and len(client_scores) == len(cases):
                for item in client_scores:
                    try:
                        sc = int(item.get("score") or 0)
                    except (ValueError, TypeError):
                        sc = 0
                    test_case_score.append({
                        "input_name": str(item.get("input_name") or ""),
                        "output_name": str(item.get("output_name") or ""),
                        "score": max(0, sc),
                    })
            else:
                share = int(100 / len(cases)) if cases else 0
                for item in cases:
                    test_case_score.append({
                        "input_name": item["input_name"],
                        "output_name": item["output_name"],
                        "score": share,
                    })
            if not input_description:
                input_description = "<p>Standard input</p>"
            if not output_description:
                output_description = "<p>Standard output</p>"

        try:
            time_limit = int(data.get("time_limit") or 1000)
            memory_limit = int(data.get("memory_limit") or 256)
        except (TypeError, ValueError):
            return self.error("Batas waktu atau memori tidak valid.")
        if time_limit < 1 or time_limit > 60000 or memory_limit < 1 or memory_limit > 1024:
            return self.error("Batas waktu atau memori di luar rentang yang diizinkan.")

        if creating:
            if not display_id:
                display_id = "S%d%s" % (session.slot, rand_str(6))
            elif Problem.objects.filter(_id=display_id, contest_id__isnull=True).exists():
                return self.error("Display ID '%s' sudah digunakan oleh soal lain." % display_id)
            problem = Problem(
                _id=display_id,
                created_by=request.user,
                visible=True,
                difficulty="Low",
                source="Ujian",
                statistic_info={},
            )
        else:
            try:
                problem = Problem.objects.get(id=data.get("id"), exam_session__isnull=False, visible=True)
            except (Problem.DoesNotExist, ValueError, TypeError):
                return self.error("Soal tidak ditemukan.")
            if display_id:
                if Problem.objects.exclude(id=problem.id).filter(_id=display_id, contest_id__isnull=True).exists():
                    return self.error("Display ID '%s' sudah digunakan oleh soal lain." % display_id)
                problem._id = display_id

        problem.title = title
        problem.description = description
        problem.input_description = input_description
        problem.output_description = output_description
        problem.samples = samples
        problem.test_case_id = test_case_id
        problem.test_case_score = test_case_score
        problem.hint = hint
        problem.languages = ["C"] if session.mode == ExamMode.JUDGE else []
        problem.template = {"pdf_url": pdf_url, "pdf_name": pdf_name} if session.mode == ExamMode.ARCHIVE else {}
        problem.time_limit = time_limit
        problem.memory_limit = memory_limit
        problem.rule_type = ProblemRuleType.OI
        total_score = sum(item.get("score", 0) for item in test_case_score)
        problem.total_score = total_score if total_score > 0 else (100 if session.mode == ExamMode.JUDGE else 0)
        problem.exam_session = session
        problem.answer_filename = answer_filename
        problem.share_submission = False
        try:
            with transaction.atomic():
                problem.save()
        except IntegrityError:
            return self.error("Soal gagal disimpan.")
        problem.exam_session = session
        return self.success(_problem_payload(problem))

    @admin_role_required
    def delete(self, request):
        try:
            problem = Problem.objects.get(id=request.GET.get("id"), exam_session__isnull=False)
        except (Problem.DoesNotExist, ValueError, TypeError):
            return self.error("Soal tidak ditemukan.")
        problem.visible = False
        problem.save(update_fields=["visible"])
        return self.success()


class ExamTestCaseAPI(APIView, TestCaseZipProcessor):
    request_parsers = ()

    @admin_role_required
    def post(self, request):
        uploaded = request.FILES.get("file")
        if not uploaded:
            return self.error("Berkas test case wajib diunggah.")
        if not zipfile.is_zipfile(uploaded):
            return self.error("Test case harus berupa zip yang berisi 1.in, 1.out, 2.in, 2.out, dan seterusnya.")
        uploaded.seek(0)
        info, test_case_id = self.process_zip(uploaded, spj=False)
        return self.success({
            "id": test_case_id,
            "test_case_id": test_case_id,
            "test_case_count": len(info),
            "info": info,
        })


class ExamSubmissionAPI(APIView):
    @admin_role_required
    def get(self, request):
        session = _get_session(request)
        if isinstance(session, HttpResponse):
            return session
        return self.success(_submission_bundle(session))


class ExamAnswerFileAPI(APIView):
    @admin_role_required
    def get(self, request):
        try:
            answer = ZipSubmission.objects.get(id=request.GET.get("id"))
        except ZipSubmission.DoesNotExist:
            return self.error("Jawaban tidak ditemukan.")
        if not os.path.exists(answer.stored_path):
            return self.error("Berkas jawaban tidak ada di server.")
        response = FileResponse(open(answer.stored_path, "rb"), content_type="application/zip")
        response["Content-Disposition"] = 'attachment; filename="%s"' % answer.original_name
        return response


class ExamDownloadAnswersAPI(APIView):
    @admin_role_required
    def get(self, request):
        session = _get_session(request)
        if isinstance(session, HttpResponse):
            return session
        bundle = BytesIO()
        with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as archive:
            submissions = Submission.objects.filter(problem__exam_session=session).select_related("problem")
            for item in submissions:
                ext = "c" if item.language == "C" else "txt"
                name = "kode/%s_%s_%s.%s" % (item.username, item.problem._id, item.id, ext)
                archive.writestr(name, item.code or "")
            for item in ZipSubmission.objects.filter(session=session).select_related("user"):
                if os.path.exists(item.stored_path):
                    arcname = "zip/%s_%s_%s" % (item.user.username, item.id, item.original_name)
                    archive.write(item.stored_path, arcname)
        bundle.seek(0)
        response = FileResponse(bundle, content_type="application/zip")
        response["Content-Disposition"] = 'attachment; filename="jawaban-sesi-%s.zip"' % session.slot
        return response


class ExamDownloadScoresAPI(APIView):
    @admin_role_required
    def get(self, request):
        session = _get_session(request)
        if isinstance(session, HttpResponse):
            return session
        text = StringIO()
        writer = csv.writer(text)
        if session.mode == ExamMode.JUDGE:
            writer.writerow(["username", "id_soal", "judul", "lulus", "total_test_case", "skor", "waktu_submit", "id_submission"])
            for row in _best_scores(session):
                writer.writerow([
                    row["username"], row["problem_display_id"], row["problem_title"],
                    row["passed"], row["total"], row["score"], row["create_time"], row["submission_id"],
                ])
        else:
            writer.writerow(["username", "id_soal", "judul", "nama_berkas", "waktu_submit"])
            for item in ZipSubmission.objects.filter(session=session).select_related("problem", "user").order_by("user__username", "problem_id", "-create_time"):
                writer.writerow([
                    item.user.username, item.problem._id, item.problem.title,
                    item.original_name, item.create_time.isoformat(),
                ])
        response = HttpResponse("\ufeff" + text.getvalue(), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="skor-sesi-%s.csv"' % session.slot
        return response


def _get_session(request):
    try:
        return ExamSession.objects.get(id=request.GET.get("session_id"))
    except (ExamSession.DoesNotExist, ValueError, TypeError):
        return APIView().error("Sesi tidak ditemukan.")


def _best_scores(session):
    best = {}
    submissions = Submission.objects.filter(problem__exam_session=session).select_related("problem").order_by("create_time")
    for item in submissions:
        info = item.statistic_info or {}
        score = info.get("score") or 0
        row = {
            "username": item.username,
            "problem_id": item.problem_id,
            "problem_display_id": item.problem._id,
            "problem_title": item.problem.title,
            "passed": info.get("passed", 0),
            "total": info.get("total", 0),
            "score": score,
            "create_time": item.create_time.isoformat(),
            "submission_id": item.id,
            "language": item.language,
            "result": item.result,
        }
        key = (item.user_id, item.problem_id)
        current = best.get(key)
        if current is None or score >= current["score"]:
            best[key] = row
    return sorted(best.values(), key=lambda row: (row["username"], row["problem_display_id"]))


def _submission_bundle(session):
    code_rows = []
    for item in Submission.objects.filter(problem__exam_session=session).select_related("problem").order_by("-create_time")[:300]:
        info = item.statistic_info or {}
        code_rows.append({
            "id": item.id,
            "username": item.username,
            "problem_id": item.problem_id,
            "problem_display_id": item.problem._id,
            "problem_title": item.problem.title,
            "language": item.language,
            "result": item.result,
            "passed": info.get("passed", 0),
            "total": info.get("total", 0),
            "score": info.get("score", 0),
            "create_time": item.create_time.isoformat(),
            "code": item.code,
        })
    zip_rows = []
    for item in ZipSubmission.objects.filter(session=session).select_related("problem", "user", "user__userprofile"):
        profile = getattr(item.user, "userprofile", None)
        zip_rows.append({
            "id": item.id,
            "user_id": item.user_id,
            "username": item.user.username,
            "real_name": profile.real_name if profile else "",
            "problem_id": item.problem_id,
            "problem_display_id": item.problem._id,
            "problem_title": item.problem.title,
            "original_name": item.original_name,
            "create_time": item.create_time.isoformat(),
        })
    students = []
    for item in ExamStudentSession.objects.filter(session=session).select_related("user", "user__userprofile").order_by("user__username"):
        profile = getattr(item.user, "userprofile", None)
        students.append({
            "id": item.id,
            "user_id": item.user_id,
            "username": item.user.username,
            "real_name": profile.real_name if profile else "",
            "create_time": item.create_time.isoformat(),
        })
    return {
        "code_submissions": code_rows,
        "zip_submissions": zip_rows,
        "scores": _best_scores(session) if session.mode == ExamMode.JUDGE else [],
        "students": students,
    }


class ExamStudentSessionAPI(APIView):
    @admin_role_required
    def delete(self, request):
        user_id = request.GET.get("user_id")
        if not user_id:
            return self.error("user_id wajib diisi.")
        ExamStudentSession.objects.filter(user_id=user_id).delete()
        return self.success()


class ResetStudentPasswordAPI(APIView):
    @admin_role_required
    def post(self, request):
        user_id = request.data.get("user_id")
        if not user_id:
            return self.error("user_id wajib diisi.")
        try:
            from account.models import User, AdminType
            user = User.objects.get(id=user_id, admin_type=AdminType.REGULAR_USER)
        except User.DoesNotExist:
            return self.error("Akun mahasiswa tidak ditemukan.")
        user.set_unusable_password()
        user.save(update_fields=["password"])
        return self.success("Password mahasiswa berhasil direset. Mahasiswa dapat membuat password baru saat login.")
