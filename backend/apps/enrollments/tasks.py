import logging
import secrets

from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def _ensure_zntc_email(applicant):
    """Generate and persist a ZNTC student email (first.last@students.zntc.ac.zw) if missing."""
    if applicant.zntc_email:
        return applicant.zntc_email

    from apps.accounts.models import User

    first = (applicant.first_name or '').strip().lower().replace(' ', '')
    last = (applicant.last_name or '').strip().lower().replace(' ', '')
    base = f"{first}.{last}".strip('.') or 'student'
    candidate = f"{base}@students.zntc.ac.zw"
    suffix = 1
    while User.objects.filter(zntc_email=candidate).exclude(pk=applicant.pk).exists():
        candidate = f"{base}{suffix}@students.zntc.ac.zw"
        suffix += 1

    applicant.zntc_email = candidate
    applicant.save(update_fields=['zntc_email'])
    return candidate


@shared_task(bind=True, max_retries=3)
def enroll_student_in_moodle(self, application_id: str):
    """Legacy entry point — delegates to application.enroll() which triggers sync_to_moodle."""
    from apps.applications.models import Application, ApplicationStatus

    try:
        application = Application.objects.select_related("applicant", "course").get(
            id=application_id
        )
    except Application.DoesNotExist:
        logger.error("enroll_student_in_moodle: application %s not found", application_id)
        return

    if application.status == ApplicationStatus.ENROLLED:
        logger.info("enroll_student_in_moodle: %s already enrolled, skipping", application_id)
        return

    try:
        application.enroll()
    except ValueError as exc:
        logger.warning("enroll_student_in_moodle: enroll() raised %s for %s", exc, application_id)
        raise self.retry(exc=exc, countdown=300)

    logger.info("enroll_student_in_moodle: enroll() complete for %s", application_id)


@shared_task(
    name='enrollments.sync_to_moodle',
    bind=True, max_retries=5, default_retry_delay=60 * 15,
)
def sync_to_moodle(self, enrollment_pk):
    from .models import Enrollment
    from .moodle_client import MoodleClient

    try:
        enrollment = Enrollment.objects.select_related(
            'application__applicant',
            'application__course',
            'application__assigned_centre',
        ).get(pk=enrollment_pk)
    except Enrollment.DoesNotExist:
        return

    if enrollment.status == 'ENROLLED' and enrollment.moodle_user_id:
        logger.info("sync_to_moodle: %s already synced, skipping", enrollment_pk)
        return

    was_enrolling = enrollment.status == 'ENROLLING'
    enrollment.status = 'ENROLLING'
    enrollment.save(update_fields=['status'])

    applicant = enrollment.application.applicant
    course = enrollment.application.course
    centre = enrollment.application.assigned_centre
    client = MoodleClient()

    if not was_enrolling:
        from apps.workflows.services import queue_notification

        queue_notification(
            recipient=applicant,
            subject=f"Enrolment setup started: {course.fullname}",
            message=(
                f"Hi {applicant.first_name},\n\n"
                f"We are setting up your Moodle access for {course.fullname}.\n\n"
                "You will receive your learning portal details once setup is complete."
            ),
            application=enrollment.application,
            action_url=f"/applications/{enrollment.application_id}",
        )

    zntc_email = _ensure_zntc_email(applicant)

    try:
        if settings.DEMO_MODE or not client.token:
            moodle_user_id = 9000 + (hash(str(enrollment_pk)) % 1000)
            temp_password = ''
        else:
            # 1. Create Moodle user
            username = zntc_email.split('@')[0]
            temp_password = secrets.token_urlsafe(12) + "Aa1!"
            users = client.create_user(
                username=username,
                email=zntc_email,
                firstname=applicant.first_name,
                lastname=applicant.last_name,
                password=temp_password,
            )
            moodle_user_id = users[0]['id'] if users else None

            if moodle_user_id:
                # 2. Enrol in course
                client.enrol_user(moodle_user_id, course.moodle_course_id)

                # 3. Add to centre cohort
                cohort_map = getattr(settings, 'MOODLE_CENTRE_COHORT_IDS', {})
                if centre and centre.name in cohort_map:
                    client.add_to_cohort(moodle_user_id, cohort_map[centre.name])

                # 4. Set custom profile fields
                client.update_user_profile(moodle_user_id, {
                    'hexco_level': enrollment.application.hexco_level or '',
                    'department': enrollment.application.department or '',
                    'student_category': enrollment.application.student_category or '',
                    'centre': centre.name if centre else '',
                })

        # 5. Save result
        enrollment.moodle_user_id = moodle_user_id
        enrollment.moodle_temp_password = temp_password
        enrollment.status = 'ENROLLED'
        enrollment.enrolled_at = timezone.now()
        enrollment.save(update_fields=[
            'status', 'moodle_user_id', 'moodle_temp_password', 'enrolled_at',
        ])
        dispatch_credentials_email.delay(str(enrollment.pk))
        _notify_lecturer_enrolled(enrollment)

    except Exception as exc:
        logger.exception("sync_to_moodle: failed for enrollment %s: %s", enrollment_pk, exc)
        enrollment.status = 'FAILED'
        enrollment.error_message = str(exc)[:500]
        enrollment.save(update_fields=['status', 'error_message'])
        if self.request.retries >= self.max_retries - 1:
            _notify_enrollment_failed(enrollment)
        raise self.retry(exc=exc)


@shared_task(
    name='enrollments.dispatch_credentials_email',
    max_retries=3, default_retry_delay=60,
)
def dispatch_credentials_email(enrollment_pk):
    from .models import Enrollment

    try:
        enrollment = Enrollment.objects.select_related(
            'application__applicant', 'application__course',
            'application__assigned_centre',
        ).get(pk=enrollment_pk)
    except Enrollment.DoesNotExist:
        return

    applicant = enrollment.application.applicant
    course = enrollment.application.course
    centre = enrollment.application.assigned_centre
    moodle_url = f"{settings.MOODLE_BASE_URL.rstrip('/')}/login/index.php"
    portal_url = getattr(settings, 'PORTAL_BASE_URL', 'http://localhost:3000')
    username = applicant.zntc_email.split('@')[0] if applicant.zntc_email else (
        applicant.student_id or applicant.email.split('@')[0]
    )

    subject = f"Welcome to ZNTC — Your Learning Portal Access, {applicant.first_name}"
    message = f"""Dear {applicant.first_name} {applicant.last_name},

Congratulations! Your enrolment at the ZESA National Training Centre has been confirmed.

STUDENT DETAILS
---------------
Student ID  : {applicant.student_id or 'Pending'}
Programme   : {course.fullname if course else 'N/A'}
Centre      : {centre.name if centre else 'N/A'}

MOODLE LEARNING PORTAL ACCESS
--------------------------------
URL         : {moodle_url}
Username    : {username}
Password    : {enrollment.moodle_temp_password}

IMPORTANT: You will be asked to change your password on first login.
Please keep your credentials safe and do not share them.

STUDENT PORTAL
--------------
Track your application and download certificates at:
{portal_url}/dashboard

If you have any questions, contact us at training@zntc.ac.zw

Regards,
ZESA National Training Centre
Ganges Road, Workington, Harare""".strip()

    from apps.workflows.services import queue_notification

    queue_notification(
        recipient=applicant,
        subject=subject,
        message=message,
        application=enrollment.application,
        action_url="/dashboard",
    )


@shared_task(name='enrollments.unenrol_from_moodle')
def unenrol_from_moodle(enrollment_pk, de_enrolment_type, reason):
    from django.utils import timezone as tz
    from .models import Enrollment
    from .moodle_client import MoodleClient

    try:
        enrollment = Enrollment.objects.select_related(
            'application__applicant', 'application__course',
        ).get(pk=enrollment_pk)
    except Enrollment.DoesNotExist:
        return

    client = MoodleClient()
    try:
        client._call(
            'enrol_manual_unenrol_users',
            **{
                'enrolments[0][userid]': enrollment.moodle_user_id,
                'enrolments[0][courseid]': enrollment.moodle_course_id,
            }
        )
    except Exception as exc:
        logger.warning("unenrol_from_moodle: Moodle unenrol failed for %s: %s", enrollment_pk, exc)

    enrollment.status = 'UNENROLLED'
    enrollment.unenrolled_at = tz.now()
    enrollment.de_enrolment_reason = reason
    enrollment.de_enrolment_type = de_enrolment_type
    enrollment.save(update_fields=[
        'status', 'unenrolled_at', 'de_enrolment_reason', 'de_enrolment_type',
    ])

    from apps.applications.models import ApplicationStatus
    enrollment.application.status = ApplicationStatus.DE_ENROLLED
    enrollment.application.save(update_fields=['status', 'updated_at'])

    applicant = enrollment.application.applicant
    verb = 'withdrawn' if de_enrolment_type == 'VOLUNTARY' else 'terminated'
    from apps.workflows.services import queue_notification

    queue_notification(
        recipient=applicant,
        subject=f"Your ZNTC enrolment status has changed — {enrollment.application.ref}",
        message=(
            f"Dear {applicant.first_name},\n\n"
            f"Your enrolment has been {verb}.\n"
            f"Reason: {reason}\n\n"
            f"Please contact us at training@zntc.ac.zw if you have questions.\n\n"
            f"Regards,\nZESA National Training Centre"
        ),
        application=enrollment.application,
        action_url=f"/applications/{enrollment.application_id}",
    )


def _notify_enrollment_failed(enrollment):
    from apps.workflows.services import queue_notification, queue_notifications, staff_recipients

    app = enrollment.application
    queue_notification(
        recipient=app.applicant,
        subject=f"Moodle enrolment needs attention: {app.course.fullname}",
        message=(
            f"Hi {app.applicant.first_name},\n\n"
            f"Your application for {app.course.fullname} was approved, but Moodle access could not be completed automatically.\n\n"
            "The training team has been notified and will resolve it."
        ),
        application=app,
        action_url=f"/applications/{app.id}",
    )
    queue_notifications(
        recipients=staff_recipients("ADMIN", "SUPERADMIN"),
        subject=f"Moodle enrolment failed: {app.ref}",
        message=(
            f"Moodle enrolment failed for {app.applicant.full_name} ({app.applicant.email}).\n\n"
            f"Course: {app.course.fullname}\n"
            f"Error: {enrollment.error_message or 'Unknown error'}"
        ),
        application=app,
        action_url=f"/admin/applications/{app.id}",
    )


def _notify_lecturer_enrolled(enrollment):
    schedule = enrollment.schedule
    lecturer = getattr(schedule, "lecturer", None)
    if not lecturer:
        return

    from apps.workflows.services import queue_notification

    app = enrollment.application
    queue_notification(
        recipient=lecturer,
        subject=f"Student enrolled: {app.applicant.full_name}",
        message=(
            f"{app.applicant.full_name} has been enrolled in {app.course.fullname}.\n\n"
            f"Student ID: {app.applicant.student_id or 'Pending'}\n"
            f"Email: {app.applicant.email}\n\n"
            "Open My Courses to manage attendance, notices, timetable, and course operations."
        ),
        application=app,
        action_url="/lecturer/courses",
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
            if completionstatus.get("completed") and not hasattr(enrollment, "certificate"):
                from apps.certificates.models import Certificate

                try:
                    cert = Certificate.issue_from_enrollment(enrollment)
                    logger.info(
                        "sync_enrollment_completions: issued certificate %s to %s for %s",
                        cert.certificate_number,
                        enrollment.application.applicant.email,
                        enrollment.application.course.shortname,
                    )
                except ValueError as exc:
                    logger.warning(
                        "sync_enrollment_completions: could not issue certificate for enrollment %s: %s",
                        enrollment.id, exc,
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
