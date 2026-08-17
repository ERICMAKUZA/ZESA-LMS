import logging
from datetime import date, timedelta

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_confirmed_payment(self, payment_id: str):
    from .models import Payment
    from .services import PaynowService

    try:
        payment = Payment.objects.select_related(
            "application__applicant", "application__course"
        ).get(id=payment_id)
    except Payment.DoesNotExist:
        logger.error("process_confirmed_payment: payment %s not found", payment_id)
        return

    if not payment.paynow_poll_url:
        logger.error("process_confirmed_payment: no poll_url for payment %s", payment_id)
        return

    svc = PaynowService()
    result = svc.check_payment_status(payment.paynow_poll_url)

    if not result.get("paid"):
        logger.warning(
            "process_confirmed_payment: payment %s not confirmed by poll (status=%s)",
            payment_id,
            result.get("status"),
        )
        return

    try:
        payment.confirm()
        logger.info("process_confirmed_payment: payment %s confirmed", payment_id)
    except Exception as exc:
        logger.exception("process_confirmed_payment: confirm() failed for %s: %s", payment_id, exc)
        raise self.retry(exc=exc, countdown=60)

    notify_payment_confirmed(payment)

    from apps.enrollments.tasks import enroll_student_in_moodle
    enroll_student_in_moodle.apply_async([str(payment.application_id)])


@shared_task(bind=True, max_retries=3)
def sync_sap_payments(self):
    from .models import Payment, PaymentMethod, PaymentStatus, SAPSyncLog
    from .services import SAPService

    date_to = date.today().isoformat()
    date_from = (date.today() - timedelta(days=7)).isoformat()

    svc = SAPService()
    records = svc.get_training_payments(date_from, date_to)

    processed = 0
    matched = 0
    errors = []

    for record in records:
        processed += 1
        try:
            application = svc.match_application(record)
            if not application:
                continue

            if Payment.objects.filter(application=application).exclude(status=PaymentStatus.FAILED).exists():
                continue

            payment = Payment.objects.create(
                application=application,
                amount=record["amount"],
                method=PaymentMethod.SAP_BUDGET,
                sap_document_number=record["document_number"],
                sap_cost_center=record["cost_center"],
            )
            payment.confirm()
            matched += 1
            notify_payment_confirmed(payment)

            from apps.enrollments.tasks import enroll_student_in_moodle
            enroll_student_in_moodle.delay(str(application.id))

        except Exception as exc:
            logger.exception("sync_sap_payments: error processing record %s: %s", record, exc)
            errors.append({"record": record, "error": str(exc)})

    SAPSyncLog.objects.create(
        records_processed=processed,
        records_matched=matched,
        errors=errors,
        success=len(errors) == 0,
    )
    logger.info(
        "sync_sap_payments: processed=%d matched=%d errors=%d",
        processed, matched, len(errors),
    )


def notify_payment_confirmed(payment):
    from apps.workflows.services import queue_notification

    app = payment.application
    queue_notification(
        recipient=app.applicant,
        subject=f"Payment confirmed: {app.course.fullname}",
        message=(
            f"Hi {app.applicant.first_name},\n\n"
            f"Your payment for {app.course.fullname} has been confirmed.\n\n"
            "Your Moodle enrolment is now being prepared. You will receive another notification once access is ready."
        ),
        application=app,
        action_url=f"/applications/{app.id}",
    )
