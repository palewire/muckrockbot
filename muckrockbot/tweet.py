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
def cli() -> None:
    """Post the latest request additions to Twitter.

    Args:
        None.

    Returns:
        None. Each addition is posted to the configured Twitter account.

    Example:
        Run ``python -m muckrockbot.tweet``.
    """
    with (DATA_DIR / "additions.json").open(encoding="utf-8") as file:
        data = json.load(file)
    print(f"Tweeting {len(data)} requests")
    api = twitter.Api(
        consumer_key=os.getenv("TWITTER_CONSUMER_KEY"),
        consumer_secret=os.getenv("TWITTER_CONSUMER_SECRET"),
        access_token_key=os.getenv("TWITTER_ACCESS_TOKEN_KEY"),
        access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    )
    for obj in data:
        text = f"""{obj["title"]} by {obj["username"]} \n\n {obj["absolute_url"]}"""
        api.PostUpdate(text)
        time.sleep(5)


if __name__ == "__main__":
    cli()
