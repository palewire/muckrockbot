from django.db import models


class CompletedManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().exclude(datetime_done=None)

    def tweeted(self):
        return self.get_queryset().exclude(completed_tweet_id='')

    def untweeted(self):
        return self.get_queryset().filter(completed_tweet_id='')


class SubmittedManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().filter(
            datetime_done=None
        ).exclude(datetime_submitted=None)

    def tweeted(self):
        return self.get_queryset().exclude(submitted_tweet_id='')

    def untweeted(self):
        return self.get_queryset().filter(submitted_tweet_id='')
