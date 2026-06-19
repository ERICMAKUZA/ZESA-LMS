import logging

from django.conf import settings
from django.http import HttpResponse
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdmin
from apps.applications.models import Application, ApplicationStatus

from .models import Payment, PaymentMethod, PaymentStatus
from .serializers import InitiatePaymentSerializer, PaymentSerializer
from .services import PaynowService

logger = logging.getLogger(__name__)


class InitiatePaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, application_id):
        serializer = InitiatePaymentSerializer(
            data={"application_id": application_id},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        application = Application.objects.select_related("course").get(
            id=application_id,
            applicant=request.user,
        )

        payment = Payment.objects.create(
            application=application,
            amount=application.course.price,
            method=PaymentMethod.PAYNOW,
        )

        svc = PaynowService()
        result = svc.initiate_payment(payment, request.user.email)

        if not result["success"]:
            payment.fail(result.get("error", "Paynow initiation failed"))
            return Response(
                {"detail": result.get("error", "Payment initiation failed.")},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        payment.paynow_poll_url = result["poll_url"]
        payment.paynow_redirect_url = result["redirect_url"]
        payment.paynow_reference = str(payment.id)
        payment.status = PaymentStatus.PROCESSING
        payment.save(update_fields=["paynow_poll_url", "paynow_redirect_url", "paynow_reference", "status"])

        application.mark_payment_pending()

        return Response(
            {"redirect_url": result["redirect_url"], "payment_id": str(payment.id)},
            status=status.HTTP_201_CREATED,
        )


class PaynowWebhookView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        post_data = request.POST.dict()
        svc = PaynowService()

        if not svc.verify_webhook(post_data):
            logger.warning("Paynow webhook: invalid hash from %s", request.META.get("REMOTE_ADDR"))
            return Response({"detail": "Invalid hash."}, status=status.HTTP_400_BAD_REQUEST)

        reference = post_data.get("reference", "")
        try:
            payment = Payment.objects.get(paynow_reference=reference)
        except Payment.DoesNotExist:
            logger.error("Paynow webhook: payment not found for reference %s", reference)
            return HttpResponse("OK")

        payment.raw_webhook_payload = post_data
        payment.save(update_fields=["raw_webhook_payload"])

        paynow_status = post_data.get("status", "")
        if paynow_status in ("Paid", "Awaiting Delivery"):
            from .tasks import process_confirmed_payment
            process_confirmed_payment.delay(str(payment.id))

        return HttpResponse("OK")


class PaymentStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, payment_id):
        try:
            payment = Payment.objects.select_related("application__course").get(id=payment_id)
        except Payment.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        if (
            payment.application.applicant != request.user
            and request.user.role not in ("ADMIN", "SUPERADMIN", "FINANCE")
        ):
            return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

        return Response(PaymentSerializer(payment).data)


class DemoConfirmPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, payment_id):
        if not settings.DEMO_MODE:
            return Response({"detail": "Demo mode is disabled."}, status=status.HTTP_403_FORBIDDEN)

        try:
            payment = Payment.objects.select_related(
                "application__applicant", "application__course"
            ).get(id=payment_id)
        except Payment.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        if payment.application.applicant != request.user:
            return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

        if payment.status not in (PaymentStatus.PENDING, PaymentStatus.PROCESSING):
            return Response(
                {"detail": "Payment already processed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment.confirm()

        try:
            from apps.enrollments.tasks import enroll_student_in_moodle
            enroll_student_in_moodle.apply(args=[str(payment.application_id)])
        except Exception as exc:
            logger.warning(
                "DemoConfirmPayment: enrollment failed for application %s: %s",
                payment.application_id, exc,
            )

        payment.refresh_from_db()
        payment.application.refresh_from_db()

        response_data = {
            "application_status": payment.application.status,
            "payment_status": payment.status,
            "enrollment_status": None,
            "moodle_course_url": None,
        }
        try:
            enrollment = payment.application.enrollment
            response_data["enrollment_status"] = enrollment.status
            response_data["moodle_course_url"] = enrollment.moodle_course_url
        except Exception:
            pass

        return Response(response_data)


class SAPSyncView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        from .tasks import sync_sap_payments
        task = sync_sap_payments.delay()
        return Response({"message": "SAP sync started", "task_id": task.id})
