import time
from feedreader.models import Entry
from muckrockbot.models import Tweet
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Make tweets at @muckrockbot"

    def handle(self, *args, **options):
        entry_list = Entry.objects.all()[:50]
        for entry in entry_list:
            tweet, created = Tweet.objects.get_or_create(entry=entry)
            if created:
                print("Created tweet record for {}".format(entry))
            if not tweet.tweet_id:
                print("Tweeting {}".format(tweet))
                tweet.post()
                time.sleep(3)
