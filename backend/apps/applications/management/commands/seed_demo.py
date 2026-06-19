"""
Seed realistic demo data for an interface design session.
Idempotent: safe to run multiple times.
"""
from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone


# ── helpers ───────────────────────────────────────────────────────────────────

def _h(history_obj, backdated):
    """Backdate an ApplicationStatusHistory row (auto_now_add bypasses via UPDATE)."""
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


# ── command ───────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = "Seed demo data for interface design sessions (idempotent)"

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

        # ── 1. Categories & courses ───────────────────────────────────────────

        cat_data, data_analytics = CourseCategory.objects.get_or_create(
            name="Data & Analytics", defaults={"moodle_id": 10}
        )
        cat_ent, _ = CourseCategory.objects.get_or_create(
            name="Enterprise Systems", defaults={"moodle_id": 11}
        )
        cat_hse, _ = CourseCategory.objects.get_or_create(
            name="HSE", defaults={"moodle_id": 12}
        )
        cat_lead, _ = CourseCategory.objects.get_or_create(
            name="Leadership", defaults={"moodle_id": 13}
        )

        course_bi, _ = Course.objects.get_or_create(
            shortname="POWERBI-ESS",
            defaults=dict(
                moodle_course_id=101,
                fullname="Power BI Essentials",
                summary=(
                    "Master data visualisation and self-service analytics using Microsoft Power BI. "
                    "Learn to connect to enterprise data sources, build interactive dashboards, and "
                    "share insights with stakeholders across ZESA's operational divisions."
                ),
                category=cat_data,
                price=150.00,
                requires_approval=True,
                is_active=True,
            ),
        )
        course_sap, _ = Course.objects.get_or_create(
            shortname="SAP-FIN-RPT",
            defaults=dict(
                moodle_course_id=102,
                fullname="SAP Financial Reporting",
                summary=(
                    "Develop practical skills in generating and interpreting financial reports within "
                    "ZESA's SAP ERP environment. Topics include cost-centre reporting, budget variance "
                    "analysis, and period-end closing procedures."
                ),
                category=cat_ent,
                price=200.00,
                requires_approval=True,
                is_active=True,
            ),
        )
        course_safety, _ = Course.objects.get_or_create(
            shortname="WS-INDUCT",
            defaults=dict(
                moodle_course_id=103,
                fullname="Workplace Safety Induction",
                summary=(
                    "A mandatory induction covering ZESA's health, safety, and environment policies. "
                    "Employees will learn hazard identification, incident reporting procedures, and "
                    "emergency response protocols applicable across all ZESA sites."
                ),
                category=cat_hse,
                price=0.00,
                requires_approval=False,
                is_active=True,
            ),
        )
        course_pm, _ = Course.objects.get_or_create(
            shortname="PM-FUND",
            defaults=dict(
                moodle_course_id=104,
                fullname="Project Management Fundamentals",
                summary=(
                    "An introduction to project management principles aligned with PMI's PMBOK framework. "
                    "Participants will apply planning, scheduling, and risk management techniques to "
                    "infrastructure and operational projects typical of the energy sector."
                ),
                category=cat_lead,
                price=180.00,
                requires_approval=True,
                is_active=True,
            ),
        )

        courses_created = sum([
            Course.objects.filter(shortname=s).count()
            for s in ("POWERBI-ESS", "SAP-FIN-RPT", "WS-INDUCT", "PM-FUND")
        ])

        # ── 2. Users ──────────────────────────────────────────────────────────

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
        # Primary demo approver account (used in /api/demo-accounts/ primary list)
        approver_demo = make_user(
            "approver.demo@zesa.co.zw", "Demo", "Reviewer", User.Role.REVIEWER,
            dept="Human Resources",
        )
        make_user(
            "finance@zesa.co.zw", "Prosper", "Ncube", User.Role.FINANCE,
            dept="Finance",
        )

        # Primary demo student account — fresh SUBMITTED state for guided demo flow
        student_demo = make_user(
            "student.demo@zesa.co.zw", "Demo", "Student", User.Role.STUDENT,
            dept="ICT", emp_id="ZESA-DEMO-001",
        )

        student_specs = [
            ("chiedza.mutasa@zesa.co.zw",   "Chiedza",    "Mutasa",    "Generation & Transmission", "ZESA-2024-001"),
            ("takudzwa.ndlovu@zesa.co.zw",  "Takudzwa",   "Ndlovu",    "Distribution",              "ZESA-2024-002"),
            ("farai.chikomba@zesa.co.zw",   "Farai",      "Chikomba",  "ICT",                       "ZESA-2024-003"),
            ("nyasha.mupambi@zesa.co.zw",   "Nyasha",     "Mupambi",   "Finance",                   "ZESA-2024-004"),
            ("blessing.zulu@zesa.co.zw",    "Blessing",   "Zulu",      "HR",                        "ZESA-2024-005"),
            ("simbarashe.dube@zesa.co.zw",  "Simbarashe", "Dube",      "Engineering",               "ZESA-2024-006"),
            # additional students for advanced-state applications
            ("tendai.moyo@zesa.co.zw",      "Tendai",     "Moyo",      "Generation & Transmission", "ZESA-2024-007"),
            ("rumbidzai.chikomo@zesa.co.zw","Rumbidzai",  "Chikomo",   "Distribution",              "ZESA-2024-008"),
            ("tinashe.mhuru@zesa.co.zw",    "Tinashe",    "Mhuru",     "ICT",                       "ZESA-2024-009"),
        ]
        students = [
            make_user(email, first, last, User.Role.STUDENT, dept=dept, emp_id=emp)
            for email, first, last, dept, emp in student_specs
        ]
        (s0, s1, s2, s3, s4, s5, tendai, rumbidzai, tinashe) = students

        users_created = User.objects.count()

        # ── 3. Applications ───────────────────────────────────────────────────

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

        # ── DRAFT ─────────────────────────────────────────────────────────────
        get_or_create_app(s0, course_bi, status=ST.DRAFT)

        # ── SUBMITTED (primary demo student) ──────────────────────────────────
        app_demo_submitted, _ = get_or_create_app(
            student_demo, course_bi,
            status=ST.SUBMITTED,
            submitted_at=now - timedelta(days=1),
        )
        if not ApplicationStatusHistory.objects.filter(
            application=app_demo_submitted, to_status=ST.SUBMITTED
        ).exists():
            _make_history(app_demo_submitted, ST.DRAFT, ST.SUBMITTED, student_demo, now - timedelta(days=1))

        # ── SUBMITTED ─────────────────────────────────────────────────────────
        app_submitted, _ = get_or_create_app(
            s1, course_bi,
            status=ST.SUBMITTED,
            submitted_at=now - timedelta(days=2),
        )
        if not ApplicationStatusHistory.objects.filter(
            application=app_submitted, to_status=ST.SUBMITTED
        ).exists():
            _make_history(app_submitted, ST.DRAFT, ST.SUBMITTED, s1, now - timedelta(days=2))

        # ── UNDER_REVIEW ──────────────────────────────────────────────────────
        app_review, _ = get_or_create_app(
            s2, course_sap,
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

        # ── MORE_INFO_REQUESTED ───────────────────────────────────────────────
        app_moreinfo, _ = get_or_create_app(
            s3, course_sap,
            status=ST.MORE_INFO_REQUESTED,
            reviewer=reviewer,
            more_info_request="Please attach your line manager approval letter.",
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

        # ── APPROVED ──────────────────────────────────────────────────────────
        app_approved, _ = get_or_create_app(
            s4, course_pm,
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
            _make_history(
                app_approved, ST.UNDER_REVIEW, ST.APPROVED, reviewer,
                now - timedelta(days=1),
            )

        # ── PAYMENT_PENDING ───────────────────────────────────────────────────
        app_paypend, _ = get_or_create_app(
            s5, course_safety,
            status=ST.PAYMENT_PENDING,
            reviewer=reviewer,
            reviewer_notes="Approved — mandatory induction.",
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

        # Payment record needed so the demo-confirm endpoint has something to confirm
        Payment.objects.get_or_create(
            application=app_paypend,
            defaults=dict(
                amount=course_safety.price if course_safety.price else 0.00,
                method=PaymentMethod.PAYNOW,
                status=PaymentStatus.PENDING,
                paynow_reference=f"demo-ref-{app_paypend.id}",
            ),
        )

        # ── PAYMENT_CONFIRMED (Tendai Moyo) ───────────────────────────────────
        app_payconf, _ = get_or_create_app(
            tendai, course_bi,
            status=ST.PAYMENT_CONFIRMED,
            reviewer=reviewer,
            reviewer_notes="Approved — strong motivation letter.",
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
                amount=150.00,
                method=PaymentMethod.PAYNOW,
                status=PaymentStatus.CONFIRMED,
                paynow_reference="DEMO-TXN-0001",
                confirmed_at=now - timedelta(hours=12),
            ),
        )

        # ── ENROLLED (Rumbidzai Chikomo) ──────────────────────────────────────
        app_enrolled, _ = get_or_create_app(
            rumbidzai, course_sap,
            status=ST.ENROLLED,
            reviewer=reviewer,
            reviewer_notes="Approved — nominated by department head.",
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
            _make_history(
                app_enrolled, ST.PAYMENT_PENDING, ST.PAYMENT_CONFIRMED, None,
                now - timedelta(days=2),
            )
            _make_history(app_enrolled, ST.PAYMENT_CONFIRMED, ST.ENROLLED, None, now - timedelta(hours=2))

        Payment.objects.get_or_create(
            application=app_enrolled,
            defaults=dict(
                amount=200.00,
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
                moodle_course_id=102,
                status=EnrollmentStatus.ENROLLED,
                enrolled_at=now - timedelta(hours=2),
            ),
        )

        # ── REJECTED (Tinashe Mhuru) ──────────────────────────────────────────
        app_rejected, _ = Application.objects.get_or_create(
            applicant=tinashe,
            course=course_bi,
            defaults=dict(
                motivation=(
                    "I am keen to advance my data analytics skills to better support "
                    "reporting requirements in the ICT department."
                ),
                line_manager_email="manager@zesa.co.zw",
                department=tinashe.department,
                employee_id=tinashe.employee_id or "",
                status=ST.REJECTED,
                reviewer=reviewer,
                rejection_reason=(
                    "Course at capacity for this quarter. "
                    "Please reapply next intake."
                ),
                submitted_at=now - timedelta(days=5),
                reviewed_at=now - timedelta(days=2),
            ),
        )
        if app_rejected.status != ST.REJECTED:
            # Defensive: if somehow already exists with wrong status, skip history
            pass
        else:
            if not ApplicationStatusHistory.objects.filter(
                application=app_rejected, to_status=ST.REJECTED
            ).exists():
                _make_history(app_rejected, ST.DRAFT, ST.SUBMITTED, tinashe, now - timedelta(days=5))
                _make_history(
                    app_rejected, ST.SUBMITTED, ST.UNDER_REVIEW, reviewer,
                    now - timedelta(hours=108),
                )
                _make_history(
                    app_rejected, ST.UNDER_REVIEW, ST.REJECTED, reviewer,
                    now - timedelta(days=2),
                )
            if not app_rejected.pk:
                apps_made += 1

        total_apps = Application.objects.count()

        # ── 4. Summary ────────────────────────────────────────────────────────

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("  ZESA ILMP — Demo Seed Complete"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")
        self.stdout.write(f"  {'Courses:':<20} {Course.objects.count()} (4 expected)")
        self.stdout.write(f"  {'Users:':<20} {User.objects.count()}")
        self.stdout.write(f"  {'Applications:':<20} {total_apps} (10 expected)")
        self.stdout.write(f"  {'Payments:':<20} {Payment.objects.count()} (3 expected)")
        self.stdout.write(f"  {'Enrollments:':<20} {Enrollment.objects.count()} (1 expected)")
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("  ── Login cheat-sheet ──────────────────────────────"))
        self.stdout.write("")
        self.stdout.write(f"  {'admin@zesa.co.zw':<35} Demo1234!  (Admin dashboard)")
        self.stdout.write(f"  {'approver.demo@zesa.co.zw':<35} Demo1234!  (Reviewer queue — PRIMARY)")
        self.stdout.write(f"  {'reviewer@zesa.co.zw':<35} Demo1234!  (Reviewer queue)")
        self.stdout.write(f"  {'finance@zesa.co.zw':<35} Demo1234!  (Finance view)")
        self.stdout.write("")
        self.stdout.write(self.style.HTTP_INFO("  ── Student demo flows ─────────────────────────────"))
        self.stdout.write("")
        self.stdout.write(
            f"  {'student.demo@zesa.co.zw':<35} SUBMITTED   — PRIMARY demo account"
        )
        self.stdout.write(
            f"  {s3.email:<35} MORE_INFO   — resubmit flow"
        )
        self.stdout.write(
            f"  {s5.email:<35} PAY_PENDING — demo-confirm payment flow"
        )
        self.stdout.write(
            f"  {tendai.email:<35} PAY_CONFIRM — payment success screen"
        )
        self.stdout.write(
            f"  {rumbidzai.email:<35} ENROLLED    — enrolled dashboard"
        )
        self.stdout.write(
            f"  {tinashe.email:<35} REJECTED    — rejection screen"
        )
        self.stdout.write("")
        self.stdout.write("  All passwords: Demo1234!")
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")
