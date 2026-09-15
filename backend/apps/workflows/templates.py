"""Versioned wording for lifecycle messages sent by email and shown in the bell."""

from django.conf import settings

BANK = "STANBIC, Park Lane Branch"
ACCOUNT_NAME = "ZESA National Training Centre"
ACCOUNT_NUMBER = "9140000940908 (Nostro)"
COLLECTION_HOURS = "0830-1600hrs Monday to Friday"


def _display_date(value):
    if value is None:
        return "to be announced"
    return f"{value.day} {value:%B %Y}"


def render_acceptance(application, schedule):
    course_name = application.course.fullname
    start_date = schedule.get_approximate_start_date() if schedule else None
    due_date = (schedule.payment_due_date or start_date) if schedule else None
    amount = f"{application.course.price:.2f}" if application.course.price is not None else "to be confirmed"

    return (
        f"Acceptance: {course_name}",
        f"You have been accepted for {course_name}, commencing on {_display_date(start_date)}. "
        f"You are required to pay full course fees of USD {amount} by {_display_date(due_date)}. "
        f"Banking details: Bank: {BANK}. Account Name: {ACCOUNT_NAME}. "
        f"Account Number: {ACCOUNT_NUMBER}. Upload proof of payment.",
    )


def render_certificate_collection(certificate):
    course_name = certificate.course.fullname
    return (
        f"Certificate collection: {course_name}",
        f"Your certificates for {course_name} are ready for collection. "
        f"Collection time {COLLECTION_HOURS}.",
    )


def render_calendar_event(event, recipient_role):
    scope = event.course.fullname if event.course_id else event.title
    start = _display_date(event.start_date)
    end = _display_date(event.end_date)
    event_type = event.event_type

    if event_type == "COMMENCEMENT":
        message = f"The {scope} course will commence on {start}. Kindly confirm attendance."
    elif event_type == "DEFERMENT":
        new_date = end if event.end_date else "TBA"
        message = (
            f"Please be advised {scope} course which was scheduled to commence on {start} "
            f"has been postponed to {new_date}."
        )
    elif event_type == "EXAMINATION":
        message = (
            f"Examinations for {scope} will be held from {start} to {end}. "
            f"Timetable: {event.timetable_url}."
        )
    elif event_type == "SEMESTER_START":
        message = (
            f"The {scope} semester runs from {start} to {end}. "
            "Please settle all outstanding course fees before commencement."
        )
    elif event_type == "SEMESTER_END":
        message = (
            f"The {scope} semester runs from {start} and ends on {end}. "
            "Please settle all outstanding course fees."
        )
    elif event_type == "BLOCK_START":
        message = (
            f"The {scope} block runs from {start} to {end}. "
            "Please settle all outstanding course fees before commencement."
        )
    elif event_type == "BLOCK_END":
        message = (
            f"The {scope} block runs from {start} and ends on {end}. "
            "Please settle all outstanding course fees."
        )
    elif event_type == "SEMESTER_BREAK":
        message = f"Semester break for {scope} runs from {start} to {end}."
    elif event_type == "EXAM_FEE":
        message = (
            f"Examination fee notice for {scope} on {start}. "
            "Please verify the total amount with the current examination-fee schedule before payment."
        )
    elif event_type == "MARKS_DEADLINE" and recipient_role == "LECTURER":
        message = f"Deadline for submission of marks: {start}."
    elif event_type == "MARKS_DEADLINE":
        message = f"Kindly verify your coursework marks by {start}."
    else:
        raise ValueError(f"Unsupported calendar event type: {event_type}")

    return f"Academic calendar: {event.title}", message


def render_upcoming_courses(quarter_key, schedules):
    lines = [f"Upcoming HEXCO and UZ courses for {quarter_key}:"]
    portal_url = settings.PORTAL_BASE_URL.rstrip("/")
    for schedule in schedules:
        lines.append(
            f"- {schedule.course.fullname} - {_display_date(schedule.get_approximate_start_date())}: "
            f"{portal_url}/courses/{schedule.course_id}"
        )
    return f"Upcoming courses ALERT {quarter_key}", "\n".join(lines)
