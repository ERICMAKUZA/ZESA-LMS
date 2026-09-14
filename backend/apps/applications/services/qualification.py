from django.db.models import F

from apps.applications.models import ApplicationQualificationAssessment


SCIENCE_SUBJECTS = {
    "BIOLOGY",
    "CHEMISTRY",
    "INTEGRATED SCIENCE",
    "PHYSICS",
    "SCIENCE",
}


def normalise_subject(subject):
    return " ".join(subject.upper().split())


def _best_results(results):
    best = {}
    for result in results:
        key = normalise_subject(result.subject)
        current = best.get(key)
        if current is None or (result.rank_snapshot or 0, result.points_snapshot or 0) > (
            current.rank_snapshot or 0,
            current.points_snapshot or 0,
        ):
            best[key] = result
    return best


def _profile_for(course):
    if course.qualification_profile_id:
        return course.qualification_profile
    if course.course_type_id:
        return course.course_type.default_qualification_profile
    return None


def assess_application(application):
    """Persist the current, fully auditable eligibility result for an application."""
    course = application.course
    profile = _profile_for(course)
    requires_assessment = course.uses_qualification_assessment

    if not requires_assessment:
        return ApplicationQualificationAssessment.objects.update_or_create(
            application=application,
            defaults={
                "qualifies": True,
                "total_o_level_points": 0,
                "has_a_level_sciences": False,
                "failed_rule_codes": [],
                "assessment_summary": "Meets requirements",
                "configuration_snapshot": {"assessment_required": False},
            },
        )[0]

    if not profile:
        return ApplicationQualificationAssessment.objects.update_or_create(
            application=application,
            defaults={
                "qualifies": False,
                "total_o_level_points": 0,
                "has_a_level_sciences": False,
                "failed_rule_codes": ["QUALIFICATION_PROFILE_REQUIRED"],
                "assessment_summary": "Does not fully meet requirements",
                "configuration_snapshot": {"assessment_required": True, "profile": None},
            },
        )[0]

    sittings = list(application.academic_sittings.prefetch_related("results__grade_band"))
    o_level_sittings = [sitting for sitting in sittings if sitting.education_level == "O_LEVEL"]
    o_level_results = [result for sitting in o_level_sittings for result in sitting.results.all()]
    a_level_results = [
        result
        for sitting in sittings
        if sitting.education_level == "A_LEVEL"
        for result in sitting.results.all()
    ]
    best_o_level = _best_results(o_level_results)
    failed_rule_codes = []

    if len(o_level_sittings) > profile.max_o_level_sittings:
        failed_rule_codes.append("O_LEVEL_SITTINGS")

    requirements = list(profile.requirements.select_related("minimum_grade_band"))
    for requirement in requirements:
        if not requirement.is_required:
            continue
        source = best_o_level if requirement.education_level == "O_LEVEL" else _best_results(a_level_results)
        allowed_subjects = {normalise_subject(subject) for subject in requirement.subject_group}
        matches = [source[subject] for subject in allowed_subjects if subject in source]
        if not matches or max(result.rank_snapshot or 0 for result in matches) < requirement.minimum_grade_band.rank:
            failed_rule_codes.append(f"REQUIRED_SUBJECT:{normalise_subject(requirement.subject_group[0])}")

    all_subjects = set(best_o_level) | set(_best_results(a_level_results))
    for subject in course.required_subjects or []:
        if normalise_subject(subject) not in all_subjects:
            failed_rule_codes.append(f"COURSE_REQUIRED_SUBJECT:{normalise_subject(subject)}")

    total_points = sum(result.points_snapshot or 0 for result in best_o_level.values())
    minimum_points = (
        course.minimum_points_required
        if course.minimum_points_required is not None
        else profile.minimum_total_points
    )
    if total_points < minimum_points:
        failed_rule_codes.append("MINIMUM_POINTS")

    has_a_level_sciences = any(
        normalise_subject(result.subject) in SCIENCE_SUBJECTS for result in a_level_results
    )
    snapshot = {
        "assessment_required": True,
        "profile": {
            "id": profile.id,
            "code": profile.code,
            "max_o_level_sittings": profile.max_o_level_sittings,
            "minimum_total_points": minimum_points,
            "prefer_a_level_sciences": profile.prefer_a_level_sciences,
        },
        "requirements": [
            {
                "education_level": requirement.education_level,
                "subject_group": requirement.subject_group,
                "minimum_grade_band": requirement.minimum_grade_band.label,
                "minimum_rank": requirement.minimum_grade_band.rank,
                "is_required": requirement.is_required,
            }
            for requirement in requirements
        ],
        "course_required_subjects": course.required_subjects or [],
    }
    qualifies = not failed_rule_codes
    return ApplicationQualificationAssessment.objects.update_or_create(
        application=application,
        defaults={
            "qualifies": qualifies,
            "total_o_level_points": total_points,
            "has_a_level_sciences": has_a_level_sciences,
            "failed_rule_codes": failed_rule_codes,
            "assessment_summary": "Meets requirements" if qualifies else "Does not fully meet requirements",
            "configuration_snapshot": snapshot,
        },
    )[0]


def shortlist_ordering(queryset):
    return queryset.select_related(
        "applicant", "qualification_assessment"
    ).order_by(
        F("qualification_assessment__has_a_level_sciences").desc(nulls_last=True),
        F("qualification_assessment__total_o_level_points").desc(nulls_last=True),
        "applicant__last_name",
        "applicant__first_name",
    )
