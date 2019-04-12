# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import twitter
from django.db import models
from django.conf import settings
from muckrockbot import managers


class Request(models.Model):
    """
    A FOIA request at MuckRock
    """
    muckrock_id = models.IntegerField()
    title = models.CharField(max_length=2000)
    slug = models.CharField(max_length=2000)
    status = models.CharField(max_length=50)
    username = models.CharField(max_length=2000)
    datetime_submitted = models.DateTimeField(null=True)
    datetime_done = models.DateTimeField(null=True)
    absolute_url = models.CharField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_tweet_id = models.CharField(blank=True, default="", max_length=500)
    completed_tweet_id = models.CharField(blank=True, default="", max_length=500)
    # Managers
    objects = models.Manager()
    completed = managers.CompletedManager()
    submitted = managers.SubmittedManager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return self.absolute_url

    def submission_tweeted(self):
        if self.submitted_tweet_id:
            return True
        else:
            return False
    submission_tweeted.boolean = True

    def completion_tweeted(self):
        if self.completed_tweet_id:
            return True
        else:
            return False
    completion_tweeted.boolean = True

    @property
    def twitter_url(self):
        return 'https://twitter.com/muckrockbot/status/{}/'.format(self.tweet_id)

    @property
    def tweet_text(self):
        return '"{}" by {}'.format(
            self.title,
            self.username
        )

    def post_submission(self):
        if self.submitted_tweet_id:
            return False
        self.submitted_tweet_id = self.post("Submitted")
        self.save()

    def post_completion(self):
        if self.completed_tweet_id:
            return False
        self.completed_tweet_id = self.post("Completed")
        self.save()

    def post(self, prefix):
        api = twitter.Api(
            consumer_key=settings.TWITTER_CONSUMER_KEY,
            consumer_secret=settings.TWITTER_CONSUMER_SECRET,
            access_token_key=settings.TWITTER_ACCESS_TOKEN_KEY,
            access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET
        )
        status = api.PostUpdate(prefix + ": " + self.tweet_text + "\n\n" + self.get_absolute_url())
        return status.id
