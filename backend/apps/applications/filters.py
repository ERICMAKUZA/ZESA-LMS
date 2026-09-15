import django_filters

from .models import Application, ApplicationStatus


class ApplicationFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=ApplicationStatus.choices)
    submitted_after = django_filters.DateFilter(field_name="submitted_at", lookup_expr="date__gte")
    submitted_before = django_filters.DateFilter(field_name="submitted_at", lookup_expr="date__lte")
    applicant_email = django_filters.CharFilter(field_name="applicant__email", lookup_expr="icontains")
    escalated = django_filters.BooleanFilter(field_name="escalated")
    course_type = django_filters.NumberFilter(field_name="course__course_type_id")
    selected_department = django_filters.NumberFilter(field_name="selected_department_id")
    certification_type = django_filters.NumberFilter(field_name="certification_type_id")
    eligibility = django_filters.ChoiceFilter(
        choices=(("MEETS", "Meets requirements"), ("DOES_NOT_MEET", "Does not meet requirements")),
        method="filter_eligibility",
    )

    def filter_eligibility(self, queryset, name, value):
        if value == "MEETS":
            return queryset.filter(qualification_assessment__qualifies=True)
        if value == "DOES_NOT_MEET":
            return queryset.filter(qualification_assessment__qualifies=False)
        return queryset

    class Meta:
        model = Application
        fields = {
            "status": ["exact"],
            "course": ["exact"],
            "reviewer": ["exact"],
        }
