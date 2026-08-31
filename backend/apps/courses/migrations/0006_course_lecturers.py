# Generated manually to add course-level lecturer assignment while preserving
# existing intake-level lecturer assignments for backward compatibility.

from django.conf import settings
from django.db import migrations, models


def backfill_course_lecturers(apps, schema_editor):
    CourseSchedule = apps.get_model("courses", "CourseSchedule")

    for schedule in CourseSchedule.objects.exclude(lecturer__isnull=True).iterator():
        schedule.course.lecturers.add(schedule.lecturer_id)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("courses", "0005_courseschedule_lecturer"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="lecturers",
            field=models.ManyToManyField(
                blank=True,
                help_text="Lecturers who may manage this course and its student activity.",
                limit_choices_to={"role": "LECTURER"},
                related_name="assigned_courses",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(backfill_course_lecturers, noop_reverse),
    ]
