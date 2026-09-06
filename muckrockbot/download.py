import json
import typing
from datetime import datetime
from pathlib import Path

import click
import pytz
from muckrock import MuckRock
from rich import print

DATA_DIR = Path(__file__).parent.parent / "data"


@click.command()
def cli() -> None:
    """Download request snapshots from the MuckRock API.

    Args:
        None.

    Returns:
        None. JSON snapshots are written to the project's data directory.

    Example:
        Run ``python -m muckrockbot.download``.
    """
    DATA_DIR.mkdir(exist_ok=True)

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
    write_json(submitted_list, DATA_DIR / "submitted" / f"{now}.json")
    write_json(submitted_list, DATA_DIR / "submitted" / "latest.json")
    write_json(completed_list, DATA_DIR / "completed" / f"{now}.json")
    write_json(completed_list, DATA_DIR / "completed" / "latest.json")


def write_json(data: typing.Any, path: Path, indent: int = 2) -> None:
    """Write JSON-compatible data to a path.

    Args:
        data: The JSON-compatible value to serialize.
        path: Destination file path.
        indent: Number of spaces used to indent JSON output.

    Returns:
        None. The serialized data is written to ``path``.

    Example:
        ``write_json([{"id": 1}], Path("requests.json"))``.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    print(f"📥 Writing JSON to {path}")
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


if __name__ == "__main__":
    cli()
