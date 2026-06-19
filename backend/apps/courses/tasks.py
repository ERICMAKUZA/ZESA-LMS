import logging

from celery import shared_task

from .services import MoodleClient

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def sync_courses_from_moodle(self):
    from .models import Course, CourseCategory

    client = MoodleClient()
    try:
        moodle_courses = client.get_courses()
    except Exception as exc:
        logger.exception("Moodle course sync failed: %s", exc)
        raise self.retry(exc=exc, countdown=60)

    synced = 0
    for mc in moodle_courses:
        category = None
        if mc.get("categoryid"):
            category, _ = CourseCategory.objects.get_or_create(
                moodle_id=mc["categoryid"],
                defaults={"name": mc.get("categoryname", "Uncategorised")},
            )

        Course.objects.update_or_create(
            moodle_course_id=mc["id"],
            defaults={
                "shortname": mc.get("shortname", ""),
                "fullname": mc.get("fullname", ""),
                "summary": mc.get("summary", ""),
                "category": category,
                "is_active": mc.get("visible", 1) == 1,
                "thumbnail_url": mc.get("courseimage", ""),
            },
        )
        synced += 1

    logger.info("Moodle sync complete: %d courses processed", synced)
    return {"synced": synced}
