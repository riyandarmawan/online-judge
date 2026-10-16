from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("exam", "0001_initial"),
        ("problem", "0014_problem_share_submission"),
    ]

    operations = [
        migrations.AddField(
            model_name="problem",
            name="exam_session",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="exam.ExamSession"),
        ),
        migrations.AddField(
            model_name="problem",
            name="answer_filename",
            field=models.TextField(blank=True, null=True),
        ),
    ]
