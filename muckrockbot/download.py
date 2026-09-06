import json
import os
from datetime import datetime
from pathlib import Path

import click
import pytz
from rich import print

from muckrockbot.client import DownloadError, PublicFoiaClient, RequestRecord

DATA_DIR = Path(__file__).parent.parent / "data"


@click.command()
@click.option(
    "--check", is_flag=True, help="Check authenticated downloads without writing files."
)
@click.option(
    "--allow-public-feed",
    is_flag=True,
    envvar="MUCKROCK_PUBLIC_FEED_APPROVED",
    help="Allow saving public requests, including records excluded from anonymous feeds.",
)
@click.option(
    "--data-dir",
    type=click.Path(file_okay=False, path_type=Path),
    help="Snapshot directory. Defaults to the project's data directory.",
)
def cli(check: bool, allow_public_feed: bool, data_dir: Path | None) -> None:
    """Download request snapshots from the MuckRock API.

    \f
    Args:
        check: Validate downloads without writing snapshots.
        allow_public_feed: Acknowledge the authenticated feed's visibility difference.
        data_dir: Snapshot directory, or None to use the project's data directory.

    Returns:
        None. Validated snapshots are written unless check is selected.

    Raises:
        click.ClickException: Approval, authentication, or download validation fails.

    Example:
        Run ``python -m muckrockbot.download --check``.
    """
    if not check and not allow_public_feed:
        raise click.ClickException(
            "Saving the authenticated public feed requires approval because it may "
            "include requests excluded from anonymous feeds. Use --check first; "
            "set MUCKROCK_PUBLIC_FEED_APPROVED=true only after approving that change."
        )
    try:
        client = PublicFoiaClient(os.environ.get("MUCKROCK_API_TOKEN", ""))
        submitted_list = client.submitted()
        completed_list = client.completed()
    except DownloadError as error:
        raise click.ClickException(str(error)) from error

    if check:
        click.echo(
            f"Checked {len(submitted_list)} submitted and {len(completed_list)} "
            "completed public requests. No files were written or posts sent. "
            "The API does not identify records excluded from anonymous feeds."
        )
        return

    # Get the current time
    tz = pytz.timezone("America/Los_Angeles")
    now = datetime.now(tz=tz)
    output_dir = data_dir if data_dir is not None else DATA_DIR

    # Write them out
    write_json(submitted_list, output_dir / "submitted" / f"{now}.json")
    write_json(submitted_list, output_dir / "submitted" / "latest.json")
    write_json(completed_list, output_dir / "completed" / f"{now}.json")
    write_json(completed_list, output_dir / "completed" / "latest.json")


def write_json(data: list[RequestRecord], path: Path, indent: int = 2) -> None:
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
