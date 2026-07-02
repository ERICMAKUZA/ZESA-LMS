from django.contrib import admin
from .models import Centre


@admin.register(Centre)
class CentreAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'is_primary', 'contact_email']
