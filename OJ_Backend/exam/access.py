import ipaddress
import os

from django.conf import settings
from django.utils.dateparse import parse_datetime
from django.utils.html import escape
from django.utils.timezone import get_current_timezone, is_naive, make_aware

from utils.api import APIError
from utils.shortcuts import rand_str

from .models import ExamMode, ExamSession, ExamStudentSession

UNLOCK_SESSION_KEY = "exam_unlocks"


def portal_secret():
    directory = os.path.join(settings.DATA_DIR, "config")
    path = os.path.join(directory, "dosen_portal.key")
    if not os.path.exists(path):
        os.makedirs(directory, exist_ok=True)
        with open(path, "w") as f:
            f.write(rand_str(48))
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
    with open(path, "r") as f:
        return f.read().strip()


def is_private_ip(value):
    if not value:
        return False
    ip_text = value.split(",")[0].strip()
    if ip_text.startswith("::ffff:"):
        ip_text = ip_text[7:]
    try:
        ip = ipaddress.ip_address(ip_text)
    except ValueError:
        return False
    return ip.is_private or ip.is_loopback or ip.is_link_local


def unlocked_session_ids(request):
    user = getattr(request, "user", None)
    if user and user.is_authenticated and not user.is_admin_role():
        student_session = ExamStudentSession.objects.filter(user=user).values_list("session_id", flat=True).first()
        if student_session:
            return [student_session]
        return []
    raw = request.session.get(UNLOCK_SESSION_KEY) or []
    ids = []
    for item in raw:
        try:
            ids.append(int(item))
        except (TypeError, ValueError):
            continue
    return ids


def remember_unlock(request, session_id):
    user = getattr(request, "user", None)
    if user and user.is_authenticated and not user.is_admin_role():
        existing = ExamStudentSession.objects.filter(user=user).first()
        if not existing:
            ExamStudentSession.objects.create(user=user, session_id=session_id)
        else:
            if existing.session_id != session_id:
                existing.session_id = session_id
                existing.save()
        request.session[UNLOCK_SESSION_KEY] = [session_id]
    else:
        ids = unlocked_session_ids(request)
        if session_id not in ids:
            ids.append(session_id)
        request.session[UNLOCK_SESSION_KEY] = ids


def visible_session_ids(request):
    """
    None means the caller is a dosen and may see every exam problem.
    A list is the sessions a mahasiswa may currently view.
    """
    user = getattr(request, "user", None)
    if user and user.is_authenticated and user.is_admin_role():
        return None
    if not user or not user.is_authenticated:
        return []
    allowed = []
    unlocked = unlocked_session_ids(request)
    for session in ExamSession.objects.filter(id__in=unlocked):
        if session.can_view:
            allowed.append(session.id)
    return allowed


def filter_exam_problems(request, queryset):
    allowed = visible_session_ids(request)
    if allowed is None:
        return queryset
    return queryset.filter(exam_session_id__in=allowed)


def student_can_manage(request):
    user = getattr(request, "user", None)
    return bool(user and user.is_authenticated and user.is_admin_role())


def submission_block_reason(request, problem, language):
    session = problem.exam_session
    if session is None:
        if student_can_manage(request):
            return None
        return "Soal tidak tersedia. Masukkan kode akses ujian terlebih dahulu."
    if session.mode == ExamMode.ARCHIVE:
        return "Soal ini dikumpulkan sebagai berkas zip, bukan kode sumber."
    if session.mode == ExamMode.JUDGE and language != "C":
        return "Ujian ini hanya menerima bahasa C."
    if student_can_manage(request):
        return None
    if session.id not in unlocked_session_ids(request):
        return "Masukkan kode akses sebelum mengumpulkan jawaban."
    if not session.can_submit:
        return "Akses pengumpulan jawaban sedang ditutup."
    return None


def _resolve_answer_filename(expected_pattern, username="", name=""):
    if not expected_pattern:
        return ""
    import re
    pattern = expected_pattern.strip()
    user_str = str(username or "{NIM}").strip()
    name_str = str(name or "{NAMA}").strip()
    resolved = re.sub(r"(?i)\{(?:nim|username)\}", user_str, pattern)
    resolved = re.sub(r"(?i)\[(?:nim|username)\]", user_str, resolved)
    resolved = re.sub(r"(?i)\{nama\}", name_str, resolved)
    resolved = re.sub(r"(?i)\[nama\]", name_str, resolved)
    return resolved


def check_answer_filename(filename, expected_pattern, nim, student_name):
    import re
    if not filename.lower().endswith(".zip"):
        return False, "Jawaban harus berformat berkas .zip."

    pattern = (expected_pattern or "").strip()
    if not pattern or pattern == "*.zip":
        return True, ""

    nim = str(nim or "").strip()
    raw_name = str(student_name or "").strip()

    p1 = pattern
    p1 = re.sub(r"(?i)\{(?:nim|username)\}", "{NIM}", p1)
    p1 = re.sub(r"(?i)\[(?:nim|username)\]", "{NIM}", p1)
    p1 = re.sub(r"(?i)\{nama\}", "{NAMA}", p1)
    p1 = re.sub(r"(?i)\[nama\]", "{NAMA}", p1)
    p1 = re.sub(r"(?i)(?<![a-zA-Z0-9\{])(?:nim|username)(?![a-zA-Z0-9\}])", "{NIM}", p1)
    p1 = re.sub(r"(?i)(?<![a-zA-Z0-9\{])nama(?![a-zA-Z0-9\}])", "{NAMA}", p1)

    c1 = p1.replace("{NIM}", nim).replace("{NAMA}", re.sub(r"[^\w\-]", "", raw_name))
    c2 = p1.replace("{NIM}", nim).replace("{NAMA}", re.sub(r"\s+", "_", raw_name))
    clean_upload = filename.strip().lower()

    if clean_upload == c1.strip().lower() or clean_upload == c2.strip().lower():
        return True, ""

    reg = re.escape(p1).replace(r"\{NIM\}", re.escape(nim)).replace(r"\{NAMA\}", r"[a-zA-Z0-9_\-]+")
    if re.fullmatch(reg, filename.strip(), re.IGNORECASE):
        return True, ""

    example = c2 if "{NAMA}" in p1 else c1
    return False, f"Nama berkas harus sesuai format: {pattern} (contoh: {example})"


def apply_exam_fields(request, item, problem):
    session = problem.exam_session
    item["exam_mode"] = session.mode if session else None
    item["session_title"] = session.title if session else None
    username = request.user.username if (request.user and request.user.is_authenticated) else ""
    item["answer_filename"] = _resolve_answer_filename(problem.answer_filename, username)
    item["answer_filename_template"] = problem.answer_filename
    if student_can_manage(request):
        item["can_submit"] = True
    else:
        item["can_submit"] = bool(session and session.can_submit)
    if session and session.mode == ExamMode.JUDGE:
        item["languages"] = ["C"]
    if session and session.mode == ExamMode.ARCHIVE:
        tpl = problem.template if isinstance(problem.template, dict) else {}
        item["pdf_url"] = tpl.get("pdf_url")
        item["pdf_name"] = tpl.get("pdf_name")
        item["my_zip"] = None
        from .models import ZipSubmission
        latest = None
        if request.user and request.user.is_authenticated:
            latest = ZipSubmission.objects.filter(problem=problem, user=request.user).first()
        else:
            cached = request.session.get("my_zip_" + str(problem.id))
            if cached:
                item["my_zip"] = cached
        if latest:
            profile = getattr(latest.user, "userprofile", None)
            info = f"{latest.user.username} - {profile.real_name}" if (profile and profile.real_name) else latest.user.username
            item["my_zip"] = {
                "original_name": latest.original_name,
                "create_time": latest.create_time.isoformat(),
                "student_info": info,
            }
    return item


def parse_dt(value):
    if value in (None, ""):
        return None
    parsed = parse_datetime(str(value))
    if parsed is None:
        raise APIError("Format waktu tidak valid")
    if is_naive(parsed):
        parsed = make_aware(parsed, get_current_timezone())
    return parsed


def plain_to_html(text):
    escaped = escape(text or "")
    return escaped.replace("\n", "<br>")


def html_to_plain(value):
    import re
    text = re.sub(r"(?i)<br\s*/?>", "\n", value or "")
    text = re.sub(r"<[^>]+>", "", text)
    return text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#39;", "'").replace("&quot;", '"')
