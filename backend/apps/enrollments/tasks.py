import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def enroll_student_in_moodle(self, application_id: str):
    from apps.applications.models import Application
    from .models import Enrollment, EnrollmentStatus
    from .services import MoodleAPIError, MoodleEnrollmentService

    try:
        application = Application.objects.select_related("applicant", "course").get(
            id=application_id
        )
    except Application.DoesNotExist:
        logger.error("enroll_student_in_moodle: application %s not found", application_id)
        return

    enrollment, _ = Enrollment.objects.get_or_create(
        application=application,
        defaults={"moodle_course_id": application.course.moodle_course_id or 0},
    )

    if enrollment.status == EnrollmentStatus.ENROLLED:
        logger.info(
            "enroll_student_in_moodle: application %s already enrolled, skipping",
            application_id,
        )
        return

    enrollment.status = EnrollmentStatus.ENROLLING
    enrollment.error_message = None
    enrollment.save(update_fields=["status", "error_message"])

    svc = MoodleEnrollmentService()
    try:
        moodle_user_id = svc.get_or_create_user(application.applicant)
        enrollment.moodle_user_id = moodle_user_id
        enrollment.save(update_fields=["moodle_user_id"])

        svc.enroll_user(moodle_user_id, application.course.moodle_course_id)

        enrollment.status = EnrollmentStatus.ENROLLED
        enrollment.enrolled_at = timezone.now()
        enrollment.save(update_fields=["status", "enrolled_at"])

    except (MoodleAPIError, Exception) as exc:
        logger.exception(
            "enroll_student_in_moodle: Moodle enrol failed for application %s: %s",
            application_id,
            exc,
        )
        enrollment.status = EnrollmentStatus.FAILED
        enrollment.error_message = str(exc)[:500]
        enrollment.save(update_fields=["status", "error_message"])
        raise self.retry(exc=exc, countdown=300)

    try:
        application.enroll()
    except ValueError as exc:
        # State machine may already be ENROLLED (idempotent retry)
        logger.warning(
            "enroll_student_in_moodle: application.enroll() raised %s for %s",
            exc,
            application_id,
        )

    logger.info(
        "enroll_student_in_moodle: enrolled %s in %s (moodle_user_id=%s)",
        application.applicant.email,
        application.course.shortname,
        moodle_user_id,
    )


@shared_task(bind=True, max_retries=2)
def sync_enrollment_completions(self):
    from .models import Enrollment, EnrollmentStatus
    from .services import MoodleAPIError, MoodleEnrollmentService

    enrollments = Enrollment.objects.filter(
        status=EnrollmentStatus.ENROLLED,
        moodle_user_id__isnull=False,
    ).select_related("application__applicant", "application__course")

    svc = MoodleEnrollmentService()
    updated = 0
    errors = 0

    for enrollment in enrollments:
        try:
            completion = svc.get_completion_status(
                enrollment.moodle_user_id,
                enrollment.moodle_course_id,
            )
            enrollment.completion_status = completion

            last_access = svc.get_user_last_access(
                enrollment.moodle_user_id,
                enrollment.moodle_course_id,
            )
            if last_access:
                enrollment.last_access = last_access

            enrollment.save(update_fields=["completion_status", "last_access"])
            updated += 1

            completionstatus = (
                completion.get("completionstatus", {}) if isinstance(completion, dict) else {}
            )
            if completionstatus.get("completed"):
                logger.info(
                    "sync_enrollment_completions: %s completed course %s — certificate generation pending",
                    enrollment.application.applicant.email,
                    enrollment.application.course.shortname,
                )

        except MoodleAPIError as exc:
            logger.warning(
                "sync_enrollment_completions: Moodle error for enrollment %s: %s",
                enrollment.id,
                exc,
            )
            errors += 1
        except Exception as exc:
            logger.exception(
                "sync_enrollment_completions: unexpected error for enrollment %s: %s",
                enrollment.id,
                exc,
            )
            errors += 1

    logger.info(
        "sync_enrollment_completions: updated=%d errors=%d",
        updated,
        errors,
    )
