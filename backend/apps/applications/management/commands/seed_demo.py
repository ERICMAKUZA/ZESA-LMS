"""
Seed realistic ZESA-relevant demo data for an interface design session.
Idempotent: safe to run multiple times.
"""
from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone


def _h(history_obj, backdated):
    from apps.applications.models import ApplicationStatusHistory
    ApplicationStatusHistory.objects.filter(pk=history_obj.pk).update(changed_at=backdated)


def _make_history(app, from_status, to_status, changed_by, at):
    from apps.applications.models import ApplicationStatusHistory
    h = ApplicationStatusHistory.objects.create(
        application=app,
        from_status=from_status,
        to_status=to_status,
        changed_by=changed_by,
        changed_by_ec_number=getattr(changed_by, 'ec_number', '') or '',
        changed_by_name_snapshot=changed_by.full_name if changed_by else 'System',
        notes="",
    )
    _h(h, at)
    return h


class Command(BaseCommand):
    help = "Seed ZESA-relevant demo data (idempotent)"

    def handle(self, *args, **options):
        from apps.accounts.models import User
        from apps.applications.models import (
            Application,
            ApplicationStatus,
            ApplicationStatusHistory,
        )
        from apps.courses.models import Course, CourseCategory
        from apps.enrollments.models import Enrollment, EnrollmentStatus
        from apps.payments.models import Payment, PaymentMethod, PaymentStatus

        now = timezone.now()

        # ── 1. Look up real courses (seed_courses must run first) ─────────────

        required = ["RPA-DRONE", "SOLAR-PV", "33KV-SWITCH", "VFL", "OHS-PS"]
        missing = [s for s in required if not Course.objects.filter(shortname=s).exists()]
        if missing:
            self.stderr.write(
                self.style.ERROR(
                    f"ERROR: Real courses not found: {missing}. "
                    "Run 'python manage.py seed_courses' first."
                )
            )
            return

        course_drone = Course.objects.get(shortname="RPA-DRONE")
        course_solar = Course.objects.get(shortname="SOLAR-PV")
        course_tech  = Course.objects.get(shortname="33KV-SWITCH")
        course_lead  = Course.objects.get(shortname="VFL")
        course_digital = Course.objects.get(shortname="OHS-PS")

        # ── 3. Users ──────────────────────────────────────────────────────────

        def make_user(email, first, last, role, dept="", emp_id=None,
                      is_staff=False, is_superuser=False):
            user, created = User.objects.get_or_create(
                email=email,
                defaults=dict(
                    first_name=first,
                    last_name=last,
                    role=role,
                    department=dept,
                    employee_id=emp_id,
                    is_staff=is_staff,
                    is_superuser=is_superuser,
                    is_active=True,
                ),
            )
            if created:
                user.set_password("Demo1234!")
                user.save(update_fields=["password"])
            return user

        admin = make_user(
            "admin@zesa.co.zw", "Admin", "ZESA", User.Role.ADMIN,
            is_staff=True, is_superuser=True,
        )
        reviewer = make_user(
            "reviewer@zesa.co.zw", "Tsitsi", "Mapfumo", User.Role.REVIEWER,
            dept="Human Resources",
        )
        approver_demo = make_user(
            "approver.demo@zesa.co.zw", "Demo", "Reviewer", User.Role.REVIEWER,
            dept="Human Resources",
        )
        make_user("finance@zesa.co.zw", "Prosper", "Ncube", User.Role.FINANCE, dept="Finance")
        make_user("lecturer@zntc.ac.zw", "Rutendo", "Mwangi", User.Role.LECTURER, dept="Training")

        student_demo = make_user(
            "student.demo@zesa.co.zw", "Demo", "Student", User.Role.STUDENT,
            dept="ICT", emp_id="ZESA-DEMO-001",
        )

        student_specs = [
            ("chiedza.mutasa@zesa.co.zw",    "Chiedza",    "Mutasa",    "Generation & Transmission", "ZESA-2024-001"),
            ("takudzwa.ndlovu@zesa.co.zw",   "Takudzwa",   "Ndlovu",    "Distribution",              "ZESA-2024-002"),
            ("farai.chikomba@zesa.co.zw",    "Farai",      "Chikomba",  "ICT",                       "ZESA-2024-003"),
            ("nyasha.mupambi@zesa.co.zw",    "Nyasha",     "Mupambi",   "Finance",                   "ZESA-2024-004"),
            ("blessing.zulu@zesa.co.zw",     "Blessing",   "Zulu",      "HR",                        "ZESA-2024-005"),
            ("simbarashe.dube@zesa.co.zw",   "Simbarashe", "Dube",      "Engineering",               "ZESA-2024-006"),
            ("tendai.moyo@zesa.co.zw",       "Tendai",     "Moyo",      "Generation & Transmission", "ZESA-2024-007"),
            ("rumbidzai.chikomo@zesa.co.zw", "Rumbidzai",  "Chikomo",   "Distribution",              "ZESA-2024-008"),
            ("tinashe.mhuru@zesa.co.zw",     "Tinashe",    "Mhuru",     "ICT",                       "ZESA-2024-009"),
        ]
        students = [
            make_user(email, first, last, User.Role.STUDENT, dept=dept, emp_id=emp)
            for email, first, last, dept, emp in student_specs
        ]
        (s0, s1, s2, s3, s4, s5, tendai, rumbidzai, tinashe) = students

        # ── 4. Applications ───────────────────────────────────────────────────

        ST = ApplicationStatus
        apps_made = 0

        def get_or_create_app(applicant, course, **fields):
            nonlocal apps_made
            app, created = Application.objects.get_or_create(
                applicant=applicant,
                course=course,
                defaults=dict(
                    motivation=(
                        "I believe this course will significantly enhance my professional "
                        "capabilities and contribute directly to departmental goals at ZESA."
                    ),
                    line_manager_email="manager@zesa.co.zw",
                    department=applicant.department,
                    employee_id=applicant.employee_id or "",
                    **fields,
                ),
            )
            if created:
                apps_made += 1
            return app, created

        # DRAFT — Chiedza / Solar & Grid
        get_or_create_app(s0, course_solar, status=ST.DRAFT)

        # SUBMITTED (primary demo student) — Drone Piloting
        app_demo_submitted, _ = get_or_create_app(
            student_demo, course_drone,
            status=ST.SUBMITTED,
            submitted_at=now - timedelta(days=1),
        )
        if not ApplicationStatusHistory.objects.filter(
            application=app_demo_submitted, to_status=ST.SUBMITTED
        ).exists():
            _make_history(app_demo_submitted, ST.DRAFT, ST.SUBMITTED, student_demo, now - timedelta(days=1))

        # SUBMITTED — Takudzwa / Drone Piloting
        app_submitted, _ = get_or_create_app(
            s1, course_drone,
            status=ST.SUBMITTED,
            submitted_at=now - timedelta(days=2),
        )
        if not ApplicationStatusHistory.objects.filter(
            application=app_submitted, to_status=ST.SUBMITTED
        ).exists():
            _make_history(app_submitted, ST.DRAFT, ST.SUBMITTED, s1, now - timedelta(days=2))

        # UNDER_REVIEW — Farai / Technical Skills
        app_review, _ = get_or_create_app(
            s2, course_tech,
            status=ST.UNDER_REVIEW,
            reviewer=reviewer,
            submitted_at=now - timedelta(days=3),
            reviewed_at=now - timedelta(hours=54),
        )
        if not ApplicationStatusHistory.objects.filter(
            application=app_review, to_status=ST.UNDER_REVIEW
        ).exists():
            _make_history(app_review, ST.DRAFT, ST.SUBMITTED, s2, now - timedelta(days=3))
            _make_history(app_review, ST.SUBMITTED, ST.UNDER_REVIEW, reviewer, now - timedelta(hours=54))

        # MORE_INFO_REQUESTED — Nyasha / Leadership
        app_moreinfo, _ = get_or_create_app(
            s3, course_lead,
            status=ST.MORE_INFO_REQUESTED,
            reviewer=reviewer,
            more_info_request="Please attach your line manager approval letter and a brief statement on how this course supports your current role.",
            submitted_at=now - timedelta(days=4),
            reviewed_at=now - timedelta(days=3),
        )
        if not ApplicationStatusHistory.objects.filter(
            application=app_moreinfo, to_status=ST.MORE_INFO_REQUESTED
        ).exists():
            _make_history(app_moreinfo, ST.DRAFT, ST.SUBMITTED, s3, now - timedelta(days=4))
            _make_history(app_moreinfo, ST.SUBMITTED, ST.UNDER_REVIEW, reviewer, now - timedelta(hours=84))
            _make_history(
                app_moreinfo, ST.UNDER_REVIEW, ST.MORE_INFO_REQUESTED, reviewer,
                now - timedelta(days=3),
            )

        # APPROVED — Blessing / Solar & Grid
        app_approved, _ = get_or_create_app(
            s4, course_solar,
            status=ST.APPROVED,
            reviewer=reviewer,
            reviewer_notes="Approved — budget confirmed with line manager.",
            submitted_at=now - timedelta(days=5),
            reviewed_at=now - timedelta(days=1),
            approved_at=now - timedelta(days=1),
        )
        if not ApplicationStatusHistory.objects.filter(
            application=app_approved, to_status=ST.APPROVED
        ).exists():
            _make_history(app_approved, ST.DRAFT, ST.SUBMITTED, s4, now - timedelta(days=5))
            _make_history(app_approved, ST.SUBMITTED, ST.UNDER_REVIEW, reviewer, now - timedelta(hours=108))
            _make_history(app_approved, ST.UNDER_REVIEW, ST.APPROVED, reviewer, now - timedelta(days=1))

        # PAYMENT_PENDING — Simbarashe / Technical Skills
        app_paypend, _ = get_or_create_app(
            s5, course_tech,
            status=ST.PAYMENT_PENDING,
            reviewer=reviewer,
            reviewer_notes="Approved — high-priority skills gap identified by Engineering.",
            submitted_at=now - timedelta(days=6),
            reviewed_at=now - timedelta(days=2),
            approved_at=now - timedelta(days=2),
        )
        if not ApplicationStatusHistory.objects.filter(
            application=app_paypend, to_status=ST.PAYMENT_PENDING
        ).exists():
            _make_history(app_paypend, ST.DRAFT, ST.SUBMITTED, s5, now - timedelta(days=6))
            _make_history(app_paypend, ST.SUBMITTED, ST.UNDER_REVIEW, reviewer, now - timedelta(hours=132))
            _make_history(app_paypend, ST.UNDER_REVIEW, ST.APPROVED, reviewer, now - timedelta(days=2))
            _make_history(app_paypend, ST.APPROVED, ST.PAYMENT_PENDING, None, now - timedelta(hours=36))

        Payment.objects.get_or_create(
            application=app_paypend,
            defaults=dict(
                amount=course_tech.price if course_tech.price else 0.00,
                method=PaymentMethod.PAYNOW,
                status=PaymentStatus.PENDING,
                paynow_reference=f"demo-ref-{app_paypend.id}",
            ),
        )

        # PAYMENT_CONFIRMED — Tendai / Drone Piloting
        app_payconf, _ = get_or_create_app(
            tendai, course_drone,
            status=ST.PAYMENT_CONFIRMED,
            reviewer=reviewer,
            reviewer_notes="Approved — recommended by Generation & Transmission division head.",
            submitted_at=now - timedelta(days=7),
            reviewed_at=now - timedelta(days=3),
            approved_at=now - timedelta(days=3),
        )
        if not ApplicationStatusHistory.objects.filter(
            application=app_payconf, to_status=ST.PAYMENT_CONFIRMED
        ).exists():
            _make_history(app_payconf, ST.DRAFT, ST.SUBMITTED, tendai, now - timedelta(days=7))
            _make_history(app_payconf, ST.SUBMITTED, ST.UNDER_REVIEW, reviewer, now - timedelta(hours=156))
            _make_history(app_payconf, ST.UNDER_REVIEW, ST.APPROVED, reviewer, now - timedelta(days=3))
            _make_history(app_payconf, ST.APPROVED, ST.PAYMENT_PENDING, None, now - timedelta(days=2))
            _make_history(app_payconf, ST.PAYMENT_PENDING, ST.PAYMENT_CONFIRMED, None, now - timedelta(hours=12))

        Payment.objects.get_or_create(
            application=app_payconf,
            defaults=dict(
                amount=250.00,
                method=PaymentMethod.PAYNOW,
                status=PaymentStatus.CONFIRMED,
                paynow_reference="DEMO-TXN-0001",
                confirmed_at=now - timedelta(hours=12),
            ),
        )

        # ENROLLED — Rumbidzai / Leadership & Corporate Development
        app_enrolled, _ = get_or_create_app(
            rumbidzai, course_lead,
            status=ST.ENROLLED,
            reviewer=reviewer,
            reviewer_notes="Approved — nominated by department head for management track.",
            submitted_at=now - timedelta(days=8),
            reviewed_at=now - timedelta(days=4),
            approved_at=now - timedelta(days=4),
            enrolled_at=now - timedelta(hours=2),
        )
        if not ApplicationStatusHistory.objects.filter(
            application=app_enrolled, to_status=ST.ENROLLED
        ).exists():
            _make_history(app_enrolled, ST.DRAFT, ST.SUBMITTED, rumbidzai, now - timedelta(days=8))
            _make_history(app_enrolled, ST.SUBMITTED, ST.UNDER_REVIEW, reviewer, now - timedelta(hours=180))
            _make_history(app_enrolled, ST.UNDER_REVIEW, ST.APPROVED, reviewer, now - timedelta(days=4))
            _make_history(app_enrolled, ST.APPROVED, ST.PAYMENT_PENDING, None, now - timedelta(days=3))
            _make_history(app_enrolled, ST.PAYMENT_PENDING, ST.PAYMENT_CONFIRMED, None, now - timedelta(days=2))
            _make_history(app_enrolled, ST.PAYMENT_CONFIRMED, ST.ENROLLED, None, now - timedelta(hours=2))

        Payment.objects.get_or_create(
            application=app_enrolled,
            defaults=dict(
                amount=180.00,
                method=PaymentMethod.PAYNOW,
                status=PaymentStatus.CONFIRMED,
                paynow_reference="DEMO-TXN-0002",
                confirmed_at=now - timedelta(days=2),
            ),
        )
        Enrollment.objects.get_or_create(
            application=app_enrolled,
            defaults=dict(
                moodle_user_id=9001,
                moodle_course_id=104,
                status=EnrollmentStatus.ENROLLED,
                enrolled_at=now - timedelta(hours=2),
            ),
        )

        # REJECTED — Tinashe / Drone Piloting
        app_rejected, _ = Application.objects.get_or_create(
            applicant=tinashe,
            course=course_drone,
            defaults=dict(
                motivation=(
                    "I am keen to develop drone inspection skills to support the ICT "
                    "department's infrastructure monitoring initiatives."
                ),
                line_manager_email="manager@zesa.co.zw",
                department=tinashe.department,
                employee_id=tinashe.employee_id or "",
                status=ST.REJECTED,
                reviewer=reviewer,
                rejection_reason=(
                    "Course cohort at capacity for this quarter. "
                    "Please reapply in the next intake cycle."
                ),
                submitted_at=now - timedelta(days=5),
                reviewed_at=now - timedelta(days=2),
            ),
        )
        if app_rejected.status == ST.REJECTED:
            if not ApplicationStatusHistory.objects.filter(
                application=app_rejected, to_status=ST.REJECTED
            ).exists():
                _make_history(app_rejected, ST.DRAFT, ST.SUBMITTED, tinashe, now - timedelta(days=5))
                _make_history(app_rejected, ST.SUBMITTED, ST.UNDER_REVIEW, reviewer, now - timedelta(hours=108))
                _make_history(app_rejected, ST.UNDER_REVIEW, ST.REJECTED, reviewer, now - timedelta(days=2))

        total_apps = Application.objects.count()

        # ── 5. Summary ────────────────────────────────────────────────────────

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 62))
        self.stdout.write(self.style.SUCCESS("  Training at ZESA NTC — Demo Seed Complete"))
        self.stdout.write(self.style.SUCCESS("=" * 62))
        self.stdout.write("")
        self.stdout.write(f"  {'Categories:':<22} {CourseCategory.objects.count()} (7 expected)")
        self.stdout.write(f"  {'Courses:':<22} {Course.objects.count()} (56 expected)")
        self.stdout.write(f"  {'Users:':<22} {User.objects.count()}")
        self.stdout.write(f"  {'Applications:':<22} {total_apps} (10 expected)")
        self.stdout.write(f"  {'Payments:':<22} {Payment.objects.count()} (3 expected)")
        self.stdout.write(f"  {'Enrollments:':<22} {Enrollment.objects.count()} (1 expected)")
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("  ── Staff logins ─────────────────────────────────────"))
        self.stdout.write("")
        self.stdout.write(f"  {'admin@zesa.co.zw':<36} Demo1234!  (Admin dashboard)")
        self.stdout.write(f"  {'approver.demo@zesa.co.zw':<36} Demo1234!  (Reviewer queue — PRIMARY)")
        self.stdout.write(f"  {'finance@zesa.co.zw':<36} Demo1234!  (Finance view)")
        self.stdout.write("")
        self.stdout.write(self.style.HTTP_INFO("  ── Student demo flows ───────────────────────────────"))
        self.stdout.write("")
        self.stdout.write(f"  {'student.demo@zesa.co.zw':<36} SUBMITTED    RPA Drone Training")
        self.stdout.write(f"  {s3.email:<36} MORE_INFO    Visual Felt Leadership")
        self.stdout.write(f"  {s5.email:<36} PAY_PENDING  33KV Switching")
        self.stdout.write(f"  {tendai.email:<36} PAY_CONFIRM  RPA Drone Training")
        self.stdout.write(f"  {rumbidzai.email:<36} ENROLLED     Visual Felt Leadership")
        self.stdout.write(f"  {tinashe.email:<36} REJECTED     RPA Drone Training")
        self.stdout.write("")
        self.stdout.write("  All passwords: Demo1234!")
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 62))
        self.stdout.write("")
