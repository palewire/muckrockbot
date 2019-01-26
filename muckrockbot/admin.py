from django.contrib import admin
from muckrockbot.models import Request


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = (
        "muckrock_id",
        "username",
        "title",
        "datetime_submitted",
        "datetime_done",
        "is_tweeted"
    )
    list_filter = ("status",)
    search_fields = ["username", "title", "slug"]
