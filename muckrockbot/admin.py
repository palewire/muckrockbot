from django.contrib import admin
from muckrockbot.models import Tweet, Request


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ("muckrock_id", "username", "title", "status", "datetime_submitted", "datetime_done")
    list_filter = ("status",)
    search_fields = ["username", "title", "slug"]


@admin.register(Tweet)
class TweetAdmin(admin.ModelAdmin):
    list_display = ("entry", "text", "tweet_id")
