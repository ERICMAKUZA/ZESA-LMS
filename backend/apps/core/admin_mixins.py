class AuditActorAdminMixin:
    """
    Stamps a transient `_audit_actor` on the instance before save/delete so
    apps.core.signals can attribute the change to the staff member acting
    in Django admin. Mix into any ModelAdmin whose model is audited.
    """

    def save_model(self, request, obj, form, change):
        obj._audit_actor = request.user
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        obj._audit_actor = request.user
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj._audit_actor = request.user
            obj.delete()
