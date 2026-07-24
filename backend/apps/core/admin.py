from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        "timestamp", "actor_email", "actor_ec_number",
        "action", "model_name", "object_repr", "field_name",
        "old_value", "new_value", "ip_address",
    ]
    list_filter = ["action", "model_name", "timestamp"]
    search_fields = ["actor_email", "actor_ec_number", "object_repr", "notes"]
    ordering = ["-timestamp"]
    readonly_fields = [f.name for f in AuditLog._meta.get_fields()]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
