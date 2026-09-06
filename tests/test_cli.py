import json
from datetime import UTC, datetime, tzinfo
from pathlib import Path

import pytest
import requests
from click.testing import CliRunner

from muckrockbot import client, download, transform
from tests.helpers import make_response, request_row


def assert_json_primitives(value: object) -> None:
    """Assert that a decoded value consists only of JSON primitives and containers.

    Args:
        value: Decoded JSON value to validate recursively.

    Returns:
        None. Raises an assertion error when an unsupported value is encountered.

    Example:
        ``assert_json_primitives({"id": 1, "tags": []})``.
    """
    if isinstance(value, dict):
        assert all(isinstance(key, str) for key in value)
        for item in value.values():
            assert_json_primitives(item)
    elif isinstance(value, list):
        for item in value:
            assert_json_primitives(item)
    else:
        assert value is None or type(value) in {bool, int, float, str}


@pytest.mark.parametrize("approval_source", ["flag", "environment"])
def test_download_cli_writes_four_consistent_json_snapshots(
    approval_source: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Write both validated feeds with one frozen timestamp and no private fields.

    Args:
        approval_source: Mechanism used to explicitly approve snapshot writing.
        tmp_path: Temporary directory supplied by pytest.
        monkeypatch: Pytest helper for replacing dependencies.

    Returns:
        None. Assertions confirm all output is JSON-compatible and consistently named.

    Example:
        Run with ``pytest tests/test_cli.py::test_download_cli_writes_four_consistent_json_snapshots``.
    """
    submitted = request_row(
        1,
        agency="Example agency",
        tags=["transparency"],
        notes="private notes",
        email="private@example.com",
        mail_id=9,
        read_collaborators=["staff"],
        edit_collaborators=["staff"],
    )
    completed = request_row(2, completed=True, communications=[])
    responses = [
        make_response({"results": [submitted]}),
        make_response({"results": [completed]}),
    ]

    def queued_get(url: str, **kwargs: object) -> requests.Response:
        """Return the next expected response without performing I/O.

        Args:
            url: Requested endpoint URL.
            **kwargs: Request arguments passed by the client.

        Returns:
            The next queued synthetic response.

        Example:
            ``queued_get("https://www.muckrock.com/api_v1/foia")``.
        """
        assert url == "https://www.muckrock.com/api_v1/foia"
        assert kwargs["timeout"] == 20
        return responses.pop(0)

    class FrozenDatetime(datetime):
        """Provide a stable instant for timestamped snapshot names."""

        @classmethod
        def now(cls, tz: tzinfo | None = None) -> datetime:
            """Return the fixture instant in the requested timezone.

            Args:
                tz: Timezone requested by the download command.

            Returns:
                A stable timezone-aware timestamp.

            Example:
                ``FrozenDatetime.now(UTC)``.
            """
            instant = datetime(2026, 9, 6, 16, 12, tzinfo=UTC)
            return instant if tz is None else instant.astimezone(tz)

    monkeypatch.setenv("MUCKROCK_API_TOKEN", "test-token")
    monkeypatch.setattr(client.requests, "get", queued_get)
    monkeypatch.setattr(download, "datetime", FrozenDatetime)
    command = ["--data-dir", str(tmp_path)]
    if approval_source == "flag":
        command.insert(0, "--allow-public-feed")
    else:
        monkeypatch.setenv("MUCKROCK_PUBLIC_FEED_APPROVED", "true")

    runner = CliRunner()
    result = runner.invoke(download.cli, command)

    assert result.exit_code == 0
    assert responses == []
    submitted_paths = sorted((tmp_path / "submitted").glob("*.json"))
    completed_paths = sorted((tmp_path / "completed").glob("*.json"))
    assert [path.name for path in submitted_paths] == [
        "2026-09-06 09:12:00-07:00.json",
        "latest.json",
    ]
    assert [path.name for path in completed_paths] == [
        "2026-09-06 09:12:00-07:00.json",
        "latest.json",
    ]
    for path in [*submitted_paths, *completed_paths]:
        assert_json_primitives(json.loads(path.read_text()))
    assert json.loads((tmp_path / "submitted" / "latest.json").read_text()) == [
        {
            key: value
            for key, value in submitted.items()
            if key
            not in {
                "notes",
                "email",
                "mail_id",
                "read_collaborators",
                "edit_collaborators",
            }
        }
    ]
    assert json.loads((tmp_path / "completed" / "latest.json").read_text()) == [
        completed
    ]


def test_check_download_does_not_create_the_requested_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Check both feeds without creating directories or snapshot files.

    Args:
        tmp_path: Temporary directory supplied by pytest.
        monkeypatch: Pytest helper for replacing dependencies.

    Returns:
        None. Assertions confirm check mode performs no writes.

    Example:
        Run with ``pytest tests/test_cli.py::test_check_download_does_not_create_the_requested_directory``.
    """
    output_dir = tmp_path / "not-created"
    responses = [make_response({"results": []}), make_response({"results": []})]

    def queued_get(url: str, **kwargs: object) -> requests.Response:
        """Return the next checked feed response.

        Args:
            url: Requested endpoint URL.
            **kwargs: Request arguments passed by the client.

        Returns:
            The next queued synthetic response.

        Example:
            ``queued_get("https://www.muckrock.com/api_v1/foia")``.
        """
        return responses.pop(0)

    monkeypatch.setenv("MUCKROCK_API_TOKEN", "test-token")
    monkeypatch.setattr(client.requests, "get", queued_get)

    result = CliRunner().invoke(
        download.cli, ["--check", "--data-dir", str(output_dir)]
    )

    assert result.exit_code == 0
    assert responses == []
    assert not output_dir.exists()
    assert "No files were written or posts sent" in result.output


def test_failure_after_submitted_preserves_existing_snapshots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Leave all existing snapshots untouched when the completed feed fails.

    Args:
        tmp_path: Temporary directory supplied by pytest.
        monkeypatch: Pytest helper for replacing dependencies.

    Returns:
        None. Assertions confirm no partial snapshot write occurs.

    Example:
        Run with ``pytest tests/test_cli.py::test_failure_after_submitted_preserves_existing_snapshots``.
    """
    original_files = {
        tmp_path / "submitted" / "latest.json": '[{"id": 99}]',
        tmp_path / "completed" / "latest.json": '[{"id": 98}]',
    }
    for path, content in original_files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    calls = 0

    def submitted_then_timeout(url: str, **kwargs: object) -> requests.Response:
        """Return submitted data once and then simulate a timeout.

        Args:
            url: Requested endpoint URL.
            **kwargs: Request arguments passed by the client.

        Returns:
            The synthetic submitted response on its first invocation.

        Raises:
            requests.Timeout: Always on the second invocation.

        Example:
            ``submitted_then_timeout("https://www.muckrock.com/api_v1/foia")``.
        """
        nonlocal calls
        calls += 1
        if calls == 1:
            return make_response({"results": [request_row(1)]})
        raise requests.Timeout("network details must not reach command output")

    monkeypatch.setenv("MUCKROCK_API_TOKEN", "test-token")
    monkeypatch.setattr(client.requests, "get", submitted_then_timeout)

    result = CliRunner().invoke(
        download.cli, ["--allow-public-feed", "--data-dir", str(tmp_path)]
    )

    assert result.exit_code == 1
    assert calls == 2
    assert {path: path.read_text() for path in original_files} == original_files
    assert set(tmp_path.rglob("*.json")) == set(original_files)


def test_writing_requires_explicit_public_feed_approval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reject snapshot writes unless approval is supplied as the true flag value.

    Args:
        tmp_path: Temporary directory supplied by pytest.
        monkeypatch: Pytest helper for setting the approval environment variable.

    Returns:
        None. Assertions confirm an unapproved command performs no request or write.

    Example:
        Run with ``pytest tests/test_cli.py::test_writing_requires_explicit_public_feed_approval``.
    """
    output_dir = tmp_path / "approval-required"
    monkeypatch.setenv("MUCKROCK_PUBLIC_FEED_APPROVED", "false")

    result = CliRunner().invoke(download.cli, ["--data-dir", str(output_dir)])

    assert result.exit_code == 1
    assert "requires approval" in result.output
    assert not output_dir.exists()


@pytest.mark.parametrize("token", [None, "", " \t ", "token\nvalue"])
def test_download_requires_a_nonempty_safe_api_token(
    token: str | None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reject absent, blank, or newline-containing API tokens before any request.

    Args:
        token: Environment value to validate.
        monkeypatch: Pytest helper for replacing environment variables.

    Returns:
        None. Assertions confirm a safe credential error is displayed.

    Example:
        Run with ``pytest tests/test_cli.py::test_download_requires_a_nonempty_safe_api_token``.
    """
    if token is None:
        monkeypatch.delenv("MUCKROCK_API_TOKEN", raising=False)
    else:
        monkeypatch.setenv("MUCKROCK_API_TOKEN", token)

    result = CliRunner().invoke(download.cli, ["--check"])

    assert result.exit_code == 1
    assert "Set MUCKROCK_API_TOKEN" in result.output


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
