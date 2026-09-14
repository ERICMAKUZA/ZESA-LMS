from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("enrollments", "0004_enrollment_end_date_enrollment_is_suspended_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="EnrollmentAttendanceResponse",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("response", models.CharField(choices=[("CONFIRMED", "Confirmed"), ("DEFERRED", "Deferred"), ("PENDING_STAFF", "Pending staff review")], max_length=20)),
                ("responded_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("audit_note", models.TextField(blank=True, default="")),
                ("enrollment", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="attendance_response", to="enrollments.enrollment")),
                ("target_schedule", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="attendance_deferrals", to="courses.courseschedule")),
            ],
        ),
    ]
