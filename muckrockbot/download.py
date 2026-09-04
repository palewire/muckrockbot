import json
import os
import typing
from datetime import datetime
from pathlib import Path

import click
import pytz
from muckrock import MuckRock
from rich import print

THIS_DIR = Path(__file__).parent.absolute()
DATA_DIR = THIS_DIR.parent / "data"


@click.command()
def cli():
    """Download requests from the MuckRock API."""
    # Create it, if it doesn't already exist
    DATA_DIR.mkdir(exist_ok=True)

    # Create the MuckRock client
    client = MuckRock(
        os.environ["MUCKROCK_USERNAME"],
        os.environ["MUCKROCK_PASSWORD"],
    )

    # Pull the submitted
    submitted_list = client.requests.list(ordering="-datetime_submitted", page_size=100)

    # Pull the completed
    completed_list = client.requests.list(
        ordering="-datetime_done", page_size=100, status="done"
    )

    # Get the current time
    tz = pytz.timezone("America/Los_Angeles")
    now = datetime.now(tz=tz)

    # Write them out
    submitted_data = serialize_requests(submitted_list.results)
    completed_data = serialize_requests(completed_list.results)
    write_json(submitted_data, DATA_DIR / "submitted" / f"{now}.json")
    write_json(submitted_data, DATA_DIR / "submitted" / "latest.json")
    write_json(completed_data, DATA_DIR / "completed" / f"{now}.json")
    write_json(completed_data, DATA_DIR / "completed" / "latest.json")


def serialize_requests(requests: typing.Iterable[typing.Any]) -> typing.List[dict]:
    """Convert API v2 request objects into JSON-compatible dictionaries."""
    data = []
    for request in requests:
        request_data = {
            key: value
            for key, value in vars(request).items()
            if not key.startswith("_")
        }
        request_data["absolute_url"] = (
            f"https://www.muckrock.com/foi/request/{request.id}/"
        )
        data.append(request_data)
    return data


def write_json(data: typing.Any, path: Path, indent: int = 2):
    """Write JSON data to the provided path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    print(f"📥 Writing JSON to {path}")
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)


if __name__ == "__main__":
    cli()
