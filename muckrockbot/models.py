# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import twitter
from django.db import models
from django.conf import settings
from feedreader.models import Entry


class Tweet(models.Model):
    """
    Every tweet by @muckrockbot.
    """
    # The @muckrock action
    entry = models.OneToOneField(Entry, on_delete=models.CASCADE)

    # The @muckrockbot post
    tweet_id = models.CharField(max_length=500, blank=True)

    class Meta:
        pass

    def __str__(self):
        return self.text

    @property
    def twitter_url(self):
        return 'https://twitter.com/muckrockbot/status/{}/'.format(self.id)

    @property
    def prefix(self):
        title = self.entry.feed.title
        if 'submitted' in title.lower():
            return 'Submitted'
        elif 'completed' in title.lower():
            return 'Completed'
        return 'Update'

    @property
    def text(self):
        return '{}: "{}"'.format(self.prefix, self.entry.title)

    def post(self):
        if self.tweet_id:
            return False
        api = twitter.Api(
            consumer_key=settings.TWITTER_CONSUMER_KEY,
            consumer_secret=settings.TWITTER_CONSUMER_SECRET,
            access_token_key=settings.TWITTER_ACCESS_TOKEN_KEY,
            access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET
        )
        status = api.PostUpdate(self.text + "\n\n" + self.entry.link)
        self.tweet_id = status.id
        self.save()
