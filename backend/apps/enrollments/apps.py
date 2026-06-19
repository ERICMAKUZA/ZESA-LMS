from django.apps import AppConfig


class EnrollmentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.enrollments"
    verbose_name = "Enrollments"

    def ready(self):
        self._register_periodic_tasks()

    @staticmethod
    def _register_periodic_tasks():
        try:
            from django_celery_beat.models import CrontabSchedule, PeriodicTask
        except ImportError:
            return

        try:
            # Daily at midnight Africa/Harare
            schedule, _ = CrontabSchedule.objects.get_or_create(
                minute="0",
                hour="0",
                day_of_week="*",
                day_of_month="*",
                month_of_year="*",
                defaults={"timezone": "Africa/Harare"},
            )
            PeriodicTask.objects.get_or_create(
                name="Sync enrollment completions from Moodle (daily midnight)",
                defaults={
                    "crontab": schedule,
                    "task": "apps.enrollments.tasks.sync_enrollment_completions",
                    "enabled": True,
                },
            )
        except Exception:
            # DB tables may not exist during initial migration run
            pass
