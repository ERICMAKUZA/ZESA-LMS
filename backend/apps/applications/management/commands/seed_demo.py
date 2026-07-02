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

        # ── 0. Remove legacy demo courses so new ones take their place ────────
        legacy_shortnames = ["POWERBI-ESS", "SAP-FIN-RPT", "WS-INDUCT", "PM-FUND"]
        Course.objects.filter(shortname__in=legacy_shortnames).delete()
        legacy_cats = ["Data & Analytics", "Enterprise Systems", "HSE"]
        CourseCategory.objects.filter(name__in=legacy_cats).delete()

        # ── 1. Categories ─────────────────────────────────────────────────────

        cat_drone, _ = CourseCategory.objects.get_or_create(
            name="Drone Technology", defaults={"moodle_id": 10}
        )
        cat_renew, _ = CourseCategory.objects.get_or_create(
            name="Renewable Energy", defaults={"moodle_id": 11}
        )
        cat_tech, _ = CourseCategory.objects.get_or_create(
            name="Technical Skills", defaults={"moodle_id": 12}
        )
        cat_lead, _ = CourseCategory.objects.get_or_create(
            name="Leadership", defaults={"moodle_id": 13}
        )

        # ── 2. Courses ────────────────────────────────────────────────────────

        course_drone, _ = Course.objects.get_or_create(
            shortname="DRONE-INSP",
            defaults=dict(
                moodle_course_id=101,
                fullname="Drone Piloting for System Inspection",
                summary=(
                    "Revolutionize energy system inspection and maintenance with cutting-edge "
                    "drone technology training. Learn to plan, execute, and analyze aerial "
                    "inspections of transmission lines, substations, and generation facilities "
                    "in compliance with ZESA operational and safety protocols."
                ),
                category=cat_drone,
                duration_days=7,
                level=Course.LEVEL_BEGINNER,
                price=250.00,
                requires_approval=True,
                is_active=True,
                thumbnail_url=(
                    "https://images.unsplash.com/photo-1473968512647-3e447244af8f"
                    "?auto=format&fit=crop&w=800&q=80"
                ),
            ),
        )

        course_solar, _ = Course.objects.get_or_create(
            shortname="SOLAR-GRID",
            defaults=dict(
                moodle_course_id=102,
                fullname="Solar & Grid Training",
                summary=(
                    "Master renewable energy systems with hands-on training in solar PV, "
                    "grid integration, and maintenance. Covers system sizing, installation "
                    "standards, fault diagnosis, and grid-tie procedures aligned with Zimbabwe's "
                    "renewable energy expansion programme."
                ),
                category=cat_renew,
                duration_days=5,
                level=Course.LEVEL_INTERMEDIATE,
                price=300.00,
                requires_approval=True,
                is_active=True,
                thumbnail_url=(
                    "https://images.unsplash.com/photo-1509391366360-2e959784a276"
                    "?auto=format&fit=crop&w=800&q=80"
                ),
            ),
        )

        course_tech, _ = Course.objects.get_or_create(
            shortname="TECH-SKILLS",
            defaults=dict(
                moodle_course_id=103,
                fullname="Hands-On Technical Skills",
                summary=(
                    "Gain practical, industry-leading skills required in the power sector "
                    "with hands-on training and certification. Topics include electrical "
                    "installation, switchgear operation, transformer maintenance, and "
                    "fault-finding techniques used across ZESA's network."
                ),
                category=cat_tech,
                duration_days=10,
                level=Course.LEVEL_ALL,
                price=200.00,
                requires_approval=True,
                is_active=True,
                thumbnail_url=(
                    "https://images.unsplash.com/photo-1581092160562-40aa08e78837"
                    "?auto=format&fit=crop&w=800&q=80"
                ),
            ),
        )

        course_lead, _ = Course.objects.get_or_create(
            shortname="LEAD-CORP",
            defaults=dict(
                moodle_course_id=104,
                fullname="Leadership & Corporate Development",
                summary=(
                    "Elevate your management skills and foster a more efficient, safe, and "
                    "productive work environment. Covers strategic thinking, team development, "
                    "performance management, and corporate governance principles tailored to "
                    "the energy utility sector."
                ),
                category=cat_lead,
                duration_days=5,
                level=Course.LEVEL_INTERMEDIATE,
                price=180.00,
                requires_approval=True,
                is_active=True,
                thumbnail_url=(
                    "https://images.unsplash.com/photo-1556761175-5973dc0f32e7"
                    "?auto=format&fit=crop&w=800&q=80"
                ),
            ),
        )

        course_digital, _ = Course.objects.get_or_create(
            shortname="DIGITECH-NRG",
            defaults=dict(
                moodle_course_id=105,
                fullname="Digital Technologies for Energy",
                summary=(
                    "Embrace modern technology with specialized training in digital solutions "
                    "for the energy sector. Topics include SCADA systems, IoT sensor networks, "
                    "predictive maintenance platforms, and cybersecurity fundamentals for "
                    "operational technology environments."
                ),
                category=cat_renew,
                duration_days=5,
                level=Course.LEVEL_INTERMEDIATE,
                price=220.00,
                requires_approval=True,
                is_active=True,
                thumbnail_url=(
                    "https://images.unsplash.com/photo-1518770660439-4636190af475"
                    "?auto=format&fit=crop&w=800&q=80"
                ),
            ),
        )

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
        self.stdout.write(f"  {'Categories:':<22} {CourseCategory.objects.count()} (4 expected)")
        self.stdout.write(f"  {'Courses:':<22} {Course.objects.count()} (5 expected)")
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
        self.stdout.write(f"  {'student.demo@zesa.co.zw':<36} SUBMITTED    Drone Piloting")
        self.stdout.write(f"  {s3.email:<36} MORE_INFO    Leadership")
        self.stdout.write(f"  {s5.email:<36} PAY_PENDING  Technical Skills")
        self.stdout.write(f"  {tendai.email:<36} PAY_CONFIRM  Drone Piloting")
        self.stdout.write(f"  {rumbidzai.email:<36} ENROLLED     Leadership")
        self.stdout.write(f"  {tinashe.email:<36} REJECTED     Drone Piloting")
        self.stdout.write("")
        self.stdout.write("  All passwords: Demo1234!")
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 62))
        self.stdout.write("")
