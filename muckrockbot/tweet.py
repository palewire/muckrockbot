import click

# import twitter


@click.command()
def cli():
    """Post latest requests to Twitter."""
    pass


#    @property
#    def tweet_text(self):
#        return f'"{self.title}" by {self.username}'

#    def post_submission(self):
#        if self.submitted_tweet_id:
#            return False
#        self.submitted_tweet_id = self.post("Submitted")
#        self.save()

#    def post_completion(self):
#        if self.completed_tweet_id:
#            return False
#        self.completed_tweet_id = self.post("Completed")
#        self.save()

#        api = twitter.Api(
#            consumer_key=settings.TWITTER_CONSUMER_KEY,
#            consumer_secret=settings.TWITTER_CONSUMER_SECRET,
#            access_token_key=settings.TWITTER_ACCESS_TOKEN_KEY,
#            access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
#        )
#        status = api.PostUpdate(
#            prefix + ": " + self.tweet_text + "\n\n" + self.absolute_url
#        )
#        return status.id

if __name__ == "__main__":
    cli()
