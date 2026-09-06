import json

from click.testing import CliRunner

from muckrockbot import download, transform


def test_download_cli(tmp_path, monkeypatch):
    """Write submitted and completed snapshots without calling MuckRock.

    Args:
        tmp_path: Temporary directory supplied by pytest.
        monkeypatch: Pytest helper for replacing dependencies.

    Returns:
        None. Assertions confirm both latest snapshot files were written.

    Example:
        Run with ``pytest tests/test_cli.py::test_download_cli``.
    """
    submitted_requests = [{"id": 1, "title": "Submitted request"}]
    completed_requests = [{"id": 2, "title": "Completed request"}]

    class FakeFoia:
        """Return fixture data for the legacy endpoint calls."""

        def filter(self, **kwargs: object) -> list[dict[str, int | str]]:
            """Return fixture data matching the requested sort field.

            Args:
                **kwargs: Endpoint query options, including ``ordering``.

            Returns:
                Fixture requests for the requested sort order.

            Example:
                ``FakeFoia().filter(ordering="-datetime_submitted")``.
            """
            if kwargs["ordering"] == "-datetime_submitted":
                return submitted_requests
            return completed_requests

    class FakeMuckRock:
        """Provide the endpoint object expected by the download command."""

        foia = FakeFoia()

    monkeypatch.setattr(download, "DATA_DIR", tmp_path)
    monkeypatch.setattr(download, "MuckRock", FakeMuckRock)

    runner = CliRunner()
    result = runner.invoke(download.cli, [])

    assert result.exit_code == 0
    assert (
        json.loads((tmp_path / "submitted" / "latest.json").read_text())
        == submitted_requests
    )
    assert (
        json.loads((tmp_path / "completed" / "latest.json").read_text())
        == completed_requests
    )


def test_transform_cli(tmp_path, monkeypatch):
    """Write only requests that are missing from the previous snapshot.

    Args:
        tmp_path: Temporary directory supplied by pytest.
        monkeypatch: Pytest helper for replacing module data paths.

    Returns:
        None. Assertions confirm only the new request is saved.

    Example:
        Run with ``pytest tests/test_cli.py::test_transform_cli``.
    """
    data_dir = tmp_path / "submitted"
    data_dir.mkdir()
    (data_dir / "2025-01-01T00:00:00+00:00.json").write_text('[{"id": 1}]')
    (data_dir / "2025-01-02T00:00:00+00:00.json").write_text('[{"id": 1}, {"id": 2}]')
    monkeypatch.setattr(transform, "DATA_DIR", data_dir)

    runner = CliRunner()
    result = runner.invoke(transform.cli, [])

    assert result.exit_code == 0
    assert json.loads((data_dir / "additions.json").read_text()) == [{"id": 2}]
