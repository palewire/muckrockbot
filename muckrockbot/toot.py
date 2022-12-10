import os
import json
import time
from pathlib import Path

import click
from mastodon import Mastodon
from rich import print

THIS_DIR = Path(__file__).parent.absolute()
DATA_DIR = THIS_DIR.parent / "data" / "submitted"


@click.command()
def cli():
    """Post latest requests to Twitter."""
    data = json.load(open(DATA_DIR / "additions.json"))
    print(f"Tooting {len(data)} requests")
    api = Mastodon(
        client_id=os.getenv("MASTODON_CLIENT_KEY"),
        client_secret=os.getenv("MASTODON_CLIENT_SECRET"),
        access_token=os.getenv("MASTODON_ACCESS_TOKEN"),
        api_base_url="https://mastodon.palewi.re",
    )
    for obj in data:
        text = f"""{obj['title']} by {obj['username']} \n\n {obj['absolute_url']}"""
        api.status_post(text)
        time.sleep(2)


if __name__ == "__main__":
    cli()
