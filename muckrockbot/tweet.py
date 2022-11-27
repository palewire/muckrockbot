import json
import os
import time
from pathlib import Path

import click
import twitter
from rich import print

THIS_DIR = Path(__file__).parent.absolute()
DATA_DIR = THIS_DIR.parent / "data" / "submitted"


@click.command()
def cli():
    """Post latest requests to Twitter."""
    data = json.load(open(DATA_DIR / "additions.json"))
    print(f"Tweeting {len(data)} requests")
    api = twitter.Api(
        consumer_key=os.getenv("TWITTER_CONSUMER_KEY"),
        consumer_secret=os.getenv("TWITTER_CONSUMER_SECRET"),
        access_token_key=os.getenv("TWITTER_ACCESS_TOKEN_KEY"),
        access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    )
    for obj in data:
        text = f"""{obj['title']} by {obj['username']} \n\n {obj['absolute_url']}"""
        api.PostUpdate(text)
        time.sleep(5)


if __name__ == "__main__":
    cli()
