import json
import typing
from datetime import datetime
from pathlib import Path

import click
import pytz
from muckrock import MuckRock
from rich import print


@click.command()
def cli():
    """Download requests from the MuckRock API."""
    # Set the download directory
    this_dir = Path(__file__).parent.absolute()
    data_dir = this_dir.parent / "data"

    # Create it, if it doesn't already exist
    data_dir.mkdir(exist_ok=True)

    # Create the MuckRock client
    client = MuckRock()

    # Pull the submitted
    submitted_list = client.foia.filter(
        ordering="-datetime_submitted", has_datetime_submitted=True
    )

    # Pull the completed
    completed_list = client.foia.filter(
        ordering="-datetime_done", has_datetime_done=True, status="done"
    )

    # Get the current time
    tz = pytz.timezone("America/Los_Angeles")
    now = datetime.now(tz=tz)

    # Write them out
    write_json(submitted_list, data_dir / "submitted" / f"{now}.json")
    write_json(submitted_list, data_dir / "submitted" / "latest.json")
    write_json(completed_list, data_dir / "completed" / f"{now}.json")
    write_json(completed_list, data_dir / "completed" / "latest.json")


def write_json(data: typing.Any, path: Path, indent: int = 2):
    """Write JSON data to the provided path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    print(f"📥 Writing JSON to {path}")
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)


if __name__ == "__main__":
    cli()
