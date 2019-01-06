from django.contrib import admin
from muckrockbot.models import Tweet


@admin.register(Tweet)
class TweetAdmin(admin.ModelAdmin):
    list_display = ("entry", "text", "tweet_id")
