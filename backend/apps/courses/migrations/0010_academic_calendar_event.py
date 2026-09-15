import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0009_courseschedule_payment_due_date"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AcademicCalendarEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("event_type", models.CharField(choices=[
                    ("COMMENCEMENT", "Commencement"),
                    ("DEFERMENT", "Deferment"),
                    ("EXAMINATION", "Examination"), ("SEMESTER_START", "Semester start"),
                    ("SEMESTER_END", "Semester end"), ("BLOCK_START", "Block start"),
                    ("BLOCK_END", "Block end"), ("SEMESTER_BREAK", "Semester break"),
                    ("EXAM_FEE", "Examination fee"), ("MARKS_DEADLINE", "Marks deadline"),
                ], max_length=20)),
                ("title", models.CharField(max_length=255)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField(blank=True, null=True)),
                ("audience", models.CharField(choices=[
                    ("STUDENTS", "Students"), ("LECTURERS", "Lecturers"),
                    ("BOTH", "Students and lecturers"),
                ], default="STUDENTS", max_length=12)),
                ("timetable_url", models.URLField(blank=True, max_length=500)),
                ("published_at", models.DateTimeField(auto_now_add=True)),
                ("course", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="calendar_events", to="courses.course")),
                ("schedule", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="calendar_events", to="courses.courseschedule")),
                ("published_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="published_calendar_events", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-published_at"]},
        ),
    ]
