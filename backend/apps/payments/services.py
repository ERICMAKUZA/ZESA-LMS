import hashlib
import logging
import urllib.parse

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class PaynowService:
    INITIATE_URL = "https://www.paynow.co.zw/interface/initiatetransaction/"

    def __init__(self):
        self.integration_id = settings.PAYNOW_INTEGRATION_ID
        self.integration_key = settings.PAYNOW_INTEGRATION_KEY
        self.return_url = settings.PAYNOW_RETURN_URL
        self.result_url = settings.PAYNOW_RESULT_URL

    def _generate_hash(self, values: list) -> str:
        raw = "".join(str(v) for v in values) + self.integration_key
        return hashlib.sha512(raw.encode("utf-8")).hexdigest().upper()

    def _parse_response(self, text: str) -> dict:
        result = {}
        for line in text.strip().splitlines():
            if "=" in line:
                key, _, value = line.partition("=")
                result[key.strip()] = urllib.parse.unquote_plus(value.strip())
        return result

    def initiate_payment(self, payment, email: str) -> dict:
        from .models import Payment  # noqa: avoid circular import at module level

        if settings.DEMO_MODE:
            logger.info("[DEMO MODE] Skipping real Paynow call for payment %s", payment.id)
            reference = str(payment.id)
            return {
                "success": True,
                "redirect_url": f"/applications/{payment.application_id}",
                "poll_url": f"demo-poll-{payment.id}",
                "error": None,
            }

        fields = {
            "id": self.integration_id,
            "reference": str(payment.id),
            "amount": f"{payment.amount:.2f}",
            "additionalinfo": payment.application.course.fullname[:100],
            "returnurl": self.return_url,
            "resulturl": self.result_url,
            "status": "Message",
        }
        fields["hash"] = self._generate_hash(list(fields.values()))

        try:
            response = requests.post(self.INITIATE_URL, data=fields, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.error("Paynow initiate_payment request failed: %s", exc)
            return {"success": False, "error": str(exc)}

        parsed = self._parse_response(response.text)
        if parsed.get("status", "").lower() == "ok":
            return {
                "success": True,
                "redirect_url": parsed.get("redirecturl", ""),
                "poll_url": parsed.get("pollurl", ""),
            }
        return {
            "success": False,
            "error": parsed.get("error", "Unknown error from Paynow"),
        }

    def check_payment_status(self, poll_url: str) -> dict:
        try:
            response = requests.get(poll_url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.error("Paynow check_payment_status failed: %s", exc)
            return {"paid": False, "error": str(exc)}

        parsed = self._parse_response(response.text)
        status = parsed.get("status", "")
        paid = status in ("Paid", "Awaiting Delivery")
        return {
            "status": status,
            "paid": paid,
            "amount": parsed.get("amount"),
            "reference": parsed.get("reference"),
        }

    def verify_webhook(self, post_data: dict) -> bool:
        received_hash = post_data.get("hash", "")
        values = [v for k, v in post_data.items() if k.lower() != "hash"]
        expected_hash = self._generate_hash(values)
        return received_hash.upper() == expected_hash


class SAPService:
    def __init__(self):
        self.base_url = settings.SAP_BASE_URL.rstrip("/")
        self.username = settings.SAP_USERNAME
        self.password = settings.SAP_PASSWORD
        self.training_entity = getattr(settings, "SAP_TRAINING_ENTITY", "ZESATraining")

    def get_training_payments(self, date_from: str, date_to: str) -> list:
        url = f"{self.base_url}/{self.training_entity}/TrainingPaymentSet"
        params = {
            "$filter": f"PaymentDate ge datetime'{date_from}T00:00:00' and PaymentDate le datetime'{date_to}T23:59:59'",
            "$format": "json",
        }
        try:
            response = requests.get(
                url,
                params=params,
                auth=(self.username, self.password),
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            results = data.get("d", {}).get("results", [])
        except requests.RequestException as exc:
            logger.error("SAP get_training_payments failed: %s", exc)
            return []
        except (ValueError, KeyError) as exc:
            logger.error("SAP response parse error: %s", exc)
            return []

        return [
            {
                "employee_id": r.get("EmployeeID", ""),
                "cost_center": r.get("CostCenter", ""),
                "document_number": r.get("DocumentNumber", ""),
                "amount": r.get("Amount", "0"),
                "course_code": r.get("CourseCode", ""),
                "payment_date": r.get("PaymentDate", ""),
            }
            for r in results
        ]

    def match_application(self, sap_record: dict):
        from apps.applications.models import Application, ApplicationStatus

        try:
            return (
                Application.objects.filter(
                    applicant__employee_id=sap_record["employee_id"],
                    status=ApplicationStatus.APPROVED,
                    course__shortname__icontains=sap_record["course_code"],
                )
                .select_related("applicant", "course")
                .first()
            )
        except Exception as exc:
            logger.error("SAP match_application error: %s", exc)
            return None
