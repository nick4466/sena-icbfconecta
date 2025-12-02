from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "level", "created_at", "read")
    list_filter = ("level", "read")
    search_fields = ("title", "message")
