import django_filters

from .models import Application, ApplicationStatus


class ApplicationFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=ApplicationStatus.choices)
    submitted_after = django_filters.DateFilter(field_name="submitted_at", lookup_expr="date__gte")
    submitted_before = django_filters.DateFilter(field_name="submitted_at", lookup_expr="date__lte")
    applicant_email = django_filters.CharFilter(field_name="applicant__email", lookup_expr="icontains")
    escalated = django_filters.BooleanFilter(field_name="escalated")

    class Meta:
        model = Application
        fields = {
            "status": ["exact"],
            "course": ["exact"],
            "reviewer": ["exact"],
        }
