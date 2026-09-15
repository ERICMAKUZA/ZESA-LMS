import csv

from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.renderers import BaseRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdmin, IsAdminOrReviewer
from apps.applications.models import Application
from apps.applications.services.qualification import shortlist_ordering

from .models import Report
from .serializers import ReportSerializer


class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all().select_related("generated_by")
    serializer_class = ReportSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ["report_type"]
    search_fields = ["title"]
    ordering_fields = ["generated_at", "title", "report_type"]

    def perform_create(self, serializer):
        serializer.save(generated_by=self.request.user)


class CsvRenderer(BaseRenderer):
    media_type = "text/csv"
    format = "csv"
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data


class ShortlistReportView(APIView):
    permission_classes = [IsAdminOrReviewer]
    renderer_classes = [JSONRenderer, CsvRenderer]

    def get(self, request):
        course_id = request.query_params.get("course")
        if not course_id:
            return Response({"course": "Select a course."}, status=status.HTTP_400_BAD_REQUEST)

        applications = shortlist_ordering(
            Application.objects.filter(course_id=course_id)
        )
        if request.query_params.get("format") == "csv":
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="course-shortlist.csv"'
            writer = csv.writer(response)
            writer.writerow(["Course", "Surname", "Name", "Points"])
            for application in applications:
                assessment = getattr(application, "qualification_assessment", None)
                writer.writerow([
                    application.course.fullname,
                    application.applicant.last_name,
                    application.applicant.first_name,
                    assessment.total_o_level_points if assessment else 0,
                ])
            return response

        return Response({
            "course": int(course_id),
            "results": [
                {
                    "application_id": str(application.id),
                    "surname": application.applicant.last_name,
                    "name": application.applicant.first_name,
                    "points": application.qualification_assessment.total_o_level_points,
                    "eligibility": application.qualification_assessment.assessment_summary,
                    "has_a_level_sciences": application.qualification_assessment.has_a_level_sciences,
                    "failed_rule_codes": application.qualification_assessment.failed_rule_codes,
                    "has_override": application.qualification_overrides.exists(),
                }
                for application in applications
            ],
        })
