from apps.applications.models import Application
from apps.enrollments.models import Enrollment
from apps.accounts.models import User

errors = []

# Public tracking fields
app_fields = [f.name for f in Application._meta.get_fields()]
for f in ['escalated', 'escalated_at', 'code_of_conduct_signed',
          'code_of_conduct_signed_at', 'source', 'ref']:
    if f not in app_fields:
        errors.append(f"Application missing: {f}")

# DE_ENROLLED status
status_choices = dict(Application._meta.get_field('status').choices)
if 'DE_ENROLLED' not in status_choices:
    errors.append("Status DE_ENROLLED missing")

# Student ID on User
user_fields = [f.name for f in User._meta.get_fields()]
if 'student_id' not in user_fields:
    errors.append("User missing student_id")

# Enrollment Moodle fields
enroll_fields = [f.name for f in Enrollment._meta.get_fields()]
for f in ['moodle_user_id', 'moodle_course_id', 'status']:
    if f not in enroll_fields:
        errors.append(f"Enrollment missing: {f}")

# Celery tasks importable
try:
    from apps.enrollments.tasks import sync_to_moodle, dispatch_credentials_email, unenrol_from_moodle
except ImportError as e:
    errors.append(f"Celery task import failed: {e}")

# Moodle client importable
try:
    from apps.enrollments.moodle_client import MoodleClient
    c = MoodleClient()
    assert c.api_url.endswith('/webservice/rest/server.php')
except Exception as e:
    errors.append(f"MoodleClient error: {e}")

if errors:
    print("SPRINT 1 FAILED:")
    for e in errors:
        print(f"  - {e}")
else:
    print("SPRINT 1 ALL CHECKS PASSED — ready for Sprint 2 (Quotation Engine)")
