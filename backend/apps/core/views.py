from rest_framework import generics

from apps.accounts.permissions import IsAdmin

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogListView(generics.ListAPIView):
    """
    GET /api/audit/
    Admin only. Optional filters: ?model=Certificate&object_id=<pk>&actor=<email>
    """
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = AuditLog.objects.all()
        model = self.request.query_params.get("model")
        object_id = self.request.query_params.get("object_id")
        actor = self.request.query_params.get("actor")
        if model:
            qs = qs.filter(model_name=model)
        if object_id:
            qs = qs.filter(object_id=object_id)
        if actor:
            qs = qs.filter(actor_email__icontains=actor)
        return qs
