from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.payments"
    verbose_name = "Payments"

    def ready(self):
        self._register_periodic_tasks()

    @staticmethod
    def _register_periodic_tasks():
        try:
            from django_celery_beat.models import IntervalSchedule, PeriodicTask
        except ImportError:
            return

        try:
            schedule, _ = IntervalSchedule.objects.get_or_create(
                every=15,
                period=IntervalSchedule.MINUTES,
            )
            PeriodicTask.objects.get_or_create(
                name="SAP payment sync (every 15 min)",
                defaults={
                    "interval": schedule,
                    "task": "apps.payments.tasks.sync_sap_payments",
                    "enabled": True,
                },
            )
        except Exception:
            # DB tables may not exist yet during initial migration run
            pass
