from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0010_academic_calendar_event"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="qualification_assessment_enabled",
            field=models.BooleanField(
                blank=True,
                default=None,
                help_text="Override the course type's qualification-assessment setting for this course.",
                null=True,
            ),
        ),
    ]
