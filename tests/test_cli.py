import json

from click.testing import CliRunner

from muckrockbot import download, transform


class FakeRequest:
    """A request returned by the API v2 client."""

    def __init__(self, request_id, title):
        self.id = request_id
        self.title = title
        self.user = 123
        self._client = object()


class FakeResults:
    """The first page of an API v2 list response."""

    def __init__(self, results):
        self.results = results


class FakeRequestClient:
    """Record API v2 request queries and return fixture data."""

    def __init__(self):
        self.calls = []

    def list(self, **params):
        self.calls.append(params)
        return FakeResults([FakeRequest(456, "Test request")])


class FakeMuckRock:
    """An authenticated API v2 client."""

    instance = None

    def __init__(self, **credentials):
        self.credentials = credentials
        self.requests = FakeRequestClient()
        FakeMuckRock.instance = self


def test_download_cli(tmp_path, monkeypatch):
    """Test a single download run."""
    monkeypatch.setattr(download, "DATA_DIR", tmp_path)
    monkeypatch.setattr(download, "MuckRock", FakeMuckRock)
    monkeypatch.setenv("MUCKROCK_USERNAME", "test-user")
    monkeypatch.setenv("MUCKROCK_PASSWORD", "test-password")

    runner = CliRunner()
    result = runner.invoke(download.cli, [])

    assert result.exit_code == 0
    assert FakeMuckRock.instance.credentials == {
        "username": "test-user",
        "password": "test-password",
    }
    assert FakeMuckRock.instance.requests.calls == [
        {"ordering": "-datetime_submitted", "page_size": 100},
        {"ordering": "-datetime_done", "page_size": 100, "status": "done"},
    ]
    data = json.loads((tmp_path / "submitted" / "latest.json").read_text())
    assert data == [
        {
            "id": 456,
            "title": "Test request",
            "user": 123,
            "absolute_url": "https://www.muckrock.com/foi/request/456/",
        }
    ]


def test_transform_cli(tmp_path, monkeypatch):
    """Test a single transform run."""
    monkeypatch.setattr(transform, "DATA_DIR", tmp_path)
    (tmp_path / "2026-01-01 00:00:00+00:00.json").write_text(
        json.dumps([{"id": 1}])
    )
    (tmp_path / "2026-01-02 00:00:00+00:00.json").write_text(
        json.dumps([{"id": 1}, {"id": 2}])
    )

    runner = CliRunner()
    result = runner.invoke(transform.cli, [])

    assert result.exit_code == 0
    assert json.loads((tmp_path / "additions.json").read_text()) == [{"id": 2}]
