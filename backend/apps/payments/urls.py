from django.urls import path

from .views import InitiatePaymentView, PaymentStatusView, PaynowWebhookView, SAPSyncView

urlpatterns = [
    path("initiate/<uuid:application_id>/", InitiatePaymentView.as_view(), name="payment-initiate"),
    path("paynow/webhook/",                PaynowWebhookView.as_view(),    name="paynow-webhook"),
    path("<uuid:payment_id>/status/",      PaymentStatusView.as_view(),    name="payment-status"),
    path("sap/sync/",                      SAPSyncView.as_view(),          name="sap-sync"),
]
