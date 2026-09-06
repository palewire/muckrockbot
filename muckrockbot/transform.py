import json
from pathlib import Path

import click
from dateutil.parser import parse as dateparse
from rich import print

THIS_DIR = Path(__file__).parent.absolute()
DATA_DIR = THIS_DIR.parent / "data" / "submitted"


@click.command()
def cli() -> None:
    """Compare submitted snapshots and save newly added requests.

    Args:
        None.

    Returns:
        None. New requests are written to ``additions.json``.

    Example:
        Run ``python -m muckrockbot.transform``.
    """
    # Pluck out the last two scrapes for comparison
    json_list = _get_sorted_json_list(DATA_DIR)
    if len(json_list) < 2:
        raise click.ClickException("At least two submitted snapshots are required.")
    latest_json = json_list[0]
    previous_json = json_list[1]
    with latest_json.open(encoding="utf-8") as latest_file:
        latest_data = json.load(latest_file)
    with previous_json.open(encoding="utf-8") as previous_file:
        previous_data = json.load(previous_file)
    print(f"🕵️ Comparing {latest_json.stem}.json against {previous_json.stem}.json")

    # Find the new filing ids that are not in the previous file
    previous_filing_ids = [d["id"] for d in previous_data]
    new_data = []
    for d in latest_data:
        if d["id"] not in previous_filing_ids:
            new_data.append(d)
    print(f"🆕 {len(new_data)} new filings found")

    # Write out to a JSON
    new_path = DATA_DIR / "additions.json"
    print(f"✏️ Writing to {new_path}")
    with open(new_path, "w") as fp:
        json.dump(new_data, fp, indent=2)

    # Trim the file list so it doesn't get super long
    can_go = json_list[24:]
    print(f"🗑️ Deleting {len(can_go)} old scrapes")
    for p in can_go:
        p.unlink()


def _get_sorted_json_list(data_dir: Path = DATA_DIR) -> list[Path]:
    """Return timestamped JSON snapshots in reverse chronological order.

    Args:
        data_dir: Directory containing submitted-request snapshots.

    Returns:
        Timestamped JSON file paths ordered newest first. ``latest.json`` and
        ``additions.json`` are excluded.

    Example:
        ``_get_sorted_json_list(Path("data/submitted"))``.
    """
    # Get all the JSON files
    json_list = list(data_dir.glob("*.json"))

    # Parse them
    json_tuples = []
    for j in json_list:
        if j.stem == "additions" or j.stem == "latest":
            continue
        json_tuples.append((dateparse(j.stem), j))

    # Sort them
    sorted_json = sorted(json_tuples, key=lambda x: x[0], reverse=True)

    # Return the path objects
    return [t[1] for t in sorted_json]


if __name__ == "__main__":
    cli()
