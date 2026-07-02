from centres.models import Centre
from apps.accounts.models import User
from apps.accounts.permissions import IsLecturer, IsCentreAdmin
from apps.applications.models import Application

errors = []

# Centres
if Centre.objects.count() != 3:
    errors.append(f"Expected 3 centres, got {Centre.objects.count()}")
if not Centre.objects.filter(is_primary=True).exists():
    errors.append("No primary centre found")

# User model fields
user_fields = [f.name for f in User._meta.get_fields()]
for f in ['assigned_centre']:
    if f not in user_fields:
        errors.append(f"User missing field: {f}")

# Application model fields
app_fields = [f.name for f in Application._meta.get_fields()]
required = [
    'hexco_level', 'department',
    'student_category', 'is_resident', 'hostel_name', 'guardian_name',
    'ref', 'national_id_doc', 'academic_certs_doc', 'student_photo',
    'source', 'staff_captured_by',
    'preferred_centre', 'assigned_centre',
]
for f in required:
    if f not in app_fields:
        errors.append(f"Application missing field: {f}")

# Roles
role_values = [r[0] for r in User._meta.get_field('role').choices]
for r in ['LECTURER', 'CENTRE_ADMIN']:
    if r not in role_values:
        errors.append(f"Role missing: {r}")

if errors:
    print("SPRINT 0 FAILED:")
    for e in errors:
        print(f"  - {e}")
else:
    print("SPRINT 0 ALL CHECKS PASSED — ready for Sprint 1")
