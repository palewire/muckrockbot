from django.db import models


class TwitterQuerySet(models.QuerySet):

    def tweeted(self):
        return self.exclude(tweet_id='')

    def untweeted(self):
        return self.filter(tweet_id='')


class CompletedManager(models.Manager):

    def get_queryset(self):
        return TwitterQuerySet(self.model, using=self._db).exclude(
            datetime_done=None
        )

    def tweeted(self):
        return self.get_queryset().tweeted()

    def untweeted(self):
        return self.get_queryset().untweeted()


class SubmittedManager(models.Manager):

    def get_queryset(self):
        return TwitterQuerySet(self.model, using=self._db).filter(
            datetime_done=None
        ).exclude(
            datetime_submitted=None
        )

    def tweeted(self):
        return self.get_queryset().tweeted()

    def untweeted(self):
        return self.get_queryset().untweeted()
