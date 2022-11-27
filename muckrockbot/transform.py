import json
import typing
from pathlib import Path

import click
from dateutil.parser import parse as dateparse
from rich import print

THIS_DIR = Path(__file__).parent.absolute()
DATA_DIR = THIS_DIR.parent / "data" / "submitted"


@click.command()
def cli():
    """Integrate files and identify any additions."""
    # Pluck out the last two scrapes for comparison
    json_list = _get_sorted_json_list()
    latest_json = json_list[0]
    previous_json = json_list[1]
    latest_data = json.load(open(latest_json))
    previous_data = json.load(open(previous_json))
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


def _get_sorted_json_list(data_dir: Path = DATA_DIR) -> typing.List[Path]:
    """Return the JSON files from our data directory in reverse chronological order."""
    # Get all the JSON files
    json_list = list(data_dir.glob("*.json"))

    # Parse them
    json_tuples = []
    for j in json_list:
        if j.stem == "additions":
            continue
        elif j.stem == "latest":
            continue
        json_tuples.append((dateparse(j.stem), j))

    # Sort them
    sorted_json = sorted(json_tuples, key=lambda x: x[0], reverse=True)

    # Return the path objects
    return [t[1] for t in sorted_json]


if __name__ == "__main__":
    cli()
