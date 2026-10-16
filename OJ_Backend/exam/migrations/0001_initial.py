from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import utils.shortcuts


def seed_sessions(apps, schema_editor):
    ExamSession = apps.get_model("exam", "ExamSession")
    if ExamSession.objects.exists():
        return
    from django.utils.crypto import get_random_string
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    for slot in range(1, 6):
        ExamSession.objects.create(
            slot=slot,
            title="Sesi %d" % slot,
            access_code=get_random_string(8, alphabet),
            mode="judge",
        )


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("problem", "0014_problem_share_submission"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExamSession",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("slot", models.PositiveSmallIntegerField(unique=True)),
                ("title", models.TextField(default="")),
                ("access_code", models.TextField(unique=True)),
                ("mode", models.TextField(default="judge")),
                ("view_start", models.DateTimeField(blank=True, null=True)),
                ("view_end", models.DateTimeField(blank=True, null=True)),
                ("submit_start", models.DateTimeField(blank=True, null=True)),
                ("submit_end", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": "exam_session",
                "ordering": ("slot",),
            },
        ),
        migrations.CreateModel(
            name="ZipSubmission",
            fields=[
                ("id", models.TextField(db_index=True, default=utils.shortcuts.rand_str, primary_key=True, serialize=False)),
                ("original_name", models.TextField()),
                ("stored_path", models.TextField()),
                ("create_time", models.DateTimeField(auto_now_add=True)),
                ("problem", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="problem.Problem")),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="exam.ExamSession")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "exam_zip_submission",
                "ordering": ("-create_time",),
            },
        ),
        migrations.RunPython(seed_sessions, migrations.RunPython.noop),
    ]
