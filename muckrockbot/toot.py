import json
import os
import time
from pathlib import Path

import click
from mastodon import Mastodon
from rich import print

THIS_DIR = Path(__file__).parent.absolute()
DATA_DIR = THIS_DIR.parent / "data" / "submitted"


@click.command()
def cli() -> None:
    """Post the latest request additions to Mastodon.

    Args:
        None.

    Returns:
        None. Each addition is posted to the configured Mastodon account.

    Example:
        Run ``python -m muckrockbot.toot``.
    """
    with (DATA_DIR / "additions.json").open(encoding="utf-8") as file:
        data = json.load(file)
    print(f"Tooting {len(data)} requests")
    api = Mastodon(
        client_id=os.getenv("MASTODON_CLIENT_KEY"),
        client_secret=os.getenv("MASTODON_CLIENT_SECRET"),
        access_token=os.getenv("MASTODON_ACCESS_TOKEN"),
        api_base_url="https://mastodon.palewi.re",
    )
    for obj in data:
        text = f"""{obj["title"]} by {obj["username"]} \n\n {obj["absolute_url"]}"""
        api.status_post(text)
        time.sleep(2)


if __name__ == "__main__":
    cli()
